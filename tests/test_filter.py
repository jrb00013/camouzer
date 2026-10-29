import numpy as np

from rednesscam.filter import reduce_redness


def test_reduce_redness_lowers_red_channel_on_flush():
    # Solid reddish "skin-like" patch
    frame = np.zeros((64, 64, 3), dtype=np.uint8)
    frame[:, :] = (90, 110, 200)  # BGR — strong red
    out = reduce_redness(frame, strength=0.8)
    assert out.shape == frame.shape
    # Mean red channel should drop; blue/green should not explode upward.
    assert float(out[:, :, 2].mean()) < float(frame[:, :, 2].mean())


def test_strength_zero_is_identity():
    frame = np.random.randint(0, 255, (32, 32, 3), dtype=np.uint8)
    out = reduce_redness(frame, strength=0.0)
    assert np.array_equal(out, frame)


def test_bgr_to_nv12_size():
    from rednesscam.filter import bgr_to_nv12

    frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    nv12 = bgr_to_nv12(frame, 1280, 720)
    assert nv12.shape == (1280 * 720 * 3 // 2,)
    assert nv12.dtype == np.uint8
