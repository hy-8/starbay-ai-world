<#
.SYNOPSIS
Packages Starbay with the installed engine's precompiled Windows Development target.
.DESCRIPTION
Does not build C++ or edit project assets. Fails if a plugin or project change
requires compilation; inspect the saved UAT log instead of treating it as a build.
Without OutputDirectory, creates a unique timestamped directory under Builds.
#>
[CmdletBinding()]
param(
    [string]$EngineRoot = 'D:\Program Files\Epic Games\UE_5.6',
    [string]$OutputDirectory,
    [string]$CacheRoot,
    [string[]]$Maps = @('/Game/Starbay/Maps/L_Starbay')
)

$ErrorActionPreference = 'Stop'
$taskProjectRoot = Split-Path -Parent $PSScriptRoot
$taskProjectFile = Join-Path $taskProjectRoot 'StarbayUE5.uproject'
$taskProjectName = [IO.Path]::GetFileNameWithoutExtension($taskProjectFile)
$taskStamp = (Get-Date -Format 'yyyyMMdd-HHmmss-fff') + '-' + [guid]::NewGuid().ToString('N').Substring(0, 6)
$taskSaved = Join-Path $taskProjectRoot 'Saved'
New-Item -ItemType Directory -Path $taskSaved -Force | Out-Null
$taskLog = Join-Path $taskSaved "package-$taskStamp.log"
$taskReportPath = Join-Path $taskSaved "package-$taskStamp.json"
if (-not $OutputDirectory) {
    $OutputDirectory = Join-Path $taskProjectRoot "Builds\Windows-Development-$taskStamp"
}
$taskOutput = [IO.Path]::GetFullPath($OutputDirectory)
$taskReport = [ordered]@{
    status = 'preflight'
    startedAtUtc = [DateTime]::UtcNow.ToString('o')
    project = $taskProjectFile
    engineRoot = $EngineRoot
    outputDirectory = $taskOutput
    configuration = 'Development'
    usesPrecompiledTarget = $true
    runtimeGameplayTested = $false
    exitCode = $null
    executableExists = $false
    executables = @()
    log = $taskLog
}
$taskEnvironmentBefore = @{}
$taskConsoleEncodingBefore = [Console]::OutputEncoding
$taskUtf8 = New-Object System.Text.UTF8Encoding($false)
$taskLogWriter = New-Object System.IO.StreamWriter($taskLog, $false, $taskUtf8)
$taskLogWriter.AutoFlush = $true
$taskFailure = $null

try {
    $taskEngine = (Resolve-Path -LiteralPath $EngineRoot).ProviderPath
    $taskRunUat = Join-Path $taskEngine 'Engine\Build\BatchFiles\RunUAT.bat'
    $taskRequired = @(
        $taskProjectFile
        $taskRunUat
        (Join-Path $taskProjectRoot 'Content\Starbay\Maps\L_Starbay.umap')
        (Join-Path $taskProjectRoot 'Content\ThirdPerson\Blueprints\BP_ThirdPersonCharacter.uasset')
        (Join-Path $taskProjectRoot 'Content\ThirdPerson\Blueprints\BP_ThirdPersonGameMode.uasset')
        (Join-Path $taskProjectRoot 'Content\ThirdPerson\Blueprints\BP_ThirdPersonPlayerController.uasset')
        (Join-Path $taskProjectRoot 'Content\Characters\Mannequins\Meshes\SKM_Quinn_Simple.uasset')
        (Join-Path $taskProjectRoot 'Content\Characters\Mannequins\Anims\Unarmed\ABP_Unarmed.uasset')
    )
    foreach ($taskRequiredFile in $taskRequired) {
        if (-not (Test-Path -LiteralPath $taskRequiredFile -PathType Leaf)) {
            throw "打包所需文件尚不存在：$taskRequiredFile"
        }
    }
    $taskProjectVersion = (Get-Content -LiteralPath $taskProjectFile -Raw | ConvertFrom-Json).EngineAssociation
    $taskVersion = Get-Content -LiteralPath (Join-Path $taskEngine 'Engine\Build\Build.version') -Raw | ConvertFrom-Json
    if ("$($taskVersion.MajorVersion).$($taskVersion.MinorVersion)" -ne $taskProjectVersion) {
        throw "引擎版本与项目指定版本 $taskProjectVersion 不符。"
    }
    if (Test-Path -LiteralPath $taskOutput) {
        if (-not (Test-Path -LiteralPath $taskOutput -PathType Container)) {
            throw "输出路径不是文件夹：$taskOutput"
        }
        if (@(Get-ChildItem -LiteralPath $taskOutput -Force).Count -gt 0) {
            throw "输出文件夹非空，不会覆盖已有交付：$taskOutput"
        }
    }
    New-Item -ItemType Directory -Path $taskOutput -Force | Out-Null
    if (-not $CacheRoot) {
        $CacheRoot = Join-Path ([IO.Path]::GetPathRoot($taskEngine)) 'UECache'
    }
    $taskDdc = Join-Path $CacheRoot 'DDC'
    $taskZen = Join-Path $CacheRoot 'Zen'
    $taskTemp = Join-Path $CacheRoot 'Temp'
    foreach ($taskDirectory in @($taskDdc, $taskZen, $taskTemp)) {
        New-Item -ItemType Directory -Path $taskDirectory -Force | Out-Null
    }

    $taskEnvironment = @{
        'UE-LocalDataCachePath' = $taskDdc
        'UE-ZenDataPath' = $taskZen
        'TEMP' = $taskTemp
        'TMP' = $taskTemp
    }
    foreach ($taskName in @('PROCESSOR_ARCHITECTURE','OS','PROCESSOR_IDENTIFIER','PROCESSOR_LEVEL','PROCESSOR_REVISION','NUMBER_OF_PROCESSORS')) {
        $taskValue = [Environment]::GetEnvironmentVariable($taskName, 'Machine')
        if ([string]::IsNullOrWhiteSpace($taskValue)) { throw "缺少标准机器环境变量：$taskName" }
        $taskEnvironment[$taskName] = $taskValue
    }
    foreach ($taskName in $taskEnvironment.Keys) {
        $taskEnvironmentBefore[$taskName] = [Environment]::GetEnvironmentVariable($taskName, 'Process')
        [Environment]::SetEnvironmentVariable($taskName, $taskEnvironment[$taskName], 'Process')
    }
    [Console]::OutputEncoding = $taskUtf8
    $taskArguments = @(
        'BuildCookRun', "-project=$taskProjectFile", '-noP4', '-platform=Win64',
        '-clientconfig=Development', '-skipbuild', '-cook', '-stage', '-pak', '-iostore',
        '-package', '-archive', "-archivedirectory=$taskOutput",
        ('-map=' + ($Maps -join '+')), '-unattended', '-utf8output',
        '-nocompileeditor', '-nocompileuat'
    )
    $taskReport.status = 'packaging'
    $taskReport.engineVersion = "$($taskVersion.MajorVersion).$($taskVersion.MinorVersion).$($taskVersion.PatchVersion)"
    $taskReport.arguments = $taskArguments
    $taskReport.cacheRoot = $CacheRoot
    $taskLogWriter.WriteLine("Started UTC: $($taskReport.startedAtUtc)")
    $taskLogWriter.WriteLine("RunUAT: $taskRunUat")
    $taskLogWriter.WriteLine(($taskArguments -join ' '))
    # Stream output to a UTF-8 log. Error lines are retained; the native exit code
    # decides whether UAT succeeded. This launches only the requested packaging job.
    $ErrorActionPreference = 'Continue'
    & $taskRunUat @taskArguments 2>&1 | ForEach-Object {
        $taskLine = $_.ToString()
        $taskLogWriter.WriteLine($taskLine)
        Write-Output $taskLine
    }
    $taskReport.exitCode = $LASTEXITCODE
    $ErrorActionPreference = 'Stop'
    $taskExecutables = @(
        (Join-Path $taskOutput "Windows\$taskProjectName.exe")
        (Join-Path $taskOutput "$taskProjectName.exe")
    ) | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf }
    $taskReport.executables = @($taskExecutables)
    $taskReport.executableExists = @($taskExecutables).Count -gt 0
    if ($taskReport.exitCode -ne 0 -or -not $taskReport.executableExists) {
        throw "打包未成功完成（UAT退出码：$($taskReport.exitCode)，游戏exe：$($taskReport.executableExists)）。详见 $taskLog"
    }
    $taskReport.status = 'packaged_awaiting_runtime_test'
} catch {
    $taskFailure = $_
    $taskReport.status = 'failed'
    $taskReport.error = $_.Exception.Message
    $taskLogWriter.WriteLine("FAILED: $($_.Exception.Message)")
} finally {
    foreach ($taskName in $taskEnvironmentBefore.Keys) {
        [Environment]::SetEnvironmentVariable($taskName, $taskEnvironmentBefore[$taskName], 'Process')
    }
    [Console]::OutputEncoding = $taskConsoleEncodingBefore
    $taskLogWriter.Dispose()
    $taskReport.finishedAtUtc = [DateTime]::UtcNow.ToString('o')
    [IO.File]::WriteAllText($taskReportPath, ($taskReport | ConvertTo-Json -Depth 5) + [Environment]::NewLine, $taskUtf8)
}
Write-Output ([pscustomobject]@{Status=$taskReport.status; Report=$taskReportPath; Log=$taskLog; Executables=$taskReport.executables})
if ($taskFailure) { throw $taskFailure }
