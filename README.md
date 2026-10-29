# RednessCam

Custom **Windows virtual camera** plus a Python library that softens facial redness (blood vessels / flush) on your Logitech feed and publishes it as a real device Discord can select.

**No OBS. No Unity Capture.** Device name: **RednessCam**.

```
Logitech C930e → Python rednesscam → shared memory → RednessCam (MF virtual cam) → Discord
```

Requires **Windows 11 22H2+** (this machine is fine). Native stack adapted from [BestCam](https://github.com/OneLimeStudio/BestCam) (GPL-2).

## Quick start (Windows)

Working copy used by the build scripts: `C:\Users\josep\rednesscam`

### One shot

```powershell
cd C:\Users\josep\rednesscam
powershell -ExecutionPolicy Bypass -File .\scripts\start_all.ps1
```

That rebuilds the native cam, installs it under `C:\ProgramData\RednessCam`, starts **RednessCamHost**, then runs the Python feed.

### Discord

1. User Settings → Voice & Video → Camera → **RednessCam** / **Windows Virtual Camera Device**
2. That frees the Logitech so Python can open it (if Discord still holds C930e, the feed falls back to a test pattern until you switch)

Tune: `--strength 0.3` … `0.7`. Preview: add `-Preview` to `start_all.ps1`. Stop: `.\scripts\stop_all.ps1`.

### Manual pieces

```powershell
.\scripts\build_native.ps1
.\scripts\install_virtual_cam.ps1
py -3 -m pip install -e .
py -3 -m rednesscam run --strength 0.45
```

DLL **must** live under `C:\ProgramData\RednessCam` (not `C:\Users\...`) or `IMFVirtualCamera::Start` returns Access Denied.

## Python API

```python
from rednesscam import reduce_redness, run_pipeline
import cv2

frame = cv2.imread("face.jpg")
soft = reduce_redness(frame, strength=0.5)
```

## Repo layout

| Path | Role |
|---|---|
| `src/rednesscam/` | Capture, redness filter, SHM writer, CLI |
| `native/` | `RednessCamSource.dll` + `RednessCamHost.exe` |
| `docs/kernel-camera-driver.md` | How a full kernel AVStream cam driver would work (not shipped) |
| `docs/superpowers/` | Design + plan |

## License

GPL-2.0-or-later (native bridge derived from BestCam). See `native/LICENSE` and root `LICENSE`.

## Repo

GitHub: https://github.com/jrb00013/rednesscam
