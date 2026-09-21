from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import Iterable

from .models import ParsedShift, ParseResult
from .time_parser import parse_time_token, TimeParseError

# ---------------------------
# Date recognition
# ---------------------------

NUM_DATE_RE = re.compile(
    r"(?<!\d)(?P<m>\d{1,2})[/-](?P<d>\d{1,2})(?:[/-](?P<y>\d{2,4}))?(?!\d)"
)

MONTHS = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4,
    "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}

MONTH_NAMES = "|".join(sorted(MONTHS, key=len, reverse=True))
NAME_DATE_RE = re.compile(
    rf"\b(?P<mon>{MONTH_NAMES})\.?\s+(?P<d>\d{{1,2}})(?:st|nd|rd|th)?(?:,\s*|\s+)?(?P<y>\d{{4}})?\b",
    re.I,
)

# ---------------------------
# Time range recognition
# ---------------------------

TIME_TOKEN = r"(?:\d{1,2}:\d{2}|\d{3,4}|\d{1,2})\s*(?:a\.?m\.?|p\.?m\.?|a|p)?"

# Handles:
# 11pm-730am
# 11pm to 7:30am
# from 11pm to 7:30am
# 11pm until 7:30am
TIME_RANGE_RE = re.compile(
    rf"(?:\bfrom\s+)?(?P<start>{TIME_TOKEN})\s*(?:[-–—]|\bto\b|\buntil\b|\bthrough\b)\s*(?P<end>{TIME_TOKEN})",
    re.I,
)

# ---------------------------
# Role/headcount recognition
# ---------------------------

COUNT_ROLE_RE = re.compile(
    r"(?P<count>\d+)\s*(?:x\s*)?(?P<role>LPNs?|STNAs?)\b",
    re.I,
)

ROLE_COUNT_RE = re.compile(
    r"\b(?P<role>LPNs?|STNAs?)\s*(?:x|:|=)?\s*(?P<count>\d+)\b",
    re.I,
)

ROLE_WORD_RE = re.compile(r"\b(?:LPNs?|STNAs?)\b", re.I)

# Already-normalized/downstream-like input:
# 2026-09-12 | 15:00:00 → 23:30:00 | LPN | 1
NORMALIZED_PIPE_RE = re.compile(
    r"^\s*(?P<date>\d{4}-\d{2}-\d{2})\s*\|\s*"
    r"(?P<start>\d{1,2}:\d{2}(?::\d{2})?)\s*(?:→|->|[-–—])\s*"
    r"(?P<end>\d{1,2}:\d{2}(?::\d{2})?)\s*\|\s*"
    r"(?P<role>LPN|STNA)s?\s*\|\s*(?P<count>\d+)\s*$",
    re.I,
)
EXPLICIT_LABEL_RE = re.compile(r"^\s*(?:date|shift|time|need|needs|requirement|requirements|coverage)\s*:", re.I)

REPORTING_RE = re.compile(
    rf"\breporting\s+(?P<date>(?:\d{{1,2}}[/-]\d{{1,2}}(?:[/-]\d{{2,4}})?|(?:{MONTH_NAMES})\.?\s+\d{{1,2}}(?:st|nd|rd|th)?(?:,\s*\d{{4}})?))\s+at\s+(?P<time>{TIME_TOKEN})",
    re.I,
)

@dataclass(frozen=True)
class DateHit:
    start: int
    end: int
    value: date
    text: str

@dataclass(frozen=True)
class RoleHit:
    start: int
    end: int
    skill: str
    count: int
    text: str

@dataclass
class PendingBlock:
    shift_date: date | None = None
    start_time: str | None = None
    end_time: str | None = None
    roles: list[RoleHit] | None = None
    source_lines: list[str] | None = None

    def __post_init__(self):
        if self.roles is None:
            self.roles = []
        if self.source_lines is None:
            self.source_lines = []

    def clear_after_emit(self, keep_date: bool = True):
        d = self.shift_date if keep_date else None
        self.shift_date = d
        self.start_time = None
        self.end_time = None
        self.roles = []
        self.source_lines = []

    def has_any_structured_component(self) -> bool:
        return bool(self.shift_date or self.start_time or self.end_time or self.roles)

def _normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\u2013", "-").replace("\u2014", "-").replace("\xa0", " ")
    return "\n".join(line.rstrip() for line in text.splitlines())

def _normalize_skill(raw: str) -> str:
    return "LPN" if raw.upper().startswith("LPN") else "STNA"

def _year_value(raw: str | None, default_year: int) -> int:
    if not raw:
        return default_year
    y = int(raw)
    return y + 2000 if y < 100 else y

def _date_from_numeric(m: re.Match, default_year: int) -> date:
    return date(
        _year_value(m.group("y"), default_year),
        int(m.group("m")),
        int(m.group("d")),
    )

def _date_from_name(m: re.Match, default_year: int) -> date:
    mon = MONTHS[m.group("mon").lower().rstrip(".")]
    return date(
        _year_value(m.group("y"), default_year),
        mon,
        int(m.group("d")),
    )

def find_dates(text: str, default_year: int) -> list[DateHit]:
    hits: list[DateHit] = []
    for m in NUM_DATE_RE.finditer(text):
        try:
            hits.append(DateHit(m.start(), m.end(), _date_from_numeric(m, default_year), m.group(0)))
        except ValueError:
            pass
    for m in NAME_DATE_RE.finditer(text):
        try:
            hits.append(DateHit(m.start(), m.end(), _date_from_name(m, default_year), m.group(0)))
        except ValueError:
            pass
    hits.sort(key=lambda x: x.start)
    return hits

def parse_date_text(text: str, default_year: int) -> date | None:
    hits = find_dates(text, default_year)
    return hits[0].value if hits else None

def extract_roles(text: str) -> list[RoleHit]:
    hits: list[RoleHit] = []
    occupied: list[tuple[int, int]] = []

    def overlaps(a: int, b: int) -> bool:
        return any(not (b <= x or a >= y) for x, y in occupied)

    for rx in (COUNT_ROLE_RE, ROLE_COUNT_RE):
        for m in rx.finditer(text):
            if overlaps(m.start(), m.end()):
                continue
            count = int(m.group("count"))
            if count <= 0:
                continue
            hits.append(
                RoleHit(
                    m.start(), m.end(),
                    _normalize_skill(m.group("role")),
                    count,
                    m.group(0),
                )
            )
            occupied.append((m.start(), m.end()))
    hits.sort(key=lambda h: h.start)
    return hits

def _nearest_date_before(hits: list[DateHit], pos: int, carry_date: date | None) -> date | None:
    prior = [h for h in hits if h.start < pos]
    if prior:
        return prior[-1].value
    if hits:
        # For natural language such as:
        # "Need 1 LPN from 11pm to 7:30am on 9/12"
        return hits[0].value
    return carry_date

def _parse_range_match(tm: re.Match) -> tuple[str, str]:
    start = parse_time_token(tm.group("start")).db_time()
    end = parse_time_token(tm.group("end")).db_time()
    return start, end

def _reporting_override(segment: str, default_year: int) -> tuple[date, str] | None:
    m = REPORTING_RE.search(segment)
    if not m:
        return None
    d = parse_date_text(m.group("date"), default_year)
    if d is None:
        return None
    t = parse_time_token(m.group("time")).db_time()
    return d, t

def _looks_like_component_line(line: str, default_year: int) -> bool:
    stripped = line.strip(" \t-*•")
    if not stripped:
        return False
    if EXPLICIT_LABEL_RE.search(stripped):
        return True

    dates = find_dates(stripped, default_year)
    ranges = list(TIME_RANGE_RE.finditer(stripped))
    roles = extract_roles(stripped)

    # Pure structured fragments used in multi-line emails.
    if dates and len(stripped) <= 35:
        return True
    if ranges and len(stripped) <= 45:
        return True
    if roles and len(stripped) <= 55:
        return True
    return False

def _emit(
    shifts: list[ParsedShift],
    d: date,
    start_time: str,
    end_time: str,
    roles: Iterable[RoleHit],
    source_text: str,
):
    for role in roles:
        shifts.append(
            ParsedShift(
                shift_date=d.isoformat(),
                start_time=start_time,
                end_time=end_time,
                skill=role.skill,
                required_count=role.count,
                status="OPEN",
                source_text=source_text.strip(),
            )
        )


def _parse_normalized_pipe_line(line: str) -> ParsedShift | None:
    m = NORMALIZED_PIPE_RE.match(line)
    if not m:
        return None

    d = date.fromisoformat(m.group("date"))
    start = parse_time_token(m.group("start")).db_time()
    end = parse_time_token(m.group("end")).db_time()
    count = int(m.group("count"))
    if count <= 0:
        return None

    return ParsedShift(
        shift_date=d.isoformat(),
        start_time=start,
        end_time=end,
        skill=_normalize_skill(m.group("role")),
        required_count=count,
        status="OPEN",
        source_text=line.strip(),
    )

def _parse_direct_line(
    line: str,
    carry_date: date | None,
    default_year: int,
) -> tuple[list[ParsedShift], date | None, list[str]]:
    """
    Parses a line that contains enough information by itself.
    It deliberately ignores prose that merely mentions LPN/STNA.
    """
    shifts: list[ParsedShift] = []
    issues: list[str] = []

    dates = find_dates(line, default_year)
    if dates:
        carry_date = dates[0].value

    ranges = list(TIME_RANGE_RE.finditer(line))
    if not ranges:
        return shifts, carry_date, issues

    all_roles = extract_roles(line)
    if not all_roles:
        # A time range without role/headcount may be office hours, signature text, etc.
        # Do not treat it as staffing unless a structured block later ties roles to it.
        return shifts, carry_date, issues

    # One time range: roles can appear before OR after the range.
    if len(ranges) == 1:
        tm = ranges[0]
        d = _nearest_date_before(dates, tm.start(), carry_date)
        if d is None:
            issues.append(f"Could not determine date for staffing line: {line}")
            return shifts, carry_date, issues

        try:
            start, end = _parse_range_match(tm)
        except TimeParseError as exc:
            issues.append(str(exc))
            return shifts, carry_date, issues

        override = _reporting_override(line, default_year)
        if override:
            d, start = override

        _emit(shifts, d, start, end, all_roles, line)
        return shifts, carry_date, issues

    # Multiple ranges: use a segment around each range so each range gets its own roles.
    # This directly handles the observed OVH style:
    # 9/14 (3pm-1130pm) 1 LPN. (7pm-1130pm) 1 LPN
    for idx, tm in enumerate(ranges):
        seg_start = tm.start()
        seg_end = ranges[idx + 1].start() if idx + 1 < len(ranges) else len(line)
        segment = line[seg_start:seg_end].strip(" .;,|-")

        roles = extract_roles(segment)

        # If no role appears after the range, allow roles immediately before it
        # within the nearest sentence/semicolon fragment.
        if not roles:
            prev_boundary = max(
                line.rfind(".", 0, tm.start()),
                line.rfind(";", 0, tm.start()),
                line.rfind("|", 0, tm.start()),
            )
            local = line[prev_boundary + 1:seg_end]
            roles = extract_roles(local)

        if not roles:
            continue

        d = _nearest_date_before(dates, tm.start(), carry_date)
        if d is None:
            issues.append(f"Could not determine date for segment: {segment}")
            continue

        try:
            start, end = _parse_range_match(tm)
        except TimeParseError as exc:
            issues.append(str(exc))
            continue

        override = _reporting_override(segment, default_year)
        if override:
            d, start = override

        _emit(shifts, d, start, end, roles, line)

    return shifts, carry_date, issues

def parse_email(subject: str, body: str, default_year: int = 2026) -> ParseResult:
    """
    Robust deterministic parser designed around the backend team's JSON contract.

    Strategy:
      1. Ignore ordinary prose/signatures.
      2. Parse self-contained staffing sentences/lines.
      3. Maintain a small state machine for labeled or split multi-line fields.
      4. Preserve source text for auditability.
      5. If structured staffing content is incomplete, surface NEEDS_REVIEW.
    """
    cleaned = _normalize_text(body)
    shifts: list[ParsedShift] = []
    issues: list[str] = []
    carry_date: date | None = None
    pending = PendingBlock()

    def flush_incomplete(reason: str):
        nonlocal pending
        # Only flag something that looks like an actual structured staffing block.
        if pending.roles and (pending.shift_date or pending.start_time or pending.end_time):
            issues.append(reason + ": " + " | ".join(pending.source_lines))
        pending = PendingBlock(shift_date=carry_date)

    lines = cleaned.splitlines()

    for line_no, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()

        if not line:
            # Paragraph break. If we have an incomplete structured block, flag it.
            if pending.source_lines and pending.has_any_structured_component():
                if pending.shift_date and pending.start_time and pending.end_time and pending.roles:
                    source = "\n".join(pending.source_lines)
                    _emit(
                        shifts, pending.shift_date,
                        pending.start_time, pending.end_time,
                        pending.roles, source,
                    )
                    pending.clear_after_emit(keep_date=True)
                elif pending.roles:
                    flush_incomplete(f"Line {line_no}: incomplete staffing block")
            continue

        # First accept an already-normalized pipe-separated shift line.
        normalized = _parse_normalized_pipe_line(line)
        if normalized is not None:
            shifts.append(normalized)
            carry_date = date.fromisoformat(normalized.shift_date)
            pending = PendingBlock(shift_date=carry_date)
            continue

        # Then try a complete human-readable line/sentence.
        direct, new_carry, line_issues = _parse_direct_line(line, carry_date, default_year)
        carry_date = new_carry
        if direct:
            # If a prior multi-line block is already complete, persist it before
            # handling this independent complete line.
            if (
                pending.source_lines
                and pending.shift_date
                and pending.start_time
                and pending.end_time
                and pending.roles
            ):
                _emit(
                    shifts,
                    pending.shift_date,
                    pending.start_time,
                    pending.end_time,
                    pending.roles,
                    "\n".join(pending.source_lines),
                )
            pending = PendingBlock(shift_date=carry_date)

            shifts.extend(direct)
            issues.extend(f"Line {line_no}: {x}" for x in line_issues)
            continue
        issues.extend(f"Line {line_no}: {x}" for x in line_issues)

        # Ordinary descriptive prose is ignored, even if it says "LPN" or "STNA".
        # It only becomes a block component if it has count-role pairs, date/time
        # structure, or an explicit Date:/Shift:/Need: label.
        component_line = _looks_like_component_line(line, default_year)
        if not component_line:
            continue

        dates = find_dates(line, default_year)
        ranges = list(TIME_RANGE_RE.finditer(line))
        roles = extract_roles(line)

        # If the previous multi-line block is already complete:
        # - another role-only line belongs to the SAME shift and should be added;
        # - a new date/time component begins a NEW shift block, so flush first.
        pending_complete = bool(
            pending.shift_date
            and pending.start_time
            and pending.end_time
            and pending.roles
        )
        role_only_component = bool(roles and not dates and not ranges)

        if pending_complete and role_only_component:
            pending.roles.extend(roles)
            pending.source_lines.append(line)
            continue

        if pending_complete and (dates or ranges):
            _emit(
                shifts,
                pending.shift_date,
                pending.start_time,
                pending.end_time,
                pending.roles,
                "\n".join(pending.source_lines),
            )
            pending.clear_after_emit(keep_date=True)

        # Start or update the pending block.
        if dates:
            new_date = dates[0].value
            # If a different date arrives while a role-bearing block is incomplete,
            # don't silently merge two staffing blocks.
            if (
                pending.roles
                and pending.shift_date
                and new_date != pending.shift_date
                and not (pending.start_time and pending.end_time)
            ):
                flush_incomplete(f"Line {line_no}: new date encountered before prior block completed")
            carry_date = new_date
            pending.shift_date = new_date

        if ranges:
            # Multi-line block should generally carry one time range.
            tm = ranges[0]
            try:
                pending.start_time, pending.end_time = _parse_range_match(tm)
            except TimeParseError as exc:
                issues.append(f"Line {line_no}: {exc}")

        if roles:
            if pending.roles:
                pending.roles.extend(roles)
            else:
                pending.roles = roles

        pending.source_lines.append(line)

        # Reporting phrase can override pending date/start.
        override = _reporting_override(line, default_year)
        if override:
            pending.shift_date, pending.start_time = override
            carry_date = pending.shift_date


    # End-of-email flush.
    if pending.source_lines and pending.has_any_structured_component():
        if (
            pending.shift_date
            and pending.start_time
            and pending.end_time
            and pending.roles
        ):
            _emit(
                shifts,
                pending.shift_date,
                pending.start_time,
                pending.end_time,
                pending.roles,
                "\n".join(pending.source_lines),
            )
        elif pending.roles:
            issues.append(
                "End of email: incomplete staffing block: "
                + " | ".join(pending.source_lines)
            )

    status = "PARSED" if not issues else "NEEDS_REVIEW"

    return ParseResult(
        subject=subject,
        source_content=body,
        status=status,
        shift_count=len(shifts),
        shifts=shifts,
        issues=issues,
    )
