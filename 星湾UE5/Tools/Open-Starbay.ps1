param([string]$EngineRoot, [switch]$ImportScene)
$ErrorActionPreference = 'Stop'
$taskProjectRoot = Split-Path -Parent $PSScriptRoot
$taskProjectFile = Join-Path $taskProjectRoot 'StarbayUE5.uproject'
if (-not $EngineRoot) {
    $taskManifest = 'C:\ProgramData\Epic\UnrealEngineLauncher\LauncherInstalled.dat'
    if (Test-Path -LiteralPath $taskManifest) {
        $taskInstalled = (Get-Content -LiteralPath $taskManifest -Raw | ConvertFrom-Json).InstallationList
        $EngineRoot = ($taskInstalled | Where-Object { $_.AppName -like 'UE_5*' } | Sort-Object AppName -Descending | Select-Object -First 1).InstallLocation
    }
}
if (-not $EngineRoot) { throw '尚未发现 UE5。请先在 Epic 安装 Unreal Engine，再运行此脚本；也可传入 -EngineRoot。' }
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
# The user explicitly requested an interactive engine editor, so a visible window is intentional.
Start-Process -FilePath $taskEditor -ArgumentList $taskArgs -WorkingDirectory $taskProjectRoot
