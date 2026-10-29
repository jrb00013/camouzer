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
    img = np.zeros((TARGET_HEIGHT, TARGET_WIDTH, 3), dtype=np.uint8)
    img[:, :] = (110, 140, 190)
    x = int((frame_index * 7) % (TARGET_WIDTH - 120))
    y = int((frame_index * 5) % (TARGET_HEIGHT - 80))
    img[y : y + 80, x : x + 120] = (60, 80, 220)
    import cv2

    cv2.putText(
        img,
        f"RednessCam test #{frame_index}",
        (40, 60),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.2,
        (20, 20, 20),
        2,
        cv2.LINE_AA,
    )
    return img


def run_pipeline(
    camera_index: int = 1,
    strength: float = 0.45,
    preview: bool = False,
    max_frames: Optional[int] = None,
    test_pattern: bool = False,
    device_name: Optional[str] = None,
    allow_test_fallback: bool = True,
) -> None:
    if sys.platform != "win32":
        raise RuntimeError("rednesscam virtual-camera output requires Windows.")

    import cv2

    cap = None
    using_pattern = test_pattern
    if not test_pattern:
        cam_name = device_name or "Logitech Webcam C930e"
        print(f"[rednesscam] opening camera via ffmpeg MJPG ({cam_name})", flush=True)
        try:
            from .ffmpeg_capture import FFmpegCamera

            cap = FFmpegCamera(
                device_name=cam_name,
                width=TARGET_WIDTH,
                height=TARGET_HEIGHT,
                fps=30,
            )
            ok, probe = cap.read()
            if not ok or probe is None:
                raise RuntimeError("ffmpeg opened but first frame failed")
            print(f"[rednesscam] ffmpeg frame ok shape={probe.shape}", flush=True)
        except Exception as exc:
            print(f"[rednesscam] ffmpeg path failed ({exc}); trying OpenCV", flush=True)
            try:
                cap = open_camera(
                    camera_index,
                    TARGET_WIDTH,
                    TARGET_HEIGHT,
                    fps=30,
                    device_name=device_name,
                )
            except RuntimeError as exc2:
                if not allow_test_fallback:
                    raise
                print(f"[rednesscam] WARN: {exc2}", flush=True)
                print("[rednesscam] falling back to test pattern", flush=True)
                using_pattern = True
                cap = None

    print("[rednesscam] connecting to RednessCam shared memory...", flush=True)
    writer = SharedMemoryWriter(timeout_s=90.0)
    mode = "test-pattern" if using_pattern else f"camera strength={strength:.2f}"
    print(f"[rednesscam] live — {mode} @ {TARGET_WIDTH}x{TARGET_HEIGHT}. Ctrl+C to stop.", flush=True)

    frames = 0
    t0 = time.time()
    try:
        while True:
            if using_pattern:
                frame = _test_pattern(frames)
            else:
                assert cap is not None
                ok, frame = cap.read()
                if not ok:
                    continue

            filtered = reduce_redness(frame, strength=strength)
            nv12 = bgr_to_nv12(filtered, TARGET_WIDTH, TARGET_HEIGHT)
            writer.write_nv12(nv12)
            frames += 1

            if preview:
                shown = cv2.resize(filtered, (640, 360))
                cv2.imshow("RednessCam preview (q quits)", shown)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

            if max_frames is not None and frames >= max_frames:
                break

            if frames == 1 or frames % 60 == 0:
                elapsed = time.time() - t0
                fps = frames / elapsed if elapsed else 0.0
                print(f"[rednesscam] frames={frames} ~{fps:.1f} fps", flush=True)
    except KeyboardInterrupt:
        print("\n[rednesscam] stopping...", flush=True)
    finally:
        writer.close()
        if cap is not None:
            cap.release()
        if preview:
            cv2.destroyAllWindows()
