from .utils import TIMECODE_PATTERN


def parse_annotation_segments(content: str, pattern: str = "default") -> list[tuple[str, str, str]]:
    """
    Return a list of tuples in the form (label, start_tc, end_tc).
    """
    chunks = content.split(pattern)[1:]
    parsed: list[tuple[str, str, str]] = []

    for chunk in chunks:
        lines = chunk.strip().splitlines()
        if not lines:
            continue

        label = lines[0].strip()
        match = TIMECODE_PATTERN.search(chunk)
        if not match:
            continue

        start_tc, end_tc = match.groups()
        parsed.append((label, start_tc, end_tc))

    return parsed
