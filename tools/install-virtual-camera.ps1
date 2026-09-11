# Run from a 64-bit elevated PowerShell. Downloads pinned MIT-licensed Unity Capture filters.
# Never registers, unregisters, or edits an OBS device.
#Requires -RunAsAdministrator
$ErrorActionPreference = 'Stop'
if (-not [Environment]::Is64BitProcess) { throw 'Use 64-bit PowerShell.' }
$revision = '3ed54c325e0ad71afcf4f246c07e5e17b3d7f2d2'
$target = Join-Path $env:ProgramFiles 'FaceVeil\VirtualCamera'
$hashes = @{
    '32' = 'aa3ebdf03dea7f3aab3dd7b724751f49ed71672256b57c6a19aa6809cabf30ba'
    '64' = '72812f5363d8ecb45632253f8c8c888844b1b62e27616f3c8cc21064ccde25e5'
}
# Unity Capture shares fixed class IDs. Refuse to replace an existing installation.
foreach ($hive in @([Microsoft.Win32.RegistryHive]::LocalMachine, [Microsoft.Win32.RegistryHive]::CurrentUser)) {
foreach ($view in @([Microsoft.Win32.RegistryView]::Registry64, [Microsoft.Win32.RegistryView]::Registry32)) {
    $root = [Microsoft.Win32.RegistryKey]::OpenBaseKey($hive, $view)
    try {
        $classes = $root.OpenSubKey('SOFTWARE\Classes\CLSID')
        if ($null -eq $classes) { continue }
        try {
            foreach ($name in $classes.GetSubKeyNames()) {
                if ($name -like '{5c2cd55c-92ad-4999-8666-912bd3e700*}') {
                    throw 'Unity Capture is already registered. Setup stopped to protect that installation. See docs/virtual-camera.md.'
                }
            }
        } finally { $classes.Dispose() }
    } finally { $root.Dispose() }
}
}
New-Item -ItemType Directory -Path $target -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $PSScriptRoot '..\docs\UnityCapture-LICENSE.txt') -Destination (Join-Path $target 'UnityCapture-LICENSE.txt')
foreach ($bits in @('32', '64')) {
    $file = Join-Path $target "UnityCaptureFilter$bits.dll"
    Invoke-WebRequest -Uri "https://raw.githubusercontent.com/schellingb/UnityCapture/$revision/Install/UnityCaptureFilter$bits.dll" -OutFile $file
    if ((Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash -ne $hashes[$bits]) {
        throw "SHA-256 verification failed for $file. No filters registered."
    }
}
# Verify both downloads before changing the device registry.
foreach ($bits in @('64', '32')) {
    $systemFolder = if ($bits -eq '64') { 'System32' } else { 'SysWOW64' }
    $registrar = Join-Path $env:windir "$systemFolder\regsvr32.exe"
    $file = Join-Path $target "UnityCaptureFilter$bits.dll"
    $process = Start-Process -FilePath $registrar -ArgumentList @('/s', '"/i:UnityCaptureName=FaceVeil Virtual Camera"', "`"$file`"") -Wait -PassThru -WindowStyle Hidden
    if ($process.ExitCode -ne 0) { throw "Registration failed ($bits-bit). Exit: $($process.ExitCode). Keep installed files and inspect before retrying." }
}
Write-Host 'FaceVeil Virtual Camera installed. Restart camera-consuming applications.'
