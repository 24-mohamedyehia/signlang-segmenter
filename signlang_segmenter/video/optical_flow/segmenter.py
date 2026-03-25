"""VideoSegmenter detects and returns motion-based segments in a video."""

import numpy as np

from .models import Segment
from .motion_analyzer import MotionAnalyzer
from .utils import (
    fill_short_gaps,
    hysteresis_binarize_var,
    mask_to_segments,
    moving_average,
    postprocess_segments,
)


class VideoSegmenter:
    """High-level optical-flow segmentation pipeline."""

    def __init__(
        self,
        roi_mode: str = "upper",
        resize_width: int = 320,
        step: int = 1,
        smooth_window: int = 7,
        min_len_sec: float = 0.25,
        merge_gap_sec: float = 0.15,
        pad_before_frames: int = 0,
        pad_after_frames: int = 0,
    ) -> None:
        self.smooth_window = smooth_window
        self.min_len_sec = min_len_sec
        self.merge_gap_sec = merge_gap_sec
        self.pad_before_frames = max(0, int(pad_before_frames))
        self.pad_after_frames = max(0, int(pad_after_frames))
        self._analyzer = MotionAnalyzer(
            roi_mode=roi_mode,
            resize_width=resize_width,
            step=step,
        )

    def segment(self, video_path: str) -> tuple[list[Segment], dict]:
        """Run segmentation on video_path and return segments with diagnostics."""
        motion, frame_idx, fps, total_frames = self._analyzer.compute(video_path)
        motion = motion.astype(np.float32)
        motion_s = moving_average(motion, self.smooth_window)

        th_high_arr, th_low_arr = self._adaptive_thresholds(motion_s, fps)
        active = hysteresis_binarize_var(motion_s, th_high_arr, th_low_arr)

        kernel = np.ones(max(1, int(fps * 0.25)))
        active = np.convolve(active.astype(float), kernel, mode="same") > 0

        active = fill_short_gaps(active, max_gap_frames=max(1, int(fps * 0.6)))
        segs = mask_to_segments(active)

        real_segments = self._remap_to_frames(segs, frame_idx)

        min_len_frames = max(1, int(self.min_len_sec * fps))
        merge_gap_frames = max(0, int(self.merge_gap_sec * fps))
        real_segments = postprocess_segments(
            real_segments,
            min_len_frames=min_len_frames,
            merge_gap_frames=merge_gap_frames,
        )
        real_segments = self._pad_segments(real_segments, total_frames)

        for seg in real_segments:
            seg.video_path = video_path

        info = {
            "fps": fps,
            "total_frames": total_frames,
            "th_high_arr": th_high_arr,
            "th_low_arr": th_low_arr,
            "motion_raw": motion,
            "motion_smooth": motion_s,
            "frame_idx": frame_idx,
            "active_mask": active,
        }
        return real_segments, info

    @staticmethod
    def _adaptive_thresholds(
        motion_s: np.ndarray,
        fps: float,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Compute local adaptive high and low thresholds."""
        win = max(5, int(fps * 1.0))
        local_mean = moving_average(motion_s, win)
        local_var = moving_average((motion_s - local_mean) ** 2, win)
        local_std = np.sqrt(np.maximum(local_var, 1e-8))
        th_high = local_mean + 1.15 * local_std
        th_low = local_mean + 0.65 * local_std
        return th_high, th_low

    @staticmethod
    def _remap_to_frames(segs: list[Segment], frame_idx: np.ndarray) -> list[Segment]:
        """Map motion-array segment indices back to original frame indices."""
        real_segments: list[Segment] = []
        for seg in segs:
            start = int(frame_idx[seg.start_frame + 1])
            end = int(frame_idx[seg.end_frame + 1])
            real_segments.append(Segment(start, end))
        return real_segments

    def _pad_segments(self, segments: list[Segment], total_frames: int) -> list[Segment]:
        """Expand segment boundaries by configured context then merge overlaps."""
        if not segments:
            return []

        if self.pad_before_frames == 0 and self.pad_after_frames == 0:
            return segments

        max_end = max(0, int(total_frames) - 1)
        expanded = [
            Segment(
                max(0, seg.start_frame - self.pad_before_frames),
                min(max_end, seg.end_frame + self.pad_after_frames),
            )
            for seg in segments
        ]
        return postprocess_segments(expanded, min_len_frames=1, merge_gap_frames=0)
