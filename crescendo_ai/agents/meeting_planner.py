from crescendo_ai.storage.models import Meeting


class MeetingPlannerAgent:
    """Decides when a meeting is needed, who should attend, and drafts the agenda."""

    def __init__(self, llm_client, store, confidence_threshold: float = 0.6):
        self._llm = llm_client
        self._store = store
        self._threshold = confidence_threshold

    def find_proposal(self, monitor, channel: str) -> dict | None:
        candidates = [
            (thread, monitor.confidence(thread)) for thread in monitor.open_topics(channel)
        ]
        candidates = [c for c in candidates if c[1] >= self._threshold]
        if not candidates:
            return None
        candidates.sort(key=lambda pair: pair[1], reverse=True)
        threads = [c[0] for c in candidates]
        participants = sorted({user for t in threads for user in t.participants})
        return {
            "channel": channel,
            "topics": [t.label for t in threads],
            "participants": participants,
            "confidence": candidates[0][1],
            "evidence": self._summarize_evidence(threads),
        }

    def _summarize_evidence(self, threads) -> str:
        return "\n".join(f"- {t.label}: mentioned {t.mentions} times, unresolved" for t in threads)

    def generate_agenda(self, proposal: dict) -> Meeting:
        system = (
            "You are an executive-board meeting planner for a student music "
            "organization. Given unresolved discussion topics, produce a focused "
            "meeting agenda as strict JSON with keys: title (string), "
            "estimated_length_minutes (int), agenda (array of short strings), "
            "expected_outcomes (array of short strings)."
        )
        user = (
            f"Topics needing resolution:\n{proposal['evidence']}\n\n"
            f"Participants who have been discussing this: {', '.join(proposal['participants']) or 'unknown'}"
        )
        result = self._llm.complete_json(system, user)
        meeting = Meeting(
            id=self._store.new_id(),
            channel=proposal["channel"],
            title=result.get("title", "Executive Board Planning Meeting"),
            status="planned",
            estimated_length_minutes=result.get("estimated_length_minutes", 25),
            agenda=result.get("agenda") or proposal["topics"],
            expected_outcomes=result.get("expected_outcomes", []),
            attendees=proposal["participants"],
        )
        self._store.save_meeting(meeting)
        return meeting
