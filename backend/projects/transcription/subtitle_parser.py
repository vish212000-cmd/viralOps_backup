import re

def parse_subtitles(content: str, ext: str):
    """
    Parses SRT or VTT content into structured segments.
    Returns: (segments, duration_seconds)
    """
    segments = []
    duration_seconds = 0.0

    lines = [line.strip() for line in content.splitlines()]
    
    if ext == 'vtt':
        if len(lines) > 0 and 'WEBVTT' in lines[0]:
            lines = lines[1:]

    # A simple regex for timestamp lines
    # SRT: 00:00:01,000 --> 00:00:02,000
    # VTT: 00:00:01.000 --> 00:00:02.000
    timestamp_pattern = re.compile(r'(\d{2}:\d{2}:\d{2}[,.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,.]\d{3})')
    
    # Optional VTT timestamp without hours: 00:01.000 --> 00:02.000
    short_timestamp_pattern = re.compile(r'(\d{2}:\d{2}[,.]\d{3})\s*-->\s*(\d{2}:\d{2}[,.]\d{3})')

    def parse_time(time_str: str) -> float:
        # Normalize separator
        time_str = time_str.replace(',', '.')
        parts = time_str.split(':')
        if len(parts) == 3:
            h, m, s = parts
            return int(h) * 3600 + int(m) * 60 + float(s)
        elif len(parts) == 2:
            m, s = parts
            return int(m) * 60 + float(s)
        return 0.0

    current_start = 0.0
    current_end = 0.0
    current_text = []

    def commit_segment():
        nonlocal duration_seconds, segments, current_start, current_end, current_text
        text = " ".join(current_text).strip()
        if text:
            segments.append({
                "start": current_start,
                "end": current_end,
                "speaker": "Speaker 1",
                "text": text
            })
            if current_end > duration_seconds:
                duration_seconds = current_end
        current_text = []

    for line in lines:
        if not line:
            continue
            
        # Ignore purely numeric lines (SRT index)
        if line.isdigit():
            continue

        ts_match = timestamp_pattern.search(line)
        if not ts_match:
            ts_match = short_timestamp_pattern.search(line)

        if ts_match:
            commit_segment()
            current_start = parse_time(ts_match.group(1))
            current_end = parse_time(ts_match.group(2))
        else:
            # It's text
            # Clean VTT tags like <v Speaker> or <c.color>
            clean_line = re.sub(r'<[^>]+>', '', line)
            if clean_line:
                current_text.append(clean_line)

    commit_segment()
    
    if not segments:
        raise ValueError(f"Could not parse any valid {ext.upper()} segments from the file.")

    return segments, int(duration_seconds)
