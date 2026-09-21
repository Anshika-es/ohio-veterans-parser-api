from parsers.requirement import parse_email

def _pairs(r):
    return [(x.skill, x.required_count) for x in r.shifts]

def test_v3_plain_paragraphs():
    body = """Good morning,

Please review the staffing needs below.

9/12 (11pm-730am) 1 LPN, 2 STNAs

Thank you."""
    r = parse_email("", body, 2026)
    assert r.status == "PARSED"
    assert r.shift_count == 2

def test_v3_role_words_in_paragraph_are_noise():
    body = """We are reviewing LPN and STNA coverage this week.
Please see the actual need below.

9/12 (11pm-730am) 1 LPN"""
    r = parse_email("", body, 2026)
    assert r.status == "PARSED"
    assert r.shift_count == 1

def test_v3_labels():
    body = """Date: 9/12
Shift: 11pm-730am
Need: 1 LPN, 2 STNAs"""
    r = parse_email("", body, 2026)
    assert r.status == "PARSED"
    assert _pairs(r) == [("LPN", 1), ("STNA", 2)]

def test_v3_split_fields():
    body = """9/12
11pm-730am
1 LPN
2 STNAs"""
    r = parse_email("", body, 2026)
    assert r.status == "PARSED"
    assert r.shift_count == 2

def test_v3_natural_to():
    r = parse_email("", "For 9/12 we need 1 LPN from 11pm to 7:30am.", 2026)
    assert r.status == "PARSED"
    assert r.shift_count == 1

def test_v3_natural_until():
    r = parse_email("", "For 9/12 we need 2 STNAs from 3pm until 11:30pm.", 2026)
    assert r.status == "PARSED"
    assert r.shift_count == 1
    assert r.shifts[0].skill == "STNA"

def test_v3_natural_through():
    r = parse_email("", "9/12 need 1 LPN from 3pm through 11:30pm", 2026)
    assert r.status == "PARSED"
    assert r.shift_count == 1

def test_v3_month_name():
    r = parse_email("", "September 12, 2026 from 11pm to 7:30am - need 1 LPN.", 2026)
    assert r.status == "PARSED"
    assert r.shifts[0].shift_date == "2026-09-12"

def test_v3_short_month_name():
    r = parse_email("", "Sep 12 from 3pm to 11:30pm: 1 LPN", 2026)
    assert r.status == "PARSED"
    assert r.shift_count == 1

def test_v3_role_colon_count():
    r = parse_email("", "9/12 11pm-730am Need: LPN: 1, STNA: 2", 2026)
    assert r.status == "PARSED"
    assert _pairs(r) == [("LPN",1),("STNA",2)]

def test_v3_role_x_count():
    r = parse_email("", "9/12 11pm-730am LPN x 1, STNA x 2", 2026)
    assert r.status == "PARSED"
    assert _pairs(r) == [("LPN",1),("STNA",2)]

def test_v3_count_x_role():
    r = parse_email("", "9/12 11pm-730am 1x LPN, 2x STNA", 2026)
    assert r.status == "PARSED"
    assert _pairs(r) == [("LPN",1),("STNA",2)]

def test_v3_bullets():
    body = """Open needs:
- 9/12 (11pm-730am) 1 LPN
- 9/13 (3pm-1130pm) 2 STNAs"""
    r = parse_email("", body, 2026)
    assert r.status == "PARSED"
    assert r.shift_count == 2

def test_v3_office_hours_are_noise():
    body = """Please call before 4pm.
9/12 (11pm-730am) 1 LPN
Office hours are 8am-5pm."""
    r = parse_email("", body, 2026)
    assert r.status == "PARSED"
    assert r.shift_count == 1

def test_v3_overnight_is_valid_not_review():
    r = parse_email("", "9/12 (11pm-730am) 1 LPN", 2026)
    assert r.status == "PARSED"
    assert r.shifts[0].start_time == "23:00:00"
    assert r.shifts[0].end_time == "07:30:00"
    assert r.shifts[0].shift_date == "2026-09-12"

def test_v3_reporting_override():
    body = """9/14 (11pm-730am) 1 LPN.
(3am-730am) 1 LPN-reporting 9/15 at 3am"""
    r = parse_email("", body, 2026)
    assert r.status == "PARSED"
    assert r.shift_count == 2
    assert r.shifts[1].shift_date == "2026-09-15"
    assert r.shifts[1].start_time == "03:00:00"

def test_v3_incomplete_structured_block():
    r = parse_email("", "Date: 9/12\nNeed: 2 LPNs", 2026)
    assert r.status == "NEEDS_REVIEW"
    assert r.shift_count == 0
    assert r.issues

def test_v3_partial_parse_keeps_valid_shift():
    body = """9/12 (11pm-730am) 1 LPN

Date: 9/13
Need: 2 STNAs"""
    r = parse_email("", body, 2026)
    assert r.status == "NEEDS_REVIEW"
    assert r.shift_count == 1
    assert r.shifts[0].skill == "LPN"

def test_v3_unknown_role_not_invented():
    body = "9/12 (11pm-730am) 2 CNAs"
    r = parse_email("", body, 2026)
    assert r.shift_count == 0
    assert all(x.skill in ("LPN","STNA") for x in r.shifts)

def test_v3_source_content_preserved():
    body = "Hello\n\n9/12 (11pm-730am) 1 LPN\nThanks"
    r = parse_email("S", body, 2026)
    assert r.source_content == body

def test_v3_multiple_date_blocks():
    body = """9/12
11pm-730am 1 LPN
3pm-11pm 2 STNAs

9/13
7am-330pm 3 STNAs"""
    r = parse_email("", body, 2026)
    assert r.status == "PARSED"
    assert r.shift_count == 3
    assert [x.shift_date for x in r.shifts] == ["2026-09-12","2026-09-12","2026-09-13"]

def test_v3_24_hour_time():
    r = parse_email("", "9/12 15:00-23:30 1 LPN", 2026)
    assert r.status == "PARSED"
    assert r.shifts[0].start_time == "15:00:00"
    assert r.shifts[0].end_time == "23:30:00"

def test_v3_short_ap():
    r = parse_email("", "9/12 11p-7:30a 1 LPN", 2026)
    assert r.status == "PARSED"
    assert r.shifts[0].start_time == "23:00:00"
    assert r.shifts[0].end_time == "07:30:00"

def test_v3_full_year_numeric():
    r = parse_email("", "9/12/2026 11pm-730am 1 LPN", 2026)
    assert r.status == "PARSED"
    assert r.shifts[0].shift_date == "2026-09-12"

def test_v3_dash_date():
    r = parse_email("", "9-12-2026 11pm-730am 1 LPN", 2026)
    assert r.status == "PARSED"
    assert r.shifts[0].shift_date == "2026-09-12"
