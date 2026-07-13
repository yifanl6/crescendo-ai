from crescendo_ai.agents.conversation_monitor import ConversationMonitorAgent, TopicThread
from crescendo_ai.agents.meeting_planner import MeetingPlannerAgent
from crescendo_ai.storage.store import JSONStore
from tests.conftest import FakeLLMClient


def test_find_proposal_returns_none_below_threshold(tmp_path):
    llm = FakeLLMClient()
    store = JSONStore(tmp_path)
    planner = MeetingPlannerAgent(llm, store, confidence_threshold=0.9)
    monitor = ConversationMonitorAgent(llm)

    monitor._channels["C1"] = {"venue": TopicThread(label="venue", mentions=1, participants={"U1"})}

    assert planner.find_proposal(monitor, "C1") is None


def test_find_proposal_returns_candidate_above_threshold(tmp_path):
    llm = FakeLLMClient()
    store = JSONStore(tmp_path)
    planner = MeetingPlannerAgent(llm, store, confidence_threshold=0.1)
    monitor = ConversationMonitorAgent(llm)

    monitor._channels["C1"] = {
        "venue": TopicThread(label="venue", mentions=4, participants={"U1", "U2"})
    }
    proposal = planner.find_proposal(monitor, "C1")

    assert proposal["topics"] == ["venue"]
    assert proposal["participants"] == ["U1", "U2"]


def test_generate_agenda_saves_meeting(tmp_path):
    llm = FakeLLMClient(
        json_responses=[
            {
                "title": "Exec Board Planning Meeting",
                "estimated_length_minutes": 25,
                "agenda": ["Volunteer recruitment", "Recital venue"],
                "expected_outcomes": ["Assign volunteers"],
            }
        ]
    )
    store = JSONStore(tmp_path)
    planner = MeetingPlannerAgent(llm, store)
    proposal = {
        "channel": "C1",
        "topics": ["venue"],
        "participants": ["U1"],
        "evidence": "- venue: mentioned 4 times, unresolved",
        "confidence": 0.8,
    }

    meeting = planner.generate_agenda(proposal)

    assert meeting.title == "Exec Board Planning Meeting"
    assert meeting.estimated_length_minutes == 25
    assert store.get_meeting(meeting.id).title == "Exec Board Planning Meeting"
