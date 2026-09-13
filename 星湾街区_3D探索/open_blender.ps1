$taskBlender = 'D:\tools\Blender\blender-4.5.9-windows-x64\blender.exe'
$taskProject = Get-ChildItem -LiteralPath $PSScriptRoot -Filter '*.blend' | Select-Object -First 1
Start-Process -FilePath $taskBlender -ArgumentList @("`"$($taskProject.FullName)`"")
