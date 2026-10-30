// ============================================================================
// DllMain.cpp — COM DLL Entry Points & Registration
// ============================================================================
#include <windows.h>
#include <new>
#include <initguid.h>
#include "Activator.h"
#include "Logger.h"

// The unique CLSID for the Camouzer Virtual Webcam Source
DEFINE_GUID(CLSID_CamouzerMediaSource,
    0xa7c4e291, 0x8f12, 0x4b6d, 0x9e, 0x3a, 0x1d, 0x5c, 0x8f, 0x0b, 0x4a, 0x27);

static HMODULE g_hModule  = nullptr;
static LONG    g_objCount = 0;

class CamouzerClassFactory : public IClassFactory
{
    LONG _refCount = 1;

public:
    STDMETHODIMP QueryInterface(REFIID riid, void** ppv) override
    {
        if (!ppv) return E_POINTER;
        if (riid == IID_IUnknown || riid == IID_IClassFactory) {
            *ppv = static_cast<IClassFactory*>(this);
            AddRef();
            return S_OK;
        }
        *ppv = nullptr;
        return E_NOINTERFACE;
    }

    STDMETHODIMP_(ULONG) AddRef() override { return InterlockedIncrement(&_refCount); }
    
    STDMETHODIMP_(ULONG) Release() override {
        LONG ref = InterlockedDecrement(&_refCount);
        if (ref == 0) delete this;
        return ref;
    }

    STDMETHODIMP CreateInstance(IUnknown* pOuter, REFIID riid, void** ppv) override
    {
        Log("CamouzerClassFactory::CreateInstance called");
        if (pOuter) return CLASS_E_NOAGGREGATION;
        if (!ppv)   return E_POINTER;
        *ppv = nullptr;

        auto activator = Microsoft::WRL::Make<VirtualCamActivator>();
        if (!activator) return E_OUTOFMEMORY;

        HRESULT hr = activator->RuntimeClassInitialize();
        if (FAILED(hr)) return hr;

        InterlockedIncrement(&g_objCount);
        hr = activator->QueryInterface(riid, ppv);
        if (FAILED(hr)) {
            InterlockedDecrement(&g_objCount);
        }
        return hr;
    }

    STDMETHODIMP LockServer(BOOL fLock) override
    {
        if (fLock) InterlockedIncrement(&g_objCount);
        else       InterlockedDecrement(&g_objCount);
        return S_OK;
    }
};

BOOL WINAPI DllMain(HINSTANCE hInstDLL, DWORD fdwReason, LPVOID /*lpReserved*/)
{
    if (fdwReason == DLL_PROCESS_ATTACH) {
        g_hModule = hInstDLL;
        DisableThreadLibraryCalls(hInstDLL);
        Log("CamouzerSource.dll loaded");
    }
    return TRUE;
}

STDAPI DllGetClassObject(REFCLSID rclsid, REFIID riid, void** ppv)
{
    if (!ppv) return E_POINTER;
    *ppv = nullptr;

    if (rclsid != CLSID_CamouzerMediaSource)
        return CLASS_E_CLASSNOTAVAILABLE;

    auto factory = new (std::nothrow) CamouzerClassFactory();
    if (!factory) return E_OUTOFMEMORY;

    HRESULT hr = factory->QueryInterface(riid, ppv);
    factory->Release();
    return hr;
}

STDAPI DllCanUnloadNow()
{
    return (g_objCount == 0) ? S_OK : S_FALSE;
}

static const WCHAR* CLSID_STRING = L"{A7C4E291-8F12-4B6D-9E3A-1D5C8F0B4A27}";

STDAPI DllRegisterServer()
{
    WCHAR dllPath[MAX_PATH];
    GetModuleFileNameW(g_hModule, dllPath, MAX_PATH);

    HKEY hKey = nullptr;
    LSTATUS status;
    WCHAR keyPath[256];

    // Important: Register directly into HKEY_LOCAL_MACHINE, not HKEY_CLASSES_ROOT.
    // HKCR can silently redirect to HKCU under UAC, making the DLL invisible 
    // to the system Frame Server pipeline.
    wsprintfW(keyPath, L"SOFTWARE\\Classes\\CLSID\\%s", CLSID_STRING);
    status = RegCreateKeyExW(HKEY_LOCAL_MACHINE, keyPath, 0, nullptr, 0, KEY_WRITE, nullptr, &hKey, nullptr);
    if (status != ERROR_SUCCESS) return HRESULT_FROM_WIN32(status);

    const WCHAR desc[] = L"Camouzer Virtual Webcam Source";
    RegSetValueExW(hKey, nullptr, 0, REG_SZ, (const BYTE*)desc, sizeof(desc));
    RegCloseKey(hKey);

    wsprintfW(keyPath, L"SOFTWARE\\Classes\\CLSID\\%s\\InprocServer32", CLSID_STRING);
    status = RegCreateKeyExW(HKEY_LOCAL_MACHINE, keyPath, 0, nullptr, 0, KEY_WRITE, nullptr, &hKey, nullptr);
    if (status != ERROR_SUCCESS) return HRESULT_FROM_WIN32(status);

    RegSetValueExW(hKey, nullptr, 0, REG_SZ, (const BYTE*)dllPath, (DWORD)((wcslen(dllPath) + 1) * sizeof(WCHAR)));

    const WCHAR threading[] = L"Both";
    RegSetValueExW(hKey, L"ThreadingModel", 0, REG_SZ, (const BYTE*)threading, sizeof(threading));
    RegCloseKey(hKey);

    return S_OK;
}

STDAPI DllUnregisterServer()
{
    WCHAR keyPath[256];
    wsprintfW(keyPath, L"SOFTWARE\\Classes\\CLSID\\%s", CLSID_STRING);
    RegDeleteTreeW(HKEY_LOCAL_MACHINE, keyPath);
    return S_OK;
}
