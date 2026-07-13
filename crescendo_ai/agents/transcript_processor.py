from crescendo_ai.storage.models import Meeting


class TranscriptProcessorAgent:
    """Extracts decisions, owners, deadlines, and risks from a meeting transcript."""

    def __init__(self, llm_client, store):
        self._llm = llm_client
        self._store = store

    def process(
        self,
        transcript: str,
        meeting_id: str | None = None,
        channel: str = "",
        attendees: list | None = None,
    ) -> Meeting:
        system = (
            "You process executive board meeting transcripts for a student music "
            "organization. Return strict JSON with keys: title (string), "
            "summary (string), decisions (array of strings), "
            "action_items (array of objects with owner, task, deadline), "
            "open_questions (array of strings), risks (array of strings), "
            "next_meeting_recommendation (string)."
        )
        result = self._llm.complete_json(system, transcript)

        meeting = self._store.get_meeting(meeting_id) if meeting_id else None
        if meeting is None:
            meeting = Meeting(
                id=meeting_id or self._store.new_id(),
                channel=channel,
                title=result.get("title", "Executive Board Meeting"),
                status="completed",
            )

        meeting.status = "completed"
        meeting.transcript = transcript
        meeting.attendees = attendees or meeting.attendees
        meeting.title = result.get("title", meeting.title)
        meeting.summary = result.get("summary", "")
        meeting.decisions = result.get("decisions", [])
        meeting.action_items = result.get("action_items", [])
        meeting.open_questions = result.get("open_questions", [])
        meeting.risks = result.get("risks", [])
        meeting.next_meeting_recommendation = result.get("next_meeting_recommendation", "")

        self._store.save_meeting(meeting)
        return meeting
