$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
    throw 'Bitte zuerst setup.ps1 ausführen.'
}
& '.\.venv\Scripts\python.exe' -m faceveil
exit $LASTEXITCODE
