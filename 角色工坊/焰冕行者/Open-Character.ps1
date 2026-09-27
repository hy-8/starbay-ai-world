$ErrorActionPreference = 'Stop'
$taskBlender = 'D:\tools\Blender\blender-4.5.9-windows-x64\blender.exe'
$taskModel = Join-Path $PSScriptRoot 'Exports\motion05\Ember_Animated.blend'
if (-not (Test-Path -LiteralPath $taskBlender)) { throw 'Blender executable not found; update the local path.' }
if (-not (Test-Path -LiteralPath $taskModel)) { throw 'Download the dynamic character Release and restore Exports/motion05 first.' }
Start-Process -FilePath $taskBlender -ArgumentList @('"' + $taskModel + '"') -WindowStyle Normal
