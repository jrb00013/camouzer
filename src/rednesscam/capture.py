"""OpenCV capture helpers for the physical Logitech (or any) webcam."""

from __future__ import annotations

from typing import Optional

import cv2

# Preferred names for this machine; first match wins when probing.
PREFERRED_NAME_SUBSTR = ("c930", "logitech", "webcam")


def open_camera(
    index: int = 0,
    width: int = 1920,
    height: int = 1080,
    fps: int = 30,
    device_name: Optional[str] = None,
) -> cv2.VideoCapture:
    """Open a webcam on Windows (name → MSMF → DirectShow)."""
    candidates: list[tuple[object, object]] = []

    if device_name:
        if hasattr(cv2, "CAP_DSHOW"):
            candidates.append((f"video={device_name}", cv2.CAP_DSHOW))
        if hasattr(cv2, "CAP_MSMF"):
            candidates.append((device_name, cv2.CAP_MSMF))

    backends: list[int] = []
    if hasattr(cv2, "CAP_MSMF"):
        backends.append(cv2.CAP_MSMF)
    if hasattr(cv2, "CAP_DSHOW"):
        backends.append(cv2.CAP_DSHOW)
    backends.append(cv2.CAP_ANY)

    for backend in backends:
        candidates.append((index, backend))
        # Also try nearby indices — Discord / Studio Effects shift numbering.
        if isinstance(index, int):
            for alt in (index + 1, index + 2, 1, 2, 0):
                if alt != index:
                    candidates.append((alt, backend))

    last_err: Optional[str] = None
    seen: set[str] = set()
    for source, backend in candidates:
        key = f"{source}|{backend}"
        if key in seen:
            continue
        seen.add(key)
        cap = cv2.VideoCapture(source, backend)
        if not cap.isOpened():
            last_err = f"source={source!r} backend={backend}"
            continue
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        cap.set(cv2.CAP_PROP_FPS, fps)
        ok, frame = cap.read()
        if not ok or frame is None:
            cap.release()
            last_err = f"source={source!r} backend={backend} opened but read failed"
            continue
        return cap

    raise RuntimeError(
        f"Could not open camera ({last_err}). "
        "In Discord, switch Camera to RednessCam (or turn video off) so the "
        "Logitech is free, then re-run rednesscam."
    )


def list_camera_indices(max_index: int = 8) -> list[int]:
    found: list[int] = []
    for i in range(max_index):
        try:
            cap = open_camera(i)
        except RuntimeError:
            continue
        cap.release()
        found.append(i)
    return found
