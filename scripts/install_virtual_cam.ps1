# Install RednessCam to ProgramData, register COM, start host.
$ErrorActionPreference = "Stop"
$Root = 'C:\Users\josep\rednesscam'

$BuiltDll = Get-ChildItem -Recurse (Join-Path $Root 'native\build') -Filter RednessCamSource.dll |
    Select-Object -First 1
$BuiltHost = Get-ChildItem -Recurse (Join-Path $Root 'native\build') -Filter RednessCamHost.exe |
    Select-Object -First 1
if (-not $BuiltDll -or -not $BuiltHost) {
    throw 'Build artifacts missing - run scripts/build_native.ps1 first'
}

$Dest = 'C:\ProgramData\RednessCam'
New-Item -ItemType Directory -Force -Path $Dest | Out-Null
$Dll = Join-Path $Dest 'RednessCamSource.dll'
$HostExe = Join-Path $Dest 'RednessCamHost.exe'

# Signal + kill host so we can replace binaries.
try {
    $stop = New-Object -TypeName System.Threading.EventWaitHandle -ArgumentList @($false, 'ManualReset', 'Global\RednessCam_Shutdown')
    [void]$stop.Set()
} catch {}
Start-Sleep -Milliseconds 400
Get-Process RednessCamHost -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Milliseconds 600

if (Test-Path $Dll) {
    & regsvr32.exe /s /u $Dll 2>$null
    Start-Sleep -Milliseconds 300
    $bak = Join-Path $Dest ("RednessCamSource.dll.bak." + [DateTime]::UtcNow.ToString('yyyyMMddHHmmss'))
    try {
        Rename-Item $Dll $bak -Force
    } catch {
        Write-Host 'Could not rename old DLL (Frame Server may hold it). Restarting FrameServer...'
        Restart-Service FrameServer -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
        Rename-Item $Dll $bak -Force
    }
}

Copy-Item $BuiltDll.FullName $Dll -Force
Copy-Item $BuiltHost.FullName $HostExe -Force
icacls $Dest /grant '*S-1-1-0:(OI)(CI)(RX)' /T | Out-Null

# Prune old backups (keep 3)
Get-ChildItem $Dest -Filter 'RednessCamSource.dll.bak.*' |
    Sort-Object LastWriteTime -Descending |
    Select-Object -Skip 3 |
    Remove-Item -Force -ErrorAction SilentlyContinue

Write-Host "Registering $Dll"
& regsvr32.exe /s $Dll
if ($LASTEXITCODE -ne 0) {
    Write-Host 'regsvr32 needs elevation; trying sudo...'
    & sudo.exe regsvr32.exe /s $Dll
}

powershell -ExecutionPolicy Bypass -File (Join-Path $Root 'scripts\ensure_shutdown_event_reset.ps1')

Remove-Item (Join-Path $Dest 'host.log') -ErrorAction SilentlyContinue
Start-Process -FilePath $HostExe -WorkingDirectory $Dest
Start-Sleep -Seconds 2
if (-not (Get-Process RednessCamHost -ErrorAction SilentlyContinue)) {
    Get-Content (Join-Path $Dest 'host.log') -ErrorAction SilentlyContinue
    throw 'RednessCamHost failed to stay running - see C:\ProgramData\RednessCam\host.log'
}
Write-Host 'RednessCamHost is running.'
Get-Content (Join-Path $Dest 'host.log') -Tail 20 -ErrorAction SilentlyContinue
