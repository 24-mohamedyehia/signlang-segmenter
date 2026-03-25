"""MotionAnalyzer computes a per-frame motion-energy curve via optical flow."""

import cv2
import numpy as np


class MotionAnalyzer:
    """Extract a 1-D motion-energy signal from a video using Farneback flow."""

    def __init__(
        self,
        roi_mode: str = "upper",
        resize_width: int = 320,
        step: int = 1,
    ) -> None:
        if roi_mode not in ("full", "upper"):
            raise ValueError("roi_mode must be 'full' or 'upper'")
        self.roi_mode = roi_mode
        self.resize_width = resize_width
        self.step = max(1, int(step))

    def compute(self, video_path: str) -> tuple[np.ndarray, np.ndarray, float, int]:
        """Compute motion-energy for a video path."""
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise FileNotFoundError(f"Cannot open video: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            fps = 25.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        ret, frame = cap.read()
        if not ret:
            cap.release()
            raise RuntimeError("Failed to read the first frame.")

        h0, w0 = frame.shape[:2]
        scale = 1.0
        if self.resize_width is not None and w0 > self.resize_width:
            scale = self.resize_width / w0
            frame = cv2.resize(frame, (int(w0 * scale), int(h0 * scale)))
        h, w = frame.shape[:2]

        prev_gray = cv2.cvtColor(self._crop_roi(frame, h), cv2.COLOR_BGR2GRAY)
        motion: list[float] = []
        frame_idx: list[int] = [0]
        idx = 0

        while True:
            for _ in range(self.step):
                ret, frame = cap.read()
                idx += 1
                if not ret:
                    cap.release()
                    return (
                        np.array(motion, dtype=np.float32),
                        np.array(frame_idx, dtype=int),
                        fps,
                        total_frames,
                    )

            if scale != 1.0:
                frame = cv2.resize(frame, (w, h))

            gray = cv2.cvtColor(self._crop_roi(frame, h), cv2.COLOR_BGR2GRAY)
            flow = cv2.calcOpticalFlowFarneback(
                prev_gray,
                gray,
                None,
                pyr_scale=0.5,
                levels=3,
                winsize=15,
                iterations=3,
                poly_n=5,
                poly_sigma=1.2,
                flags=0,
            )
            mag, _ = cv2.cartToPolar(flow[..., 0], flow[..., 1])
            motion.append(float(np.mean(mag)))
            frame_idx.append(idx)
            prev_gray = gray

    def _crop_roi(self, frame: np.ndarray, h: int) -> np.ndarray:
        if self.roi_mode == "full":
            return frame
        return frame[: int(h * 0.7), :]
