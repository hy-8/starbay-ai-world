<#
.SYNOPSIS
Starts Epic through its official EOS bootstrapper with standard Windows CPU environment values.
.DESCRIPTION
Some automation hosts omit standard Windows environment variables. EOS may then
fail with "Unsupported architecture: unknown" and exit code 71. This script
restores six machine values in the new child process only. It never stops an
existing launcher, changes persistent environment settings, or edits EOS files.
.PARAMETER LauncherRoot
The installed Epic Games Launcher directory, for example:
C:\Program Files\Epic Games\Launcher
#>
[CmdletBinding()]
param([string]$LauncherRoot)

$ErrorActionPreference = 'Stop'

$taskRunning = @(Get-Process -Name 'EpicGamesLauncher' -ErrorAction SilentlyContinue)
if ($taskRunning.Count -gt 0) {
    Write-Host 'Epic Games Launcher 已在运行；不会重启或中断当前下载。'
    [pscustomobject]@{
        Status = 'AlreadyRunning'
        ProcessIds = @($taskRunning.Id)
    }
    return
}

if ([string]::IsNullOrWhiteSpace($LauncherRoot)) {
    $taskProgramDirs = @(
        [Environment]::GetEnvironmentVariable('ProgramW6432', 'Process')
        [Environment]::GetFolderPath('ProgramFiles')
        [Environment]::GetFolderPath('ProgramFilesX86')
    ) | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -Unique

    foreach ($taskProgramDir in $taskProgramDirs) {
        $taskCandidate = Join-Path $taskProgramDir 'Epic Games\Launcher'
        $taskCandidateBootstrapper = Join-Path $taskCandidate 'Portal\Extras\EOSBootStrapper\EOSBootStrapper.exe'
        if (Test-Path -LiteralPath $taskCandidateBootstrapper -PathType Leaf) {
            $LauncherRoot = $taskCandidate
            break
        }
    }
}

if ([string]::IsNullOrWhiteSpace($LauncherRoot)) {
    throw '未找到 Epic 的官方 EOS 启动入口。请安装 Epic Games Launcher，或使用 -LauncherRoot 指定其安装目录。'
}

$taskLauncherRoot = (Resolve-Path -LiteralPath $LauncherRoot).ProviderPath
$taskBootstrapper = Join-Path $taskLauncherRoot 'Portal\Extras\EOSBootStrapper\EOSBootStrapper.exe'
$taskBootstrapConfig = Join-Path $taskLauncherRoot 'Portal\Extras\EOSBootStrapper\EOSBootStrapper.ini'
$taskLauncherExe = Join-Path $taskLauncherRoot 'Portal\Binaries\Win64\EpicGamesLauncher.exe'
foreach ($taskRequiredFile in @($taskBootstrapper, $taskBootstrapConfig, $taskLauncherExe)) {
    if (-not (Test-Path -LiteralPath $taskRequiredFile -PathType Leaf)) {
        throw "Epic 安装缺少文件，请通过官方安装程序修复：$taskRequiredFile"
    }
}

$taskStartInfo = New-Object System.Diagnostics.ProcessStartInfo
$taskStartInfo.FileName = $taskBootstrapper
$taskStartInfo.WorkingDirectory = Split-Path -Parent $taskBootstrapper
$taskStartInfo.UseShellExecute = $false
# Hide the background bootstrap helper; the launcher manages its own interactive UI.
$taskStartInfo.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Hidden
$taskStartInfo.CreateNoWindow = $true

$taskRestoreNames = @(
    'PROCESSOR_ARCHITECTURE'
    'OS'
    'PROCESSOR_IDENTIFIER'
    'PROCESSOR_LEVEL'
    'PROCESSOR_REVISION'
    'NUMBER_OF_PROCESSORS'
)
foreach ($taskRestoreName in $taskRestoreNames) {
    $taskMachineValue = [Environment]::GetEnvironmentVariable($taskRestoreName, 'Machine')
    if ([string]::IsNullOrWhiteSpace($taskMachineValue)) {
        throw "机器环境中缺少标准变量 $taskRestoreName；未启动 Epic，也未修改环境设置。"
    }
    # EnvironmentVariables belongs to this child process; there is no persistent write.
    $taskStartInfo.EnvironmentVariables[$taskRestoreName] = $taskMachineValue
}

# Check again after discovery so another already-started launcher is left alone.
$taskRunning = @(Get-Process -Name 'EpicGamesLauncher' -ErrorAction SilentlyContinue)
if ($taskRunning.Count -gt 0) {
    Write-Host 'Epic Games Launcher 已启动；保留当前进程。'
    [pscustomobject]@{
        Status = 'AlreadyRunning'
        ProcessIds = @($taskRunning.Id)
    }
    return
}

$taskBootstrapProcess = [System.Diagnostics.Process]::Start($taskStartInfo)
if ($null -eq $taskBootstrapProcess) {
    throw '官方 EOS 启动入口未返回进程；请查看 Epic 的启动日志。'
}
$taskBootstrapId = $taskBootstrapProcess.Id
$taskBootstrapProcess.Dispose()
Write-Host '已通过官方 EOS 入口启动 Epic；仅为本次子进程恢复 Windows 标准环境。'
[pscustomobject]@{
    Status = 'Started'
    BootstrapperProcessId = $taskBootstrapId
    LauncherRoot = $taskLauncherRoot
}
