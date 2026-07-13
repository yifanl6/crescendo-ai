from crescendo_ai.agents.knowledge_agent import KnowledgeAgent
from crescendo_ai.storage.models import Meeting
from crescendo_ai.storage.store import JSONStore
from tests.conftest import FakeLLMClient


def test_answer_returns_message_when_no_history(tmp_path):
    llm = FakeLLMClient()
    store = JSONStore(tmp_path)
    agent = KnowledgeAgent(llm, store)

    answer = agent.answer("have we performed Beethoven's 9th before?")

    assert "couldn't find" in answer.lower()


def test_answer_uses_matching_meeting_history(tmp_path):
    llm = FakeLLMClient(text_responses=["Yes, last year's fundraiser was organized by the Treasurer."])
    store = JSONStore(tmp_path)
    agent = KnowledgeAgent(llm, store)
    meeting = Meeting(
        id="m1",
        channel="C1",
        title="Fundraiser Retro",
        status="completed",
        summary="The treasurer organized last year's fundraiser.",
    )
    agent.save_meeting(meeting)

    answer = agent.answer("who organized last year's fundraiser?")

    assert "Treasurer" in answer
