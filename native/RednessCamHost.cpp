// ============================================================================
// RednessCamHost.exe — registers RednessCam via MFCreateVirtualCamera.
// Stays alive until ENTER (console) or Global\RednessCam_Shutdown is signaled.
// ============================================================================
#include <windows.h>
#include <mfvirtualcamera.h>
#include <mfapi.h>
#include <mfidl.h>
#include <wrl/client.h>
#include <stdio.h>

#pragma comment(lib, "mf.lib")
#pragma comment(lib, "mfplat.lib")
#pragma comment(lib, "mfuuid.lib")
#pragma comment(lib, "mfsensorgroup.lib")
#pragma comment(lib, "ole32.lib")

using Microsoft::WRL::ComPtr;

static const WCHAR* SOURCE_CLSID = L"{A7C4E291-8F12-4B6D-9E3A-1D5C8F0B4A27}";
static const WCHAR* SHUTDOWN_EVENT = L"Global\\RednessCam_Shutdown";

static void HostLog(const char* msg)
{
    FILE* f = nullptr;
    if (fopen_s(&f, "C:\\ProgramData\\RednessCam\\host.log", "a") == 0 && f) {
        fprintf(f, "%s\n", msg);
        fflush(f);
        fclose(f);
    }
    OutputDebugStringA(msg);
    OutputDebugStringA("\n");
    puts(msg);
    fflush(stdout);
}

static void HostLogHr(const char* msg, HRESULT hr)
{
    char buf[256];
    sprintf_s(buf, "%s 0x%08X", msg, (unsigned)hr);
    HostLog(buf);
}

static void WaitUntilStop()
{
    SECURITY_DESCRIPTOR sd;
    InitializeSecurityDescriptor(&sd, SECURITY_DESCRIPTOR_REVISION);
    SetSecurityDescriptorDacl(&sd, TRUE, nullptr, FALSE);
    SECURITY_ATTRIBUTES sa{ sizeof(sa), &sd, FALSE };

    HANDLE stopEvent = CreateEventW(&sa, TRUE, FALSE, SHUTDOWN_EVENT);
    // Install scripts may leave this event signaled — clear it so we actually stay alive.
    if (stopEvent) {
        ResetEvent(stopEvent);
    }

    // Also wake if stdin has a line (interactive console).
    HANDLE stdinHandle = GetStdHandle(STD_INPUT_HANDLE);
    DWORD stdinType = GetFileType(stdinHandle);
    bool consoleIn = (stdinHandle && stdinHandle != INVALID_HANDLE_VALUE &&
                      stdinType == FILE_TYPE_CHAR);
    if (consoleIn) {
        HostLog("  Press ENTER to stop (or signal Global\\RednessCam_Shutdown).");
    } else {
        HostLog("  Running headless; signal Global\\RednessCam_Shutdown to stop.");
    }

    if (consoleIn) {
        // Pump: wait 200ms slices; check for ENTER.
        for (;;) {
            if (stopEvent) {
                DWORD w = WaitForSingleObject(stopEvent, 200);
                if (w == WAIT_OBJECT_0) break;
            } else {
                Sleep(200);
            }
            INPUT_RECORD rec{};
            DWORD read = 0;
            while (PeekConsoleInputW(stdinHandle, &rec, 1, &read) && read == 1) {
                ReadConsoleInputW(stdinHandle, &rec, 1, &read);
                if (rec.EventType == KEY_EVENT && rec.Event.KeyEvent.bKeyDown &&
                    (rec.Event.KeyEvent.wVirtualKeyCode == VK_RETURN)) {
                    return;
                }
            }
            if (!stopEvent) {
                // no event and somehow no console loop exit — keep sleeping
            }
        }
        return;
    }

    if (stopEvent) {
        WaitForSingleObject(stopEvent, INFINITE);
        return;
    }
    // Last resort
    Sleep(INFINITE);
}

int main()
{
    CreateDirectoryW(L"C:\\ProgramData\\RednessCam", nullptr);
    HostLog("[RednessCam] host starting");

    HRESULT hr = CoInitializeEx(nullptr, COINIT_MULTITHREADED);
    if (FAILED(hr)) {
        HostLogHr("[ERROR] CoInitialize failed", hr);
        return 1;
    }

    hr = MFStartup(MF_VERSION);
    if (FAILED(hr)) {
        HostLogHr("[ERROR] MFStartup failed", hr);
        CoUninitialize();
        return 1;
    }

    BOOL supported = FALSE;
    hr = MFIsVirtualCameraTypeSupported(MFVirtualCameraType_SoftwareCameraSource, &supported);
    HostLogHr("[info] MFIsVirtualCameraTypeSupported", hr);
    if (FAILED(hr) || !supported) {
        HostLog("[ERROR] Virtual cameras not supported (need Windows 11 22H2+).");
        MFShutdown();
        CoUninitialize();
        return 1;
    }
    HostLog("[OK] System supports virtual cameras.");

    ComPtr<IMFVirtualCamera> virtualCamera;
    HostLog("[info] calling MFCreateVirtualCamera...");
    hr = MFCreateVirtualCamera(
        MFVirtualCameraType_SoftwareCameraSource,
        MFVirtualCameraLifetime_Session,
        MFVirtualCameraAccess_CurrentUser,
        L"RednessCam",
        SOURCE_CLSID,
        nullptr,
        0,
        &virtualCamera
    );

    if (FAILED(hr)) {
        HostLogHr("[ERROR] MFCreateVirtualCamera failed", hr);
        HostLog("        Did you run regsvr32 RednessCamSource.dll as Administrator?");
        MFShutdown();
        CoUninitialize();
        return 1;
    }
    HostLog("[OK] Virtual camera created.");

    hr = virtualCamera->Start(nullptr);
    if (FAILED(hr)) {
        HostLogHr("[ERROR] Failed to start virtual camera", hr);
        HostLog("        Install DLL under C:\\ProgramData\\RednessCam (not C:\\Users\\...).");
        if (virtualCamera) {
            virtualCamera->Stop();
            virtualCamera->Shutdown();
            virtualCamera.Reset();
        }
        MFShutdown();
        CoUninitialize();
        return 2;
    }

    HostLog("========================================================");
    HostLog("  RednessCam is LIVE");
    HostLog("  In Teams: Devices -> Camera -> RednessCam");
    HostLog("  (shown as 'RednessCam Windows Virtual Camera')");
    HostLog("  Then run: py -m rednesscam run --strength 0.75");
    HostLog("========================================================");

    WaitUntilStop();

    HostLog("[RednessCam] Shutting down...");
    virtualCamera->Stop();
    virtualCamera->Shutdown();
    virtualCamera.Reset();
    MFShutdown();
    CoUninitialize();
    HostLog("[RednessCam] done");
    return 0;
}
