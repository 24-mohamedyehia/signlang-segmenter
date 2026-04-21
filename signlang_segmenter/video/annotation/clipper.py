from __future__ import annotations

import csv
import os
import shutil
import subprocess
from dataclasses import asdict
from pathlib import Path
from typing import Any

from tqdm.auto import tqdm

from .metadata import probe_video_info
from .models import ClipRecord
from .parser import parse_annotation_segments
from .utils import sanitize_label, tc_to_seconds


def _ensure_ffmpeg_available() -> None:
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg is not available in PATH.")
    if shutil.which("ffprobe") is None:
        raise RuntimeError("ffprobe is not available in PATH.")


def _find_video(videos_dir: str, stem: str, video_extensions: tuple[str, ...]) -> str | None:
    for ext in video_extensions:
        candidate = os.path.join(videos_dir, f"{stem}{ext}")
        if os.path.exists(candidate):
            return candidate

        candidate_lower = os.path.join(videos_dir, f"{stem}{ext.lower()}")
        if os.path.exists(candidate_lower):
            return candidate_lower

        candidate_upper = os.path.join(videos_dir, f"{stem}{ext.upper()}")
        if os.path.exists(candidate_upper):
            return candidate_upper

    return None


def _build_ffmpeg_cmd(
    video_path: str,
    start_tc: str,
    end_tc: str,
    output_file: str,
    reencode: bool,
) -> list[str]:
    cmd = ["ffmpeg", "-y", "-i", video_path, "-ss", start_tc, "-to", end_tc]
    if reencode:
        cmd += ["-c:v", "libx264", "-c:a", "copy"]
    else:
        cmd += ["-c", "copy"]
    cmd.append(output_file)
    return cmd


def split_video_with_timecode(
    annotations_dir: str,
    videos_dir: str,
    output_dir: str,
    csv_file: str | None = None,
    pattern: str = "default",
    video_extensions: tuple[str, ...] = (".mp4", ".mov", ".mkv"),
    dry_run: bool = False,
    reencode: bool = True,
) -> Any:
    """
    Split videos into clips from annotation text files.

    Returns a pandas DataFrame when pandas is installed, otherwise returns
    a list of dictionaries.
    """
    _ensure_ffmpeg_available()

    annotations_path = Path(annotations_dir)
    videos_path = Path(videos_dir)
    output_path = Path(output_dir)

    if not annotations_path.exists():
        raise FileNotFoundError(f"annotations_dir does not exist: {annotations_dir}")
    if not videos_path.exists():
        raise FileNotFoundError(f"videos_dir does not exist: {videos_dir}")

    output_path.mkdir(parents=True, exist_ok=True)

    records: list[ClipRecord] = []
    global_counter = 1
    processed_tasks: set[tuple[str, str, str]] = set()

    if csv_file:
        csv_path = Path(csv_file)
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        if csv_path.exists() and csv_path.stat().st_size > 0:
            with csv_path.open("r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    processed_tasks.add((row.get("annotation_file", ""), row.get("start_tc", ""), row.get("end_tc", "")))

                    def _parse_int(val: Any) -> int | None:
                        try:
                            return int(val) if val else None
                        except (ValueError, TypeError):
                            return None

                    def _parse_float(val: Any) -> float | None:
                        try:
                            return float(val) if val else None
                        except (ValueError, TypeError):
                            return None

                    records.append(
                        ClipRecord(
                            attachment_id=row.get("attachment_id", ""),
                            width=_parse_int(row.get("width")),
                            height=_parse_int(row.get("height")),
                            duration=_parse_float(row.get("duration")) or 0.0,
                            fps=_parse_float(row.get("fps")),
                            text=row.get("text", ""),
                            source_video=row.get("source_video", ""),
                            annotation_file=row.get("annotation_file", ""),
                            start_tc=row.get("start_tc", ""),
                            end_tc=row.get("end_tc", ""),
                        )
                    )
                    
                    try:
                        att_id = row.get("attachment_id", "")
                        num = int(att_id.split("_")[-1].split(".")[0])
                        if num >= global_counter:
                            global_counter = num + 1
                    except (ValueError, IndexError):
                        pass
        else:
            with csv_path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=[
                        "attachment_id",
                        "width",
                        "height",
                        "duration",
                        "fps",
                        "text",
                        "source_video",
                        "annotation_file",
                        "start_tc",
                        "end_tc",
                    ],
                )
                writer.writeheader()

    annotation_files = sorted(p for p in annotations_path.iterdir() if p.suffix.lower() == ".txt")

    # Phase 1: Parse all files and gather all tasks
    clip_tasks = []
    for annotation_file in annotation_files:
        video_path = _find_video(str(videos_path), annotation_file.stem, video_extensions)
        if video_path is None:
            continue

        width, height, fps = probe_video_info(video_path)

        content = annotation_file.read_text(encoding="utf-8")
        segments = parse_annotation_segments(content, pattern=pattern)

        for label, start_tc, end_tc in segments:
            if (annotation_file.name, start_tc, end_tc) in processed_tasks:
                continue

            clip_tasks.append({
                "video_path": video_path,
                "annotation_file": annotation_file,
                "width": width,
                "height": height,
                "fps": fps,
                "label": label,
                "start_tc": start_tc,
                "end_tc": end_tc,
            })

    # Phase 2: Process all clips with a single global progress bar
    for task in tqdm(clip_tasks, desc="Extracting clips"):
        label = task["label"]
        start_tc = task["start_tc"]
        end_tc = task["end_tc"]
        video_path = task["video_path"]
        annotation_file = task["annotation_file"]

        duration = round(tc_to_seconds(end_tc) - tc_to_seconds(start_tc), 2)
        safe_label = sanitize_label(label)
        clip_name = f"clip_{global_counter:05d}.mp4"
        output_file = output_path / clip_name

        if not dry_run:
            cmd = _build_ffmpeg_cmd(
                video_path=video_path,
                start_tc=start_tc,
                end_tc=end_tc,
                output_file=str(output_file),
                reencode=reencode,
            )
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)

        record = ClipRecord(
            attachment_id=clip_name,
            width=task["width"],
            height=task["height"],
            duration=duration,
            fps=task["fps"],
            text=label,
            source_video=os.path.basename(video_path),
            annotation_file=annotation_file.name,
            start_tc=start_tc,
            end_tc=end_tc,
        )
        records.append(record)
        global_counter += 1

        if csv_file:
            with csv_path.open("a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=[
                        "attachment_id",
                        "width",
                        "height",
                        "duration",
                        "fps",
                        "text",
                        "source_video",
                        "annotation_file",
                        "start_tc",
                        "end_tc",
                    ],
                )
                writer.writerow(asdict(record))

    rows = [asdict(r) for r in records]
    try:
        import pandas as pd  # type: ignore

        output: Any = pd.DataFrame(rows)
    except ImportError:
        output = rows

    return output
