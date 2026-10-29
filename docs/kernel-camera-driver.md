# Full custom kernel camera driver (documented, not built in v1)

RednessCam v1 uses **user-mode** Media Foundation virtual cameras (`MFCreateVirtualCamera` + COM `IMFMediaSource`). That is the supported Windows 11 path and what Discord enumerates today.

If you ever need a **kernel** fake camera (ViGEm-style, visible even to apps that reject software sources, or pre-Win11), you are in AVStream / KMDF land. This doc is the map — not an implementation.

## What “like xinput / ViGEm” means for cameras

| Controllers | Cameras |
|---|---|
| ViGEmBus.sys exposes virtual XUSB/HID gamepads | An **AVStream** minidriver exposes a capture pin under `KSCATEGORY_VIDEO_CAMERA` |
| User-mode client submits button/axis reports | User-mode (or kernel) client submits video frames into the pin’s allocator |
| Signed driver + INF install | Signed driver + INF; Secure Boot demands attestation signing for broad deploy |

There is no supported one-file Python API that creates a kernel camera. You ship a `.sys` + `.inf` (+ catalog), install it, then a user-mode app opens the device and feeds buffers.

## Microsoft stack to study

1. **AVStream** — streaming class for cameras/tuners (`stream.sys` clients).
2. **KS** (Kernel Streaming) — pins, formats (`KSDATAFORMAT_TYPE_VIDEO`, subtypes NV12/YUY2…).
3. **KMDF** — modern driver framework wrapping WDM.
4. Samples / references:
   - Microsoft **AVStream simulated capture** / softcam-style samples in older WDK trees
   - WDK **Toaster** / general KMDF patterns for INF + PnP
   - DirectShow **virtual cam** filters (user-mode legacy) — Discord/Zoom increasingly prefer MF devices

## Rough architecture for a kernel RednessCam

```
User app (Python/C++)
   │  DeviceIoControl / shared memory / queue
   ▼
RednessCam.sys  (KMDF + AVStream)
   │  Capture pin, NV12 1920x1080@30
   ▼
KS proxy / Frame Server
   ▼
Discord
```

### Driver responsibilities

- Register as a camera under the right device interface GUIDs.
- Advertise media types (NV12 preferred).
- Own buffer pool; copy or map incoming frames from user mode.
- Timestamp samples; handle run/stop/flush.
- Survive surprise remove; power IRPs.

### User-mode companion

- Open the symbolic link created by the INF.
- Push frames (IOCTL with MDL, or shared section mapped into kernel).
- Same redness filter as today; only the sink changes from SHM→MF DLL to SHM→`.sys`.

## Signing & install reality

- **Test mode** / self-signed: fine for your machine.
- **Production**: EV cert + Microsoft attestation signing for kernel; Partner Center submission.
- INF must declare camera class correctly or UWP/Discord privacy toggles will hide you.

## Why v1 did not do this

- Weeks of WDK work vs a working MF software camera Discord already accepts.
- Kernel bugs = bugchecks; MF bugs = a stuck preview.
- Win11 already gives a first-class software camera API.

## When to revisit

- Target OS &lt; Win11 22H2 with no MF virtual cam.
- An app explicitly filters out software / virtual cameras.
- You need multiple simultaneous virtual devices with custom KS properties.

Until then: keep the Python filter, keep SHM, swap only the sink if you graduate to `.sys`.

# Build tip
Build from a Windows NTFS checkout (not a `\\wsl$` UNC path) so MSVC/CMake work cleanly.
