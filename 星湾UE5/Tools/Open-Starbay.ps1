param([string]$EngineRoot, [switch]$ImportScene, [string]$CacheRoot, [string]$ExecuteScript)
$ErrorActionPreference = 'Stop'
$taskProjectRoot = Split-Path -Parent $PSScriptRoot
$taskProjectFile = Join-Path $taskProjectRoot 'StarbayUE5.uproject'
$taskProjectVersion = (Get-Content -LiteralPath $taskProjectFile -Raw | ConvertFrom-Json).EngineAssociation
function Find-StarbayInstalledEngine {
    param([string]$Version, [string]$ProgramDataRoot)
    if (-not $ProgramDataRoot) {
        $ProgramDataRoot = [Environment]::GetFolderPath('CommonApplicationData')
    }
    $taskManifest = Join-Path $ProgramDataRoot 'Epic\UnrealEngineLauncher\LauncherInstalled.dat'
    if (Test-Path -LiteralPath $taskManifest) {
        try {
            $taskInstalled = (Get-Content -LiteralPath $taskManifest -Raw | ConvertFrom-Json).InstallationList
            $taskMatch = $taskInstalled | Where-Object {
                $_.AppName -eq "UE_$Version" -and
                $_.InstallLocation -is [string] -and
                -not [string]::IsNullOrWhiteSpace($_.InstallLocation)
            } | Select-Object -First 1
            if ($taskMatch) { return $taskMatch.InstallLocation }
        } catch {
            Write-Verbose 'Epic legacy registration is not readable; checking completed item manifests.'
        }
    }
    $taskItemDirectory = Join-Path $ProgramDataRoot 'Epic\EpicGamesLauncher\Data\Manifests'
    if (Test-Path -LiteralPath $taskItemDirectory -PathType Container) {
        foreach ($taskItem in (Get-ChildItem -LiteralPath $taskItemDirectory -Filter '*.item' -File | Sort-Object Name)) {
            try { $taskEntry = Get-Content -LiteralPath $taskItem.FullName -Raw | ConvertFrom-Json }
            catch { continue } # Epic may be replacing a manifest while this script reads it.
            if ($taskEntry.AppName -eq "UE_$Version" -and
                $taskEntry.bIsIncompleteInstall -is [bool] -and
                $taskEntry.bIsIncompleteInstall -eq $false -and
                $taskEntry.InstallLocation -is [string] -and
                -not [string]::IsNullOrWhiteSpace($taskEntry.InstallLocation)) {
                return $taskEntry.InstallLocation
            }
        }
    }
    return $null
}
if (-not $EngineRoot) {
    $EngineRoot = Find-StarbayInstalledEngine -Version $taskProjectVersion
}
if (-not $EngineRoot) { throw "尚未发现项目指定的 UE $taskProjectVersion。请等待 Epic 完成安装，再运行此脚本；其他引擎版本需显式传入 -EngineRoot。" }
$taskEditor = Join-Path $EngineRoot 'Engine\Binaries\Win64\UnrealEditor.exe'
if (-not (Test-Path -LiteralPath $taskEditor)) { throw "未找到 UnrealEditor.exe：$taskEditor" }
if (-not $CacheRoot) {
    $CacheRoot = Join-Path ([System.IO.Path]::GetPathRoot((Resolve-Path -LiteralPath $EngineRoot).ProviderPath)) 'UECache'
}
$taskDdc = Join-Path $CacheRoot 'DDC'
$taskZen = Join-Path $CacheRoot 'Zen'
$taskTemp = Join-Path $CacheRoot 'Temp'
foreach ($taskCacheDirectory in @($taskDdc,$taskZen,$taskTemp)) {
    New-Item -ItemType Directory -Path $taskCacheDirectory -Force | Out-Null
}
$taskArgs = @("`"$taskProjectFile`"")
$taskArgs += "-ZenDataPath=`"$taskZen`""
if ($ImportScene) {
    if ($ExecuteScript) { throw 'ImportScene 与 ExecuteScript 不能同时使用。' }
    $taskMap = Join-Path $taskProjectRoot 'Content\Starbay\Maps\L_Starbay.umap'
    if (Test-Path -LiteralPath $taskMap) { throw '场景已经存在，不会覆盖手工编辑。请正常打开工程。' }
    if (-not (Test-Path -LiteralPath (Join-Path $taskProjectRoot 'SourceAssets\asset_manifest.json'))) { throw '缺少资产，请先运行 Blender 导出脚本。' }
    $taskImportScript = Join-Path $PSScriptRoot 'bootstrap_scene.py'
    $taskArgs += "-ExecutePythonScript=`"$taskImportScript`""
}
if ($ExecuteScript) {
    $taskRunScript = (Resolve-Path -LiteralPath $ExecuteScript).ProviderPath
    $taskArgs += "-ExecutePythonScript=`"$taskRunScript`""
}
# Automation hosts can omit standard Windows CPU variables. Restore only this
# child process environment; never write persistent user or machine settings.
$taskStartInfo = New-Object System.Diagnostics.ProcessStartInfo
$taskStartInfo.FileName = $taskEditor
$taskStartInfo.Arguments = $taskArgs -join ' '
$taskStartInfo.WorkingDirectory = $taskProjectRoot
$taskStartInfo.UseShellExecute = $false
$taskStartInfo.EnvironmentVariables['UE-LocalDataCachePath'] = $taskDdc
$taskStartInfo.EnvironmentVariables['UE-ZenDataPath'] = $taskZen
$taskStartInfo.EnvironmentVariables['TEMP'] = $taskTemp
$taskStartInfo.EnvironmentVariables['TMP'] = $taskTemp
foreach ($taskName in @('PROCESSOR_ARCHITECTURE','OS','PROCESSOR_IDENTIFIER','PROCESSOR_LEVEL','PROCESSOR_REVISION','NUMBER_OF_PROCESSORS')) {
    $taskValue = [Environment]::GetEnvironmentVariable($taskName, 'Machine')
    if (-not [string]::IsNullOrWhiteSpace($taskValue)) { $taskStartInfo.EnvironmentVariables[$taskName] = $taskValue }
}
# The user requested an interactive editor, so its visible window is intentional.
$taskEditorProcess = [System.Diagnostics.Process]::Start($taskStartInfo)
Write-Output ([pscustomobject]@{ProcessId=$taskEditorProcess.Id; EngineRoot=$EngineRoot; Project=$taskProjectFile})
$taskEditorProcess.Dispose()
