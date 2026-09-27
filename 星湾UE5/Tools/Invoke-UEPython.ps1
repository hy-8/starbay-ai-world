param([Parameter(Mandatory=$true)][string]$Script, [string]$LogName='character-tool', [string]$ProjectFile)
$ErrorActionPreference='Stop'
$taskRoot=Split-Path -Parent $PSScriptRoot
$taskEditor='D:\Program Files\Epic Games\UE_5.6\Engine\Binaries\Win64\UnrealEditor-Cmd.exe'
$taskProject=Join-Path $taskRoot 'StarbayUE5.uproject'
if($ProjectFile){$taskProject=(Resolve-Path -LiteralPath $ProjectFile).ProviderPath;$taskRoot=Split-Path -Parent $taskProject}
$taskScript=(Resolve-Path -LiteralPath $Script).ProviderPath
$taskLog=Join-Path $taskRoot ('Saved\'+$LogName+'.log')
$taskStart=[Diagnostics.ProcessStartInfo]::new()
$taskStart.FileName=$taskEditor
$taskStart.Arguments='"'+$taskProject+'" -run=pythonscript -script="'+$taskScript+'" -unattended -AllowCommandletRendering -NoSplash -abslog="'+$taskLog+'"'
$taskStart.WorkingDirectory=$taskRoot
$taskStart.UseShellExecute=$false
$taskStart.CreateNoWindow=$true
$taskStart.EnvironmentVariables['UE-LocalDataCachePath']='D:\UECache\DDC'
$taskStart.EnvironmentVariables['UE-ZenDataPath']='D:\UECache\Zen'
$taskStart.EnvironmentVariables['TEMP']='D:\UECache\Temp'
$taskStart.EnvironmentVariables['TMP']='D:\UECache\Temp'
foreach($taskName in @('PROCESSOR_ARCHITECTURE','OS','PROCESSOR_IDENTIFIER','PROCESSOR_LEVEL','PROCESSOR_REVISION','NUMBER_OF_PROCESSORS')) {
    $taskValue=[Environment]::GetEnvironmentVariable($taskName,'Machine')
    if($taskValue){$taskStart.EnvironmentVariables[$taskName]=$taskValue}
}
$taskProcess=[Diagnostics.Process]::Start($taskStart)
$taskProcess.WaitForExit()
Write-Output ('UE_EXIT='+$taskProcess.ExitCode+' LOG='+$taskLog)
if($taskProcess.ExitCode -ne 0){throw 'UE Python commandlet failed; inspect log'}
