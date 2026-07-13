from crescendo_ai.agents.transcript_processor import TranscriptProcessorAgent
from crescendo_ai.storage.store import JSONStore
from tests.conftest import FakeLLMClient


def test_process_extracts_and_saves_meeting(tmp_path):
    llm = FakeLLMClient(
        json_responses=[
            {
                "title": "Weekly Exec Meeting",
                "summary": "Discussed recital planning.",
                "decisions": ["Booked recital hall for June 3rd"],
                "action_items": [
                    {"owner": "President", "task": "Confirm catering", "deadline": "Friday"}
                ],
                "open_questions": ["Who is emceeing?"],
                "risks": ["Low volunteer turnout"],
                "next_meeting_recommendation": "Next week to finalize marketing",
            }
        ]
    )
    store = JSONStore(tmp_path)
    processor = TranscriptProcessorAgent(llm, store)

    meeting = processor.process(
        "raw transcript text", channel="C1", attendees=["President", "Treasurer"]
    )

    assert meeting.status == "completed"
    assert meeting.decisions == ["Booked recital hall for June 3rd"]
    assert meeting.action_items[0]["owner"] == "President"
    assert meeting.attendees == ["President", "Treasurer"]
    assert store.get_meeting(meeting.id).summary == "Discussed recital planning."


def test_process_updates_existing_meeting(tmp_path):
    llm = FakeLLMClient(
        json_responses=[
            {
                "title": "Weekly Exec Meeting",
                "summary": "Wrapped up planning.",
                "decisions": [],
                "action_items": [],
                "open_questions": [],
                "risks": [],
                "next_meeting_recommendation": "",
            }
        ]
    )
    store = JSONStore(tmp_path)
    processor = TranscriptProcessorAgent(llm, store)
    existing_id = store.new_id()

    from crescendo_ai.storage.models import Meeting

    store.save_meeting(Meeting(id=existing_id, channel="C1", title="Draft Meeting", status="planned"))

    meeting = processor.process("transcript", meeting_id=existing_id, channel="C1")

    assert meeting.id == existing_id
    assert meeting.status == "completed"
    assert store.get_meeting(existing_id).summary == "Wrapped up planning."
