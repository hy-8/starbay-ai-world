param([string]$EngineRoot, [switch]$ImportScene)
$ErrorActionPreference = 'Stop'
$taskProjectRoot = Split-Path -Parent $PSScriptRoot
$taskProjectFile = Join-Path $taskProjectRoot 'StarbayUE5.uproject'
$taskProjectVersion = (Get-Content -LiteralPath $taskProjectFile -Raw | ConvertFrom-Json).EngineAssociation
if (-not $EngineRoot) {
    $taskManifest = 'C:\ProgramData\Epic\UnrealEngineLauncher\LauncherInstalled.dat'
    if (Test-Path -LiteralPath $taskManifest) {
        $taskInstalled = (Get-Content -LiteralPath $taskManifest -Raw | ConvertFrom-Json).InstallationList
        $EngineRoot = ($taskInstalled | Where-Object { $_.AppName -eq "UE_$taskProjectVersion" } | Select-Object -First 1).InstallLocation
    }
}
if (-not $EngineRoot) { throw "尚未发现项目指定的 UE $taskProjectVersion。请等待 Epic 完成安装，再运行此脚本；其他引擎版本需显式传入 -EngineRoot。" }
$taskEditor = Join-Path $EngineRoot 'Engine\Binaries\Win64\UnrealEditor.exe'
if (-not (Test-Path -LiteralPath $taskEditor)) { throw "未找到 UnrealEditor.exe：$taskEditor" }
$taskArgs = @("`"$taskProjectFile`"")
if ($ImportScene) {
    $taskMap = Join-Path $taskProjectRoot 'Content\Starbay\Maps\L_Starbay.umap'
    if (Test-Path -LiteralPath $taskMap) { throw '场景已经存在，不会覆盖手工编辑。请正常打开工程。' }
    if (-not (Test-Path -LiteralPath (Join-Path $taskProjectRoot 'SourceAssets\asset_manifest.json'))) { throw '缺少资产，请先运行 Blender 导出脚本。' }
    $taskImportScript = Join-Path $PSScriptRoot 'bootstrap_scene.py'
    $taskArgs += "-ExecutePythonScript=`"$taskImportScript`""
}
# Automation hosts can omit standard Windows CPU variables. Restore only this
# child process environment; never write persistent user or machine settings.
$taskStartInfo = New-Object System.Diagnostics.ProcessStartInfo
$taskStartInfo.FileName = $taskEditor
$taskStartInfo.Arguments = $taskArgs -join ' '
$taskStartInfo.WorkingDirectory = $taskProjectRoot
$taskStartInfo.UseShellExecute = $false
foreach ($taskName in @('PROCESSOR_ARCHITECTURE','OS','PROCESSOR_IDENTIFIER','PROCESSOR_LEVEL','PROCESSOR_REVISION','NUMBER_OF_PROCESSORS')) {
    $taskValue = [Environment]::GetEnvironmentVariable($taskName, 'Machine')
    if (-not [string]::IsNullOrWhiteSpace($taskValue)) { $taskStartInfo.EnvironmentVariables[$taskName] = $taskValue }
}
# The user requested an interactive editor, so its visible window is intentional.
$taskEditorProcess = [System.Diagnostics.Process]::Start($taskStartInfo)
Write-Output ([pscustomobject]@{ProcessId=$taskEditorProcess.Id; EngineRoot=$EngineRoot; Project=$taskProjectFile})
$taskEditorProcess.Dispose()
