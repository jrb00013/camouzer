# RednessCam

Custom **Windows virtual camera** plus a Python library that softens facial redness (blood vessels / flush) on a webcam feed and publishes it as a real device **Teams / Discord / Camera** can select.

**No OBS. No Unity Capture.** Device name: **RednessCam**.

```
Webcam → Python rednesscam (MJPG via ffmpeg) → shared memory → RednessCam (MF virtual cam) → Teams
```

Requires **Windows 11 22H2+**. Native stack adapted from [BestCam](https://github.com/OneLimeStudio/BestCam) (GPL-2).

## Quick start (Windows)

Clone/copy the repo onto a normal Windows path (not a `\\wsl$\...` UNC path), then:

```powershell
cd <this-repo>
powershell -ExecutionPolicy Bypass -File .\scripts\start_all.ps1
```

That rebuilds the native cam, installs it under `C:\ProgramData\RednessCam`, starts **RednessCamHost**, then runs the Python feed.

### Teams

1. Start RednessCam **before** turning on your camera in the call (so the feed owns the physical webcam).
2. Settings → Devices → Camera → **RednessCam (Windows Virtual Camera)** — not the raw Logitech.
3. If Teams already locked the Logitech, FPS will tank; turn camera off, restart the feed, pick RednessCam only.

Tune: `--strength 0.3` … `0.75`. Preview: `.\scripts\start_all.ps1 -Preview`. Stop: `.\scripts\stop_all.ps1`.

### Manual pieces

```powershell
.\scripts\build_native.ps1
.\scripts\install_virtual_cam.ps1
py -3 -m pip install -e .
py -3 -m rednesscam run --strength 0.75
```

Needs **ffmpeg** on `PATH` (or a WinGet ffmpeg install under `%LOCALAPPDATA%`).

DLL **must** live under `C:\ProgramData\RednessCam` (not under a user profile tree) or `IMFVirtualCamera::Start` returns Access Denied.

## Python API

```python
from rednesscam import reduce_redness, run_pipeline
import cv2

frame = cv2.imread("face.jpg")
soft = reduce_redness(frame, strength=0.5)
```

## Strength tips

Start at 0.45; raise toward 0.7+ only if vessels still show.

## Repo layout

| Path | Role |
|---|---|
| `src/rednesscam/` | Capture, redness filter, SHM writer, CLI |
| `native/` | `RednessCamSource.dll` + `RednessCamHost.exe` |
| `docs/kernel-camera-driver.md` | How a full kernel AVStream cam driver would work (not shipped) |
| `docs/superpowers/` | Design + plan |

## Repo

GitHub: https://github.com/jrb00013/rednesscam

## License

GPL-2.0-or-later (native bridge derived from BestCam). See `native/LICENSE` and root `LICENSE`.
