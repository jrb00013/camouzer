# Build RednessCamSource.dll + RednessCamHost.exe (x64 Release)
$ErrorActionPreference = "Stop"

# Always build from the Windows working copy (MSVC cannot use WSL UNC cwd).
$Root = 'C:\Users\josep\rednesscam'
$Native = Join-Path $Root 'native'
$Build = Join-Path $Native 'build'

$Vcvars = 'C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat'
if (-not (Test-Path $Vcvars)) {
    throw 'vcvars64.bat not found. Install VS 2022 Build Tools with C++ workload.'
}
if (-not (Test-Path $Native)) {
    throw "Native sources missing at $Native. Sync the repo to C:\Users\josep\rednesscam first."
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
$Tmp = Join-Path $env:TEMP 'rednesscam_build.bat'
Set-Content -Path $Tmp -Value $batLines -Encoding ASCII
cmd.exe /c $Tmp
if ($LASTEXITCODE -ne 0) { throw "Native build failed with exit $LASTEXITCODE" }

Write-Host 'Built artifacts:'
Get-ChildItem -Recurse $Build -Include RednessCamSource.dll,RednessCamHost.exe |
    ForEach-Object { Write-Host $_.FullName }
