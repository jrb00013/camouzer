"""End-to-end: webcam → redness filter → RednessCam shared memory."""

from __future__ import annotations

import sys
import time
from typing import Optional

import numpy as np

from .capture import open_camera
from .filter import bgr_to_nv12, reduce_redness
from .shm import TARGET_HEIGHT, TARGET_WIDTH, SharedMemoryWriter


def _test_pattern(frame_index: int) -> np.ndarray:
    """BGR test pattern so Discord still shows a live feed without a webcam."""
    img = np.zeros((TARGET_HEIGHT, TARGET_WIDTH, 3), dtype=np.uint8)
    # Soft skin-ish tone so strength tuning is visible later.
    img[:, :] = (110, 140, 190)
    x = int((frame_index * 7) % (TARGET_WIDTH - 120))
    y = int((frame_index * 5) % (TARGET_HEIGHT - 80))
    img[y : y + 80, x : x + 120] = (60, 80, 220)  # moving red patch
    import cv2

    cv2.putText(
        img,
        f"RednessCam test pattern #{frame_index}",
        (40, 80),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.4,
        (20, 20, 20),
        3,
        cv2.LINE_AA,
    )
    cv2.putText(
        img,
        "Switch Discord to RednessCam, free the Logitech, rerun without --test-pattern",
        (40, 140),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (30, 30, 30),
        2,
        cv2.LINE_AA,
    )
    return img


def run_pipeline(
    camera_index: int = 0,
    strength: float = 0.45,
    preview: bool = False,
    max_frames: Optional[int] = None,
    test_pattern: bool = False,
    device_name: Optional[str] = None,
    allow_test_fallback: bool = True,
) -> None:
    """Capture, filter, and publish until interrupted.

    Requires RednessCamHost.exe already running so shared memory exists.
    Discord must use camera device **RednessCam**, not the raw Logitech.
    """
    if sys.platform != "win32":
        raise RuntimeError("rednesscam virtual-camera output requires Windows.")

    import cv2

    cap = None
    using_pattern = test_pattern
    if not test_pattern:
        print(f"[rednesscam] opening camera index={camera_index} name={device_name!r}")
        try:
            cap = open_camera(
                camera_index,
                TARGET_WIDTH,
                TARGET_HEIGHT,
                device_name=device_name,
            )
        except RuntimeError as exc:
            if not allow_test_fallback:
                raise
            print(f"[rednesscam] WARN: {exc}")
            print("[rednesscam] falling back to test pattern so the virtual cam stays alive")
            using_pattern = True

    print("[rednesscam] connecting to RednessCam shared memory (host must be running)...")
    writer = SharedMemoryWriter(timeout_s=90.0)
    mode = "test-pattern" if using_pattern else f"camera strength={strength:.2f}"
    print(f"[rednesscam] live — {mode}. Ctrl+C to stop.")

    frames = 0
    t0 = time.time()
    try:
        while True:
            if using_pattern:
                frame = _test_pattern(frames)
                filtered = reduce_redness(frame, strength=strength)
            else:
                assert cap is not None
                ok, frame = cap.read()
                if not ok:
                    time.sleep(0.01)
                    continue
                filtered = reduce_redness(frame, strength=strength)

            nv12 = bgr_to_nv12(filtered, TARGET_WIDTH, TARGET_HEIGHT)
            writer.write_nv12(nv12)
            frames += 1

            if preview:
                shown = cv2.resize(filtered, (960, 540))
                cv2.imshow("RednessCam preview (q quits)", shown)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

            if max_frames is not None and frames >= max_frames:
                break

            if frames % 120 == 0:
                elapsed = time.time() - t0
                fps = frames / elapsed if elapsed else 0.0
                print(f"[rednesscam] frames={frames} ~{fps:.1f} fps")
    except KeyboardInterrupt:
        print("\n[rednesscam] stopping...")
    finally:
        writer.close()
        if cap is not None:
            cap.release()
        if preview:
            cv2.destroyAllWindows()
