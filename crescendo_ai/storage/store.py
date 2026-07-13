import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from crescendo_ai.storage.models import Meeting


class JSONStore:
    """Simple file-based persistence for the hackathon MVP.

    Swappable behind the same interface (save_meeting/get_meeting/list_meetings/
    search_meetings) if this later moves to a real database.
    """

    def __init__(self, data_dir: Path):
        self.meetings_dir = Path(data_dir) / "meetings"
        self.meetings_dir.mkdir(parents=True, exist_ok=True)

    def new_id(self) -> str:
        return uuid.uuid4().hex[:12]

    def save_meeting(self, meeting: Meeting) -> Meeting:
        if not meeting.created_at:
            meeting.created_at = datetime.now(timezone.utc).isoformat()
        path = self.meetings_dir / f"{meeting.id}.json"
        path.write_text(json.dumps(meeting.to_dict(), indent=2))
        return meeting

    def get_meeting(self, meeting_id: str) -> Optional[Meeting]:
        path = self.meetings_dir / f"{meeting_id}.json"
        if not path.exists():
            return None
        return Meeting.from_dict(json.loads(path.read_text()))

    def list_meetings(self) -> list:
        meetings = [
            Meeting.from_dict(json.loads(p.read_text()))
            for p in self.meetings_dir.glob("*.json")
        ]
        return sorted(meetings, key=lambda m: m.created_at, reverse=True)

    def search_meetings(self, query: str, top_k: int = 5) -> list:
        terms = [t.lower() for t in query.split() if len(t) > 2]
        if not terms:
            return []
        scored = []
        for meeting in self.list_meetings():
            haystack = " ".join(
                [
                    meeting.title,
                    meeting.summary,
                    meeting.next_meeting_recommendation,
                    " ".join(meeting.decisions),
                    " ".join(meeting.open_questions),
                    " ".join(meeting.risks),
                    " ".join(a.get("task", "") for a in meeting.action_items),
                ]
            ).lower()
            score = sum(haystack.count(term) for term in terms)
            if score > 0:
                scored.append((score, meeting))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [meeting for _, meeting in scored[:top_k]]
