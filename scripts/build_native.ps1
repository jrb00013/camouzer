# Build CamouzerSource.dll + CamouzerHost.exe (x64 Release)
$ErrorActionPreference = "Stop"

# Repo root = parent of scripts/ (never hardcode a username path)
$Root = Split-Path -Parent $PSScriptRoot
if ($Root -like '\\wsl*\*' -or $Root -like '\\wsl.localhost\*') {
    throw "Run this script from a Windows checkout (not a WSL UNC path). Clone/copy the repo under %USERPROFILE% or another NTFS path, then re-run."
}
$Native = Join-Path $Root 'native'
$Build = Join-Path $Native 'build'

$Vcvars = 'C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat'
if (-not (Test-Path $Vcvars)) {
    $Vcvars = 'C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat'
}
if (-not (Test-Path $Vcvars)) {
    throw 'vcvars64.bat not found. Install VS 2022 Build Tools with C++ workload.'
}
if (-not (Test-Path $Native)) {
    throw "Native sources missing at $Native."
}

New-Item -ItemType Directory -Force -Path $Build | Out-Null

$batLines = @(
    '@echo off'
    "call `"$Vcvars`""
    'if errorlevel 1 exit /b 1'
    "cd /d `"$Native`""
    'cmake -S . -B build -G "Visual Studio 17 2022" -A x64'
    'if errorlevel 1 exit /b 1'
    'cmake --build build --config Release'
    'exit /b %ERRORLEVEL%'
)
$Tmp = Join-Path $env:TEMP 'camouzer_build.bat'
Set-Content -Path $Tmp -Value $batLines -Encoding ASCII
cmd.exe /c $Tmp
if ($LASTEXITCODE -ne 0) { throw "Native build failed with exit $LASTEXITCODE" }

Write-Host 'Built artifacts:'
Get-ChildItem -Recurse $Build -Include CamouzerSource.dll,CamouzerHost.exe |
    ForEach-Object { Write-Host $_.FullName }
