from crescendo_ai.agents.conversation_monitor import ConversationMonitorAgent
from tests.conftest import FakeLLMClient


def test_ingest_message_tracks_open_topic():
    llm = FakeLLMClient(
        json_responses=[
            {
                "is_planning_topic": True,
                "topic_label": "performer recruitment",
                "resolved": False,
                "sentiment": "uncertain",
            }
        ]
    )
    monitor = ConversationMonitorAgent(llm)
    monitor.ingest_message("C1", "U1", "We still need performers", "1")

    topics = monitor.open_topics("C1")
    assert len(topics) == 1
    assert topics[0].label == "performer recruitment"
    assert topics[0].mentions == 1


def test_resolved_topic_is_excluded():
    llm = FakeLLMClient(
        json_responses=[
            {
                "is_planning_topic": True,
                "topic_label": "recital venue",
                "resolved": False,
                "sentiment": "neutral",
            },
            {
                "is_planning_topic": True,
                "topic_label": "recital venue",
                "resolved": True,
                "sentiment": "positive",
            },
        ]
    )
    monitor = ConversationMonitorAgent(llm)
    monitor.ingest_message("C1", "U1", "Has anyone booked the recital hall?", "1")
    monitor.ingest_message("C1", "U2", "Yes, I booked it for June 3rd", "2")

    assert monitor.open_topics("C1") == []


def test_non_planning_message_is_ignored():
    llm = FakeLLMClient(
        json_responses=[
            {"is_planning_topic": False, "topic_label": None, "resolved": False, "sentiment": "neutral"}
        ]
    )
    monitor = ConversationMonitorAgent(llm)
    monitor.ingest_message("C1", "U1", "lol nice", "1")

    assert monitor.open_topics("C1") == []


def test_confidence_increases_with_mentions_and_participants():
    llm = FakeLLMClient(
        json_responses=[
            {
                "is_planning_topic": True,
                "topic_label": "fundraising",
                "resolved": False,
                "sentiment": "neutral",
            },
            {
                "is_planning_topic": True,
                "topic_label": "fundraising",
                "resolved": False,
                "sentiment": "neutral",
            },
        ]
    )
    monitor = ConversationMonitorAgent(llm)
    monitor.ingest_message("C1", "U1", "We should discuss fundraising", "1")
    thread = monitor.open_topics("C1")[0]
    first_confidence = monitor.confidence(thread)

    monitor.ingest_message("C1", "U2", "Yeah fundraising needs a plan", "2")
    second_confidence = monitor.confidence(thread)

    assert second_confidence > first_confidence
