import re


TIMECODE_PATTERN = re.compile(
    r"TC\s+(\d{2}:\d{2}:\d{2}\.\d+)\s*-\s*(\d{2}:\d{2}:\d{2}\.\d+)"
)


def tc_to_seconds(tc: str) -> float:
    h, m, s = tc.split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def sanitize_label(label: str) -> str:
    safe = re.sub(r"[^\w\u0600-\u06FF]+", "_", label).strip("_")
    return safe or "empty_label"
