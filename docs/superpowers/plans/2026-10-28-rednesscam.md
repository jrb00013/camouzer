# RednessCam Implementation Plan

> **For agentic workers:** Implement task-by-task. Steps use checkbox syntax.

**Goal:** Ship a GPL-2 repo with a Windows MF virtual camera named RednessCam plus a Python library that captures the Logitech webcam, reduces facial redness, and feeds NV12 frames into that device for Discord.

**Architecture:** Python producer → Global shared memory → RednessCamSource.dll (IMFMediaSource) ← RednessCamHost (MFCreateVirtualCamera).

**Tech Stack:** C++17 / CMake / Windows SDK 10.0.26100+, Python 3.11, OpenCV, NumPy.

## Global Constraints

- No OBS, no Unity Capture.
- Windows 11 build ≥ 22000 (target 26200).
- Device friendly name: `RednessCam`.
- Native stack adapted from BestCam (GPL-2); keep LICENSE.
- Document kernel-mode driver path; do not implement it in v1.

---

### Task 1: Native RednessCam virtual camera
- [ ] Rebrand BestCam native sources (CLSID, SHM names, device name)
- [ ] CMake build Release x64
- [ ] Install script: regsvr32 + note host must stay running

### Task 2: Python `rednesscam` library
- [ ] Package layout, redness filter, SHM writer, CLI `rednesscam run`
- [ ] Unit test for filter math (no Windows required)

### Task 3: Docs + repo
- [ ] README (Discord switch steps)
- [ ] `docs/kernel-camera-driver.md`
- [ ] git init + initial commit
