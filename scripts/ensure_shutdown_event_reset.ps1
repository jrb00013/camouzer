# Reset Global\RednessCam_Shutdown so the host does not exit immediately.
$ErrorActionPreference = "Stop"
Add-Type @"
using System;
using System.Runtime.InteropServices;
public static class NativeEvt {
  [DllImport("kernel32.dll", SetLastError=true, CharSet=CharSet.Unicode)]
  public static extern IntPtr CreateEvent(IntPtr lpEventAttributes, bool bManualReset, bool bInitialState, string lpName);
  [DllImport("kernel32.dll", SetLastError=true)]
  public static extern bool ResetEvent(IntPtr hEvent);
  [DllImport("kernel32.dll", SetLastError=true)]
  public static extern bool CloseHandle(IntPtr hObject);
}
"@
$h = [NativeEvt]::CreateEvent([IntPtr]::Zero, $true, $false, "Global\RednessCam_Shutdown")
if ($h -eq [IntPtr]::Zero) { throw "CreateEvent failed" }
[void][NativeEvt]::ResetEvent($h)
[void][NativeEvt]::CloseHandle($h)
Write-Host 'Global\RednessCam_Shutdown reset'
