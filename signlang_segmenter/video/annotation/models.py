from dataclasses import dataclass


@dataclass
class ClipRecord:
    attachment_id: str
    width: int | None
    height: int | None
    duration: float
    fps: float | None
    text: str
    source_video: str
    annotation_file: str
    start_tc: str
    end_tc: str
