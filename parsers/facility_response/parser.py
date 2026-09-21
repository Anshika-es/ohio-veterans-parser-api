import re
from typing import Optional
from .models import FacilityDecision, ParseResult
from .lexicon import PHRASE_GROUPS

REQ_ID_RE = re.compile(
    r"\b(?:availability[_ -]?request(?:[_ -]?id)?|request[_ -]?id|ar)\s*[:#-]?\s*([A-Za-z0-9_-]+)\b",
    re.I,
)
SHIFT_RE = re.compile(
    r"\b(?:shift\s*[:#-]?\s*)?"
    r"(?:(\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?)\s+)?"
    r"(\d{1,2}(?::?\d{2})?\s*(?:am|pm|a|p))\s*(?:-|–|—|to)\s*"
    r"(\d{1,2}(?::?\d{2})?\s*(?:am|pm|a|p))\b",
    re.I,
)
NAME_PREFIX_RE = re.compile(
    r"^\s*(?:[-*•]\s*)?(?:candidate|clinician)?\s*"
    r"([A-Z][A-Za-z'.-]+(?:\s+[A-Z][A-Za-z'.-]+){1,3})\s*(?:[-–—:|,])"
)

def _phrase_regex(phrase: str):
    escaped = re.escape(phrase).replace(r"\ ", r"\s+")
    return re.compile(rf"(?<![A-Za-z0-9]){escaped}(?![A-Za-z0-9])", re.I)

_COMPILED = [
    (decision, phrase, _phrase_regex(phrase))
    for decision, phrases in PHRASE_GROUPS
    for phrase in sorted(phrases, key=len, reverse=True)
]

def detect_decision(text: str):
    for decision, phrase, rx in _COMPILED:
        if rx.search(text):
            return decision, phrase
    return None, None

def _extract_request_id(text: str):
    m = REQ_ID_RE.search(text)
    return m.group(1) if m else None

def _extract_shift(text: str):
    m = SHIFT_RE.search(text)
    if not m:
        return None
    date_part, start, end = m.groups()
    start = re.sub(r"\s+", "", start.lower())
    end = re.sub(r"\s+", "", end.lower())
    return f"{date_part + ' ' if date_part else ''}{start}-{end}"

def _extract_candidate_name(text: str):
    m = NAME_PREFIX_RE.search(text)
    return m.group(1).strip() if m else None

def _lines(body: str):
    out = []
    for raw in (body or "").splitlines():
        raw = raw.strip()
        if not raw:
            continue
        out.extend([x.strip() for x in re.split(r"\s*;\s*", raw) if x.strip()])
    return out

def parse_facility_response(subject: str, body: str, *,
                            availability_request_id: Optional[str] = None,
                            selected_shift: Optional[str] = None) -> ParseResult:
    subject = subject or ""
    body = body or ""
    decisions = []
    issues = []

    for line in _lines(body):
        decision, keyword = detect_decision(line)
        if not decision:
            continue

        req_id = _extract_request_id(line) or availability_request_id
        shift = _extract_shift(line) or selected_shift
        candidate = _extract_candidate_name(line)

        normalized = decision
        confidence = "HIGH"
        if not req_id:
            normalized = "NEEDS_REVIEW"
            confidence = "LOW"
            issues.append(f"Decision recognized but availability_request_id is missing: {line}")

        decisions.append(FacilityDecision(
            response=normalized,
            source_text=line,
            matched_keyword=keyword,
            availability_request_id=req_id,
            selected_shift=shift,
            candidate_name=candidate,
            confidence=confidence,
        ))

    if not decisions:
        combined = f"{subject}\n{body}".strip()
        decision, keyword = detect_decision(combined)
        if decision:
            req_id = availability_request_id or _extract_request_id(combined)
            shift = selected_shift or _extract_shift(combined)
            if req_id:
                decisions.append(FacilityDecision(
                    response=decision,
                    source_text=body.strip() or subject.strip(),
                    matched_keyword=keyword,
                    availability_request_id=req_id,
                    selected_shift=shift,
                ))
            else:
                decisions.append(FacilityDecision(
                    response="NEEDS_REVIEW",
                    source_text=body.strip() or subject.strip(),
                    matched_keyword=keyword,
                    selected_shift=shift,
                    confidence="LOW",
                ))
                issues.append("Facility decision recognized, but availability_request_id is missing.")

    if not decisions:
        issues.append("No supported facility approval/confirmation statement found.")
        status = "NEEDS_REVIEW"
    elif any(d.response == "NEEDS_REVIEW" for d in decisions):
        status = "NEEDS_REVIEW"
    else:
        status = "PARSED"

    return ParseResult(
        subject=subject,
        source_content=body,
        status=status,
        decision_count=len(decisions),
        decisions=decisions,
        issues=issues,
    )
