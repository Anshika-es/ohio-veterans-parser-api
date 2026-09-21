
from parsers.requirement import parse_email

def test_normalized_pipe_unicode_arrow():
    r = parse_email("", "2026-09-12 | 15:00:00 → 23:30:00 | LPN | 1", 2026)
    assert r.status == "PARSED"
    assert r.shift_count == 1
    s = r.shifts[0]
    assert s.shift_date == "2026-09-12"
    assert s.start_time == "15:00:00"
    assert s.end_time == "23:30:00"
    assert s.skill == "LPN"
    assert s.required_count == 1

def test_normalized_pipe_ascii_arrow():
    r = parse_email("", "2026-09-12 | 23:00 -> 07:30 | STNA | 2", 2026)
    assert r.status == "PARSED"
    assert r.shift_count == 1
    s = r.shifts[0]
    assert s.start_time == "23:00:00"
    assert s.end_time == "07:30:00"
    assert s.skill == "STNA"
    assert s.required_count == 2

def test_mixed_raw_and_normalized_lines():
    body = """9/12 (11pm-730am) 1 LPN
2026-09-13 | 15:00:00 → 23:30:00 | STNA | 2"""
    r = parse_email("", body, 2026)
    assert r.status == "PARSED"
    assert r.shift_count == 2
