$ErrorActionPreference = 'Stop'
$taskPython = (Get-Command python -ErrorAction Stop).Source
$taskOllama = Get-Command ollama -ErrorAction SilentlyContinue
if ($taskOllama) {
    try { $null = Invoke-RestMethod 'http://127.0.0.1:11434/api/tags' -TimeoutSec 2 }
    catch { Start-Process -FilePath $taskOllama.Source -ArgumentList 'serve' -WindowStyle Hidden }
}
Start-Process -FilePath $taskPython -ArgumentList @("`"$PSScriptRoot\server.py`"") -WorkingDirectory $PSScriptRoot -WindowStyle Hidden
