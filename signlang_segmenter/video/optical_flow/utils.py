"""Signal-processing utilities used by the optical-flow segmentation pipeline."""

import numpy as np

from .models import Segment


def moving_average(x: np.ndarray, window: int) -> np.ndarray:
    """Smooth a 1-D array with a uniform moving average."""
    if window <= 1:
        return x.astype(np.float32)
    kernel = np.ones(int(window), dtype=np.float32) / int(window)
    return np.convolve(x, kernel, mode="same")


def hysteresis_binarize_var(
    signal: np.ndarray,
    th_high_arr: np.ndarray,
    th_low_arr: np.ndarray,
) -> np.ndarray:
    """Hysteresis thresholding with per-sample adaptive thresholds."""
    active = np.zeros_like(signal, dtype=bool)
    on = False
    for i, value in enumerate(signal):
        if not on and value >= th_high_arr[i]:
            on = True
        elif on and value <= th_low_arr[i]:
            on = False
        active[i] = on
    return active


def fill_short_gaps(active: np.ndarray, max_gap_frames: int) -> np.ndarray:
    """Fill short OFF gaps between two ON regions in a boolean mask."""
    mask = active.copy().astype(bool)
    n = len(mask)
    i = 0
    while i < n:
        if mask[i]:
            i += 1
            continue

        j = i
        while j < n and not mask[j]:
            j += 1

        gap_len = j - i
        left_true = i - 1 >= 0 and mask[i - 1]
        right_true = j < n and mask[j]
        if left_true and right_true and gap_len <= max_gap_frames:
            mask[i:j] = True
        i = j

    return mask


def mask_to_segments(active: np.ndarray) -> list[Segment]:
    """Convert a boolean activity mask to a list of Segment objects."""
    segments: list[Segment] = []
    in_segment = False
    start = 0

    for i, is_active in enumerate(active):
        if is_active and not in_segment:
            in_segment = True
            start = i
        elif (not is_active) and in_segment:
            in_segment = False
            segments.append(Segment(start, i - 1))

    if in_segment:
        segments.append(Segment(start, len(active) - 1))

    return segments


def postprocess_segments(
    segments: list[Segment],
    min_len_frames: int,
    merge_gap_frames: int,
) -> list[Segment]:
    """Drop short segments and merge close neighboring segments."""
    if not segments:
        return []

    filtered = [s for s in segments if s.length_frames >= min_len_frames]
    if not filtered:
        return []

    merged = [filtered[0]]
    for seg in filtered[1:]:
        prev = merged[-1]
        gap = seg.start_frame - prev.end_frame - 1
        if gap <= merge_gap_frames:
            merged[-1] = Segment(prev.start_frame, max(prev.end_frame, seg.end_frame))
        else:
            merged.append(seg)

    return merged
