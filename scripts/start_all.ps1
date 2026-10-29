# Full bring-up: rebuild (optional) -> install host -> run Python feed.
param(
    [switch]$SkipBuild,
    [double]$Strength = 0.45,
    [switch]$TestPattern,
    [switch]$Preview
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
if ($Root -like '\\wsl*\*' -or $Root -like '\\wsl.localhost\*') {
    throw "Run from a Windows checkout, not a WSL UNC path."
}
Set-Location $Root

if (-not $SkipBuild) {
    Write-Host '=== build native ==='
    powershell -ExecutionPolicy Bypass -File (Join-Path $Root 'scripts\build_native.ps1')
}

Write-Host '=== install + start host ==='
powershell -ExecutionPolicy Bypass -File (Join-Path $Root 'scripts\install_virtual_cam.ps1')

Write-Host '=== install python package ==='
py -3 -m pip install -e $Root -q

$args = @('-3', '-m', 'rednesscam', 'run', '--strength', "$Strength")
if ($TestPattern) { $args += '--test-pattern' }
if ($Preview) { $args += '--preview' }

Write-Host '=== starting rednesscam feed ==='
Write-Host 'Teams: Devices -> Camera -> RednessCam (Windows Virtual Camera)'
Write-Host ("Command: py " + ($args -join ' '))
& py @args
