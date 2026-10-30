# Stop Camouzer host + any camouzer python feeds.
$ErrorActionPreference = "Continue"
try {
    $stop = New-Object -TypeName System.Threading.EventWaitHandle -ArgumentList @($false, 'ManualReset', 'Global\Camouzer_Shutdown')
    $stop.Set() | Out-Null
} catch {}
Start-Sleep -Milliseconds 400
Get-Process CamouzerHost -ErrorAction SilentlyContinue | Stop-Process -Force
Get-CimInstance Win32_Process -Filter "Name='python.exe' OR Name='py.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -match 'camouzer' } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
Write-Host 'Stopped Camouzer host / feeds.'
