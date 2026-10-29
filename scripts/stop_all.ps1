# Stop RednessCam host + any rednesscam python feeds.
$ErrorActionPreference = "Continue"
try {
    $stop = New-Object -TypeName System.Threading.EventWaitHandle -ArgumentList @($false, 'ManualReset', 'Global\RednessCam_Shutdown')
    $stop.Set() | Out-Null
} catch {}
Start-Sleep -Milliseconds 400
Get-Process RednessCamHost -ErrorAction SilentlyContinue | Stop-Process -Force
Get-CimInstance Win32_Process -Filter "Name='python.exe' OR Name='py.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -match 'rednesscam' } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
Write-Host 'Stopped RednessCam host / feeds.'
