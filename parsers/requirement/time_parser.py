import re
from dataclasses import dataclass

class TimeParseError(ValueError):
    pass

@dataclass(frozen=True)
class ParsedTime:
    hour: int
    minute: int

    def db_time(self) -> str:
        return f"{self.hour:02d}:{self.minute:02d}:00"

def parse_time_token(token: str) -> ParsedTime:
    """
    Supported examples:
      3pm, 3 PM, 3:00 PM, 15:00
      330pm, 3:30pm, 03:30 PM
      730am, 7:30am, 07:30 AM
      1130pm, 11:30pm
      11p, 7:30a
    """
    raw = token.strip().lower().strip(".,;!?")
    raw = raw.replace("a.m.", "am").replace("p.m.", "pm")
    raw = raw.replace("a.m", "am").replace("p.m", "pm")
    raw = re.sub(r"\s+", "", raw)

    m = re.fullmatch(r"(?P<num>\d{1,4}(?::\d{2}(?::\d{2})?)?)(?P<suffix>am|pm|a|p)?", raw)
    if not m:
        raise TimeParseError(f"Unsupported time token: {token!r}")

    num = m.group("num")
    suffix = m.group("suffix")

    if ":" in num:
        parts = num.split(":")
        hour = int(parts[0])
        minute = int(parts[1])
        if len(parts) == 3 and int(parts[2]) != 0:
            raise TimeParseError(f"Seconds must be 00 for shift times: {token!r}")
    elif len(num) <= 2:
        hour, minute = int(num), 0
    elif len(num) == 3:
        hour, minute = int(num[0]), int(num[1:])
    elif len(num) == 4:
        hour, minute = int(num[:2]), int(num[2:])
    else:
        raise TimeParseError(f"Unsupported compact time: {token!r}")

    if not 0 <= minute <= 59:
        raise TimeParseError(f"Invalid minute: {token!r}")

    if suffix:
        if not 1 <= hour <= 12:
            raise TimeParseError(f"Invalid 12-hour time: {token!r}")
        if suffix in ("pm", "p") and hour != 12:
            hour += 12
        elif suffix in ("am", "a") and hour == 12:
            hour = 0
    elif not 0 <= hour <= 23:
        raise TimeParseError(f"Invalid 24-hour time: {token!r}")

    return ParsedTime(hour, minute)
