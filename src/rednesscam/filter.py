"""Facial redness reduction — fast path for live Teams/Discord."""

from __future__ import annotations

import numpy as np


def reduce_redness(bgr: np.ndarray, strength: float = 0.45) -> np.ndarray:
    """Pull red flush down cheaply (quarter-res mask, BGR only)."""
    import cv2

    strength = float(np.clip(strength, 0.0, 1.0))
    if strength <= 1e-6:
        return bgr

    h0, w0 = bgr.shape[:2]
    # Quarter-res work image keeps this under a few ms even at 720p/1080p.
    sw, sh = max(1, w0 // 4), max(1, h0 // 4)
    small = cv2.resize(bgr, (sw, sh), interpolation=cv2.INTER_AREA)

    b, g, r = cv2.split(small)
    # Flush = red ahead of green (and a bit ahead of blue).
    excess = cv2.subtract(r, g)
    # Ignore tiny differences (noise / lips edge cases stay).
    _, mask = cv2.threshold(excess, 12, 255, cv2.THRESH_BINARY)
    mask = cv2.GaussianBlur(mask, (0, 0), sigmaX=1.2)

    pull = (excess.astype(np.float32) * (0.75 * strength) * (mask.astype(np.float32) / 255.0))
    r2 = np.clip(r.astype(np.float32) - pull, 0, 255).astype(np.uint8)
    # Mild green lift so skin doesn't go gray-magenta.
    g2 = np.clip(g.astype(np.float32) + pull * 0.15, 0, 255).astype(np.uint8)

    fixed = cv2.merge([b, g2, r2])
    if (sw, sh) != (w0, h0):
        return cv2.resize(fixed, (w0, h0), interpolation=cv2.INTER_LINEAR)
    return fixed


def bgr_to_nv12(bgr: np.ndarray, width: int, height: int) -> np.ndarray:
    """Resize BGR frame to width×height and convert to contiguous NV12 bytes."""
    import cv2

    if bgr.shape[1] != width or bgr.shape[0] != height:
        bgr = cv2.resize(bgr, (width, height), interpolation=cv2.INTER_LINEAR)
    i420 = np.ascontiguousarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2YUV_I420)).reshape(-1)
    y_size = width * height
    u = i420[y_size : y_size + y_size // 4]
    v = i420[y_size + y_size // 4 :]
    nv12 = np.empty(y_size + y_size // 2, dtype=np.uint8)
    nv12[:y_size] = i420[:y_size]
    nv12[y_size::2] = u
    nv12[y_size + 1 :: 2] = v
    return nv12
