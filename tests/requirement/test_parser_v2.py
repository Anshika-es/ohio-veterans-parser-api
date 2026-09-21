from parsers.requirement import parse_email
from parsers.requirement import parse_staffing_email

def pairs(r):
    return [(s.skill, s.required_count) for s in r.shifts]

def test_observed_mixed_roles():
    r = parse_email("", "9/12 (11pm-730am) 1 LPN, 2 STNAs", 2026)
    assert r.status == "PARSED"
    assert r.shift_count == 2
    assert pairs(r) == [("LPN",1),("STNA",2)]

def test_multiple_ranges_same_line():
    r = parse_email("", "9/14 (3pm-1130pm) 1 LPN. (7pm-1130pm) 1 LPN", 2026)
    assert r.status == "PARSED"
    assert r.shift_count == 2
    assert [x.start_time for x in r.shifts] == ["15:00:00","19:00:00"]

def test_compact_times():
    r = parse_email("", "9/11 (7am-330pm) 2 STNAs. (7am-1130am) 2 STNAs", 2026)
    assert [x.end_time for x in r.shifts] == ["15:30:00","11:30:00"]

def test_reporting_override():
    r = parse_email("", "9/14 (11pm-730am) 1 LPN.\n(3am-730am) 1 LPN-reporting 9/15 at 3am", 2026)
    assert r.shift_count == 2
    assert r.shifts[1].shift_date == "2026-09-15"
    assert r.shifts[1].start_time == "03:00:00"

def test_paragraph_noise_ignored():
    body = """Good morning team,

Please review the staffing needs below.
We appreciate your continued support.

9/12 (11pm-730am) 1 LPN, 2 STNAs

Please confirm if anyone is available.
Thank you."""
    r = parse_email("", body, 2026)
    assert r.status == "PARSED"
    assert r.shift_count == 2

def test_descriptive_paragraph_mentions_roles_without_false_warning():
    body = """Good morning Kelly,

We are reviewing LPN and STNA coverage for the upcoming weekend.
Please see the current open needs below.

9/12 (11pm-730am) 1 LPN, 2 STNAs

Thank you."""
    r = parse_email("", body, 2026)
    assert r.status == "PARSED"
    assert r.shift_count == 2
    assert r.issues == []

def test_labeled_multiline_fields():
    body = """Date: 9/12
Shift: 11pm-730am
Need: 1 LPN, 2 STNAs"""
    r = parse_email("", body, 2026)
    assert r.status == "PARSED"
    assert r.shift_count == 2
    assert pairs(r) == [("LPN",1),("STNA",2)]

def test_fully_split_multiline_fields():
    body = """9/12
11pm-730am
1 LPN
2 STNAs"""
    r = parse_email("", body, 2026)
    assert r.status == "PARSED"
    assert r.shift_count == 2

def test_natural_language_from_to():
    body = "For 9/12, we need 1 LPN and 2 STNAs from 11pm to 7:30am."
    r = parse_email("", body, 2026)
    assert r.status == "PARSED"
    assert r.shift_count == 2
    assert r.shifts[0].start_time == "23:00:00"
    assert r.shifts[0].end_time == "07:30:00"

def test_natural_language_until():
    body = "For 9/12, 1 LPN and 2 STNAs are needed from 11pm until 7:30am."
    r = parse_email("", body, 2026)
    assert r.status == "PARSED"
    assert r.shift_count == 2

def test_unrelated_times_do_not_create_shifts():
    body = """Please call me before 4pm.

9/12 (11pm-730am) 1 LPN

Office hours are 8am-5pm."""
    r = parse_email("", body, 2026)
    assert r.status == "PARSED"
    assert r.shift_count == 1
    assert r.shifts[0].skill == "LPN"

def test_month_name_date():
    body = "September 12, 2026 from 11pm to 7:30am - need 1 LPN and 2 STNAs."
    r = parse_email("", body, 2026)
    assert r.status == "PARSED"
    assert r.shift_count == 2
    assert all(x.shift_date == "2026-09-12" for x in r.shifts)

def test_short_month_name_date():
    body = "Sep 12 from 3pm to 11:30pm: 1 LPN"
    r = parse_email("", body, 2026)
    assert r.status == "PARSED"
    assert r.shift_count == 1
    assert r.shifts[0].shift_date == "2026-09-12"

def test_date_with_dash():
    body = "9-12-2026 (11pm-730am) 1 LPN"
    r = parse_email("", body, 2026)
    assert r.status == "PARSED"
    assert r.shift_count == 1

def test_role_colon_count():
    body = "9/12 from 11pm to 7:30am Need: LPN: 1, STNA: 2"
    r = parse_email("", body, 2026)
    assert r.status == "PARSED"
    assert pairs(r) == [("LPN",1),("STNA",2)]

def test_role_x_count():
    body = "9/12 11pm-730am LPN x 1, STNA x 2"
    r = parse_email("", body, 2026)
    assert r.status == "PARSED"
    assert pairs(r) == [("LPN",1),("STNA",2)]

def test_count_x_role():
    body = "9/12 11pm-730am 1x LPN, 2x STNA"
    r = parse_email("", body, 2026)
    assert r.status == "PARSED"
    assert pairs(r) == [("LPN",1),("STNA",2)]

def test_bullet_lines():
    body = """Open needs:
- 9/12 (11pm-730am) 1 LPN
- 9/13 (3pm-1130pm) 2 STNAs"""
    r = parse_email("", body, 2026)
    assert r.status == "PARSED"
    assert r.shift_count == 2

def test_date_line_then_two_shift_blocks():
    body = """9/12
11pm-730am 1 LPN
3pm-11pm 2 STNAs"""
    r = parse_email("", body, 2026)
    assert r.status == "PARSED"
    assert r.shift_count == 2
    assert all(x.shift_date == "2026-09-12" for x in r.shifts)

def test_incomplete_staffing_block_needs_review():
    body = """Date: 9/12
Need: 2 LPNs"""
    r = parse_email("", body, 2026)
    assert r.status == "NEEDS_REVIEW"
    assert r.shift_count == 0
    assert r.issues

def test_random_role_words_without_counts_are_ignored():
    body = """Our LPN and STNA teams are doing great.
Please call before 4pm.
Thank you."""
    r = parse_email("", body, 2026)
    assert r.status == "PARSED"
    assert r.shift_count == 0
    assert r.issues == []

def test_source_content_exactly_preserved():
    body = "Hello\n\n9/12 (11pm-730am) 1 LPN"
    r = parse_email("x", body, 2026)
    assert r.source_content == body

def test_adapter_returns_backend_shape():
    out = parse_staffing_email(
        subject="OVH",
        body="9/12 (11pm-730am) 1 LPN, 2 STNAs",
        default_year=2026,
    )
    assert set(out) == {"subject","source_content","status","shift_count","shifts","issues"}
    assert set(out["shifts"][0]) == {
        "shift_date","start_time","end_time","skill","required_count","status","source_text"
    }

def test_observed_large_block():
    body = """9/11 (7am-330pm) 2 STNAs. (7am-1130am) 2 STNAs
9/11 (7pm-1130pm) 2 STNAs

9/12 (7pm-1130pm) 2 STNAs
9/12 (11pm-730am) 1 LPN, 2 STNAs

9/13 (3pm-1130pm) 4 STNAs. (7pm-1130pm) 2 STNAs
9/13 (11pm-730am) 6 LPNs"""
    r = parse_email("", body, 2026)
    assert r.status == "PARSED"
    assert r.shift_count == 9
