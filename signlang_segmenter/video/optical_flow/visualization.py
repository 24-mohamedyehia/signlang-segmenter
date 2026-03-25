"""Visualization helpers for motion-based segmentation outputs."""

from collections.abc import Iterable

import matplotlib.pyplot as plt
import numpy as np

from .models import Segment


def plot_motion_segments(
    segments: Iterable[Segment],
    info: dict,
    *,
    figsize: tuple[float, float] = (14.0, 4.0),
    segment_alpha: float = 0.2,
    title: str = "Motion-based segmentation (shaded = detected segments)",
    show: bool = True,
):
    """Plot motion curves, thresholds, and shaded detected segments.

    Expected keys in info: motion_raw, motion_smooth, fps, frame_idx, th_high_arr, th_low_arr.
    """
    required = {
        "motion_raw",
        "motion_smooth",
        "fps",
        "frame_idx",
        "th_high_arr",
        "th_low_arr",
    }
    missing = [k for k in required if k not in info]
    if missing:
        raise KeyError(f"Missing required info keys: {missing}")

    motion = np.asarray(info["motion_raw"])
    motion_s = np.asarray(info["motion_smooth"])
    th_high_arr = np.asarray(info["th_high_arr"])
    th_low_arr = np.asarray(info["th_low_arr"])
    fps = float(info["fps"])
    frame_idx = np.asarray(info["frame_idx"])

    if fps <= 0:
        raise ValueError("fps must be > 0")
    if frame_idx.size < 2:
        raise ValueError("frame_idx must contain at least two indices")

    t = frame_idx[1:] / fps

    fig, ax = plt.subplots(figsize=figsize)
    ax.plot(t, motion, label="motion raw")
    ax.plot(t, motion_s, label="motion smooth")
    ax.plot(t, th_high_arr, linestyle="--", label="th_high")
    ax.plot(t, th_low_arr, linestyle="--", label="th_low")

    for seg in segments:
        ax.axvspan(seg.start_frame / fps, seg.end_frame / fps, alpha=segment_alpha)

    ax.set_xlabel("Time (sec)")
    ax.set_ylabel("Motion energy")
    ax.legend()
    ax.set_title(title)

    if show:
        plt.show()

    return fig, ax
