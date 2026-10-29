"""OpenCV capture helpers — force MJPG 720p for usable FPS on C930e."""

from __future__ import annotations

from typing import Optional

import cv2


def _fourcc_str(cap: cv2.VideoCapture) -> str:
    v = int(cap.get(cv2.CAP_PROP_FOURCC))
    return "".join(chr((v >> (8 * i)) & 0xFF) for i in range(4))


def _configure_fast(cap: cv2.VideoCapture, width: int, height: int, fps: int) -> None:
    # Order matters on many UVC devices: FOURCC first, then size, then fps.
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, float(width))
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, float(height))
    cap.set(cv2.CAP_PROP_FPS, float(fps))
    try:
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    except Exception:
        pass
    # Convert mode / autofocus thrash kills FPS — leave defaults otherwise.


def open_camera(
    index: int = 1,
    width: int = 1280,
    height: int = 720,
    fps: int = 30,
    device_name: Optional[str] = None,
) -> cv2.VideoCapture:
    """Open webcam; require a fast mode (prefer <=720p MJPG)."""
    candidates: list[tuple[object, int]] = []
    if device_name and hasattr(cv2, "CAP_DSHOW"):
        candidates.append((f"video={device_name}", cv2.CAP_DSHOW))
    if hasattr(cv2, "CAP_DSHOW"):
        for i in (index, 0, 1, 2):
            candidates.append((i, cv2.CAP_DSHOW))
    if hasattr(cv2, "CAP_MSMF"):
        for i in (index, 0, 1, 2):
            candidates.append((i, cv2.CAP_MSMF))

    last_err: Optional[str] = None
    seen: set[str] = set()
    best: tuple[cv2.VideoCapture, object, int, tuple] | None = None

    for source, backend in candidates:
        key = f"{source}|{backend}"
        if key in seen:
            continue
        seen.add(key)
        cap = cv2.VideoCapture(source, backend)
        if not cap.isOpened():
            last_err = f"source={source!r} backend={backend}"
            continue

        _configure_fast(cap, width, height, fps)
        # Warm up + apply mode
        ok, frame = None, None
        for _ in range(5):
            ok, frame = cap.read()
        if not ok or frame is None:
            cap.release()
            last_err = f"source={source!r} backend={backend} read failed"
            continue

        fcc = _fourcc_str(cap)
        got_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        got_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print(
            f"[rednesscam] try source={source!r} be={backend} "
            f"fourcc={fcc!r} nego={got_w}x{got_h} frame={frame.shape}",
            flush=True,
        )

        # Prefer MJPG and <= requested size.
        score = 0
        if "MJPG" in fcc.upper() or "JPEG" in fcc.upper():
            score += 100
        if frame.shape[1] <= width + 16 and frame.shape[0] <= height + 16:
            score += 50
        elif frame.shape[1] * frame.shape[0] <= width * height * 2:
            score += 10

        if best is None or score > best[3][0]:
            if best is not None:
                best[0].release()
            best = (cap, source, backend, (score, fcc, frame.shape))
            # Good enough — take it
            if score >= 150:
                break
        else:
            cap.release()

    if best is None:
        raise RuntimeError(
            f"Could not open camera ({last_err}). "
            "In Teams, pick RednessCam (not Logitech) so the webcam is free."
        )

    cap, source, backend, (score, fcc, shape) = best
    print(
        f"[rednesscam] camera ok source={source!r} backend={backend} "
        f"fourcc={fcc!r} shape={shape} score={score}",
        flush=True,
    )
    return cap


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
