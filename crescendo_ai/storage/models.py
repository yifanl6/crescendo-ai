from dataclasses import asdict, dataclass, field
from typing import Optional


@dataclass
class Meeting:
    id: str
    channel: str
    title: str
    status: str  # "planned" | "completed"
    estimated_length_minutes: Optional[int] = None
    agenda: list = field(default_factory=list)
    expected_outcomes: list = field(default_factory=list)
    attendees: list = field(default_factory=list)
    summary: str = ""
    decisions: list = field(default_factory=list)
    action_items: list = field(default_factory=list)  # [{owner, task, deadline}]
    open_questions: list = field(default_factory=list)
    risks: list = field(default_factory=list)
    next_meeting_recommendation: str = ""
    transcript: str = ""
    created_at: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Meeting":
        known = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        return cls(**known)
