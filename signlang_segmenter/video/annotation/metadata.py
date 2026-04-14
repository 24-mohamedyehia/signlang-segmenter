import json
import subprocess


def probe_video_info(video_path: str) -> tuple[int | None, int | None, float | None]:
    """
    Return (width, height, fps) or (None, None, None) if probing fails.
    """
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height,r_frame_rate",
        "-of",
        "json",
        video_path,
    ]

    try:
        raw = subprocess.check_output(cmd, encoding="utf-8")
        data = json.loads(raw)
        streams = data.get("streams", [])
        if not streams:
            return None, None, None

        stream = streams[0]
        width = stream.get("width")
        height = stream.get("height")

        fps = None
        r_frame_rate = stream.get("r_frame_rate")
        if isinstance(r_frame_rate, str) and "/" in r_frame_rate:
            num, den = r_frame_rate.split("/", 1)
            den_i = int(den)
            fps = round(int(num) / den_i, 2) if den_i != 0 else 0.0

        return width, height, fps
    except (subprocess.CalledProcessError, FileNotFoundError, ValueError, KeyError, TypeError):
        return None, None, None
