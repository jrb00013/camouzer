"""Facial redness reduction (blood-vessel / flush softening)."""

from __future__ import annotations

import numpy as np


def reduce_redness(bgr: np.ndarray, strength: float = 0.45) -> np.ndarray:
    """Attenuate red-ward chroma in skin-like LAB regions.

    Parameters
    ----------
    bgr:
        HxWx3 uint8 BGR frame.
    strength:
        0 = no change, 1 = aggressive a-channel pull toward neutral on skin.
    """
    import cv2

    strength = float(np.clip(strength, 0.0, 1.0))
    if strength <= 1e-6:
        return bgr

    # Work on a downscaled copy for speed, then apply the a-channel delta full-res.
    h0, w0 = bgr.shape[:2]
    scale = 0.5 if max(h0, w0) >= 1280 else 1.0
    small = cv2.resize(bgr, (int(w0 * scale), int(h0 * scale)), interpolation=cv2.INTER_AREA) if scale < 1.0 else bgr

    lab = cv2.cvtColor(small, cv2.COLOR_BGR2LAB)
    L = lab[:, :, 0].astype(np.float32)
    a = lab[:, :, 1].astype(np.float32)
    bb = lab[:, :, 2].astype(np.float32)

    a_centered = a - 128.0
    red_amount = np.clip(a_centered, 0.0, None)
    skin = (
        (L > 40.0)
        & (L < 220.0)
        & (red_amount > 4.0)
        & (np.abs(bb - 128.0) < 55.0)
    ).astype(np.float32)
    skin = cv2.GaussianBlur(skin, (0, 0), sigmaX=2.0)

    # Delta to subtract from a (positive = less red)
    delta_a = (red_amount * strength * skin * 0.85).astype(np.float32)
    if scale < 1.0:
        delta_a = cv2.resize(delta_a, (w0, h0), interpolation=cv2.INTER_LINEAR)

    full = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
    full[:, :, 1] = np.clip(full[:, :, 1] - delta_a, 0, 255)

    # Light HSV sat hush on reds (also at half-res then upscaled)
    hsv_s = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
    h = hsv_s[:, :, 0].astype(np.float32)
    s = hsv_s[:, :, 1].astype(np.float32)
    red_hue = ((h < 12.0) | (h > 168.0)).astype(np.float32)
    sat_mul = 1.0 - 0.30 * strength * red_hue * skin
    if scale < 1.0:
        sat_mul = cv2.resize(sat_mul, (w0, h0), interpolation=cv2.INTER_LINEAR)

    out = cv2.cvtColor(full.astype(np.uint8), cv2.COLOR_LAB2BGR)
    hsv = cv2.cvtColor(out, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[:, :, 1] = np.clip(hsv[:, :, 1] * sat_mul, 0, 255)
    return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)


def bgr_to_nv12(bgr: np.ndarray, width: int, height: int) -> np.ndarray:
    """Resize BGR frame to width×height and convert to contiguous NV12 bytes."""
    import cv2

    if bgr.shape[1] != width or bgr.shape[0] != height:
        bgr = cv2.resize(bgr, (width, height), interpolation=cv2.INTER_AREA)
    # OpenCV returns I420 as shape (h*3/2, w) — flatten before slicing planes.
    i420 = np.ascontiguousarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2YUV_I420)).reshape(-1)
    y_size = width * height
    u = i420[y_size : y_size + y_size // 4]
    v = i420[y_size + y_size // 4 :]
    nv12 = np.empty(y_size + y_size // 2, dtype=np.uint8)
    nv12[:y_size] = i420[:y_size]
    nv12[y_size::2] = u
    nv12[y_size + 1 :: 2] = v
    return nv12
