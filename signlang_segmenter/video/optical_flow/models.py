from dataclasses import dataclass


@dataclass
class Segment:
    """Represents a single motion segment identified in a video."""

    start_frame: int
    end_frame: int
    video_path: str = ""

    @property
    def length_frames(self) -> int:
        return self.end_frame - self.start_frame + 1

    def to_seconds(self, fps: float) -> tuple[float, float]:
        """Return (start_sec, end_sec) for this segment."""
        return self.start_frame / fps, self.end_frame / fps

    def __repr__(self) -> str:
        return (
            f"Segment(start={self.start_frame}, end={self.end_frame}, "
            f"len={self.length_frames})"
        )
