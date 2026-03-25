"""SegmentExporter writes detected segments as individual video clips."""

import os
import shutil
import subprocess

import cv2

from .models import Segment


class SegmentExporter:
    """Export Segment objects as per-segment MP4 clip files."""

    _H264_CODECS = ("avc1", "H264", "X264")
    _WRITER_ATTEMPT_ORDER = ("mp4v", "avc1", "H264", "X264")

    def __init__(self, out_dir: str = "segments_out") -> None:
        self.out_dir = out_dir

    def export(self, video_path: str, segments: list[Segment]) -> str:
        """Cut and export segments from a source video to out_dir."""
        os.makedirs(self.out_dir, exist_ok=True)

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise FileNotFoundError(f"Cannot open video: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            fps = 25.0
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        for i, seg in enumerate(segments, start=1):
            self._write_segment(cap, seg, i, fps, (w, h))

        cap.release()
        return self.out_dir

    def _write_segment(
        self,
        cap: cv2.VideoCapture,
        seg: Segment,
        index: int,
        fps: float,
        size: tuple[int, int],
    ) -> None:
        final_path = os.path.join(
            self.out_dir,
            f"seg_{index:03d}_{seg.start_frame}_{seg.end_frame}.mp4",
        )
        raw_path = final_path.replace(".mp4", "_raw.mp4")

        writer, codec_used = self._open_writer(raw_path, fps, size)

        cap.set(cv2.CAP_PROP_POS_FRAMES, seg.start_frame)
        for _ in range(seg.start_frame, seg.end_frame + 1):
            ret, frame = cap.read()
            if not ret:
                break
            writer.write(frame)
        writer.release()

        if codec_used.lower() in {c.lower() for c in self._H264_CODECS}:
            os.replace(raw_path, final_path)
            return

        if self._transcode_to_h264(raw_path, final_path):
            if os.path.exists(raw_path):
                os.remove(raw_path)
        else:
            os.replace(raw_path, final_path)

    def _open_writer(
        self,
        path: str,
        fps: float,
        size: tuple[int, int],
    ) -> tuple[cv2.VideoWriter, str]:
        for codec in self._WRITER_ATTEMPT_ORDER:
            writer = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*codec), fps, size)
            if writer.isOpened():
                return writer, codec
            writer.release()
        raise RuntimeError("Could not initialize VideoWriter with available codecs.")

    @staticmethod
    def _transcode_to_h264(src_path: str, dst_path: str) -> bool:
        ffmpeg = shutil.which("ffmpeg")
        if ffmpeg is None:
            return False
        cmd = [
            ffmpeg,
            "-y",
            "-loglevel",
            "error",
            "-i",
            src_path,
            "-vf",
            "scale=trunc(iw/2)*2:trunc(ih/2)*2",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            "-an",
            dst_path,
        ]
        return subprocess.run(cmd).returncode == 0
