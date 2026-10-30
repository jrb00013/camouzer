# Camouzer Design

**Date:** 2026-10-28  
**Status:** Approved (approach 2)  
**Goal:** Custom Windows virtual camera Discord can select; Logitech C930e in → face-redness reduction → virtual cam out. No OBS.

## Problem

Discord only enumerates camera devices. A Python process cannot inject frames into Discord without registering a fake camera with Windows (same class of problem as ViGEmBus for fake XInput pads).

## Chosen architecture (user-mode MF virtual camera)

```
Logitech C930e  →  Python camouzer  →  shared memory (NV12)
                                              ↓
                         CamouzerSource.dll (IMFMediaSource)
                                              ↓
                         CamouzerHost (MFCreateVirtualCamera)
                                              ↓
                                    Discord / any app
```

1. **Python library `camouzer`** — open the physical webcam, apply redness reduction, write NV12 frames into a Global shared-memory region.
2. **Native COM media source DLL** — loaded by Windows Frame Server; reads SHM; exposes a real camera device.
3. **Host process** — calls `MFCreateVirtualCamera` + `Start`, keeps the device alive for the session.
4. **No OBS. No Unity Capture.** Device friendly name: **Camouzer**.

### Redness filter

- Convert BGR → LAB; attenuate positive **a** channel (red–green) in skin-like regions (moderate L, moderate chroma), or selective HSV red-hue desaturation.
- Tunable `strength` (0–1). Default ~0.45 so vessels soften without gray plastic skin.
- Whole-frame processing v1 (no face mesh). Face-aware ROI is a later upgrade.

### Platform

- Windows 11 (build ≥ 22000). Confirmed target: build 26200.
- Runs as a **Windows** Python process (not WSL) so the cam and MF APIs are reachable.

### Out of scope for v1

- Kernel-mode camera minidriver (documented only — see `docs/kernel-camera-driver.md`).
- GPU face segmentation / beauty filters.
- macOS / Linux virtual cam backends.

## Licensing note

Native MF stack is adapted from the BestCam reference architecture (GPL-2). This repository is GPL-2 for the native bridge; Python filter code is original and distributed under the same license for the combined work.

## Success criteria

1. After install + `camouzer run`, Device Manager / Discord lists **Camouzer**.
2. Selecting it in Discord shows the live Logitech feed with reduced facial redness.
3. Strength is adjustable via CLI (`--strength`).
4. Kernel-driver path is documented for a future hard-mode rewrite.
