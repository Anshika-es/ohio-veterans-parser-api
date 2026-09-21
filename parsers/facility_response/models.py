from dataclasses import dataclass, asdict
from typing import Optional, List

@dataclass
class FacilityDecision:
    response: str
    source_text: str
    matched_keyword: Optional[str] = None
    availability_request_id: Optional[str] = None
    selected_shift: Optional[str] = None
    candidate_name: Optional[str] = None
    confidence: str = "HIGH"

    def to_dict(self):
        return asdict(self)

@dataclass
class ParseResult:
    subject: str
    source_content: str
    status: str
    decision_count: int
    decisions: List[FacilityDecision]
    issues: List[str]

    def to_dict(self):
        return {
            "subject": self.subject,
            "source_content": self.source_content,
            "status": self.status,
            "decision_count": self.decision_count,
            "decisions": [d.to_dict() for d in self.decisions],
            "issues": self.issues,
        }
