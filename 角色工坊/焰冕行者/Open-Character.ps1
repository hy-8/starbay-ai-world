$ErrorActionPreference = 'Stop'
$taskBlender = 'D:\tools\Blender\blender-4.5.9-windows-x64\blender.exe'
$taskModel = Join-Path $PSScriptRoot 'Exports\v14\Ember_Regent.blend'
if (-not (Test-Path -LiteralPath $taskBlender)) { throw 'Blender executable not found; update the local path.' }
if (-not (Test-Path -LiteralPath $taskModel)) { throw 'Download the couture character Release and restore Exports/v14 first.' }
Start-Process -FilePath $taskBlender -ArgumentList @('"' + $taskModel + '"') -WindowStyle Normal
