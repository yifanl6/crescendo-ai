"""MCP server exposing Crescendo AI's tools to any MCP-compatible client.

Run standalone with `python mcp_server.py`, or point an MCP client (Claude
Desktop, etc.) at this file. The client's own model decides when to call
each tool.
"""

from mcp.server.fastmcp import FastMCP

from crescendo_ai.agents.knowledge_agent import KnowledgeAgent
from crescendo_ai.agents.meeting_planner import MeetingPlannerAgent
from crescendo_ai.agents.reminder_agent import ReminderAgent
from crescendo_ai.agents.transcript_processor import TranscriptProcessorAgent
from crescendo_ai.config import config
from crescendo_ai.llm.client import OpenAIClient
from crescendo_ai.storage.store import JSONStore

mcp = FastMCP("crescendo-ai")

_llm = OpenAIClient(config.openai_api_key, config.openai_model) if config.openai_api_key else None
_store = JSONStore(config.data_dir)
_reminder_agent = ReminderAgent(config.officers)
_knowledge_agent = KnowledgeAgent(_llm, _store) if _llm else None
_transcript_processor = TranscriptProcessorAgent(_llm, _store) if _llm else None
_meeting_planner = MeetingPlannerAgent(_llm, _store, config.meeting_confidence_threshold) if _llm else None


def _require_llm() -> None:
    if _llm is None:
        raise RuntimeError("OPENAI_API_KEY is not configured")


@mcp.tool()
def create_meeting(channel: str, topics: list, participants: list, evidence: str = "") -> dict:
    """Draft a meeting (title, length, agenda, expected outcomes) from unresolved topics."""
    _require_llm()
    proposal = {
        "channel": channel,
        "topics": topics,
        "participants": participants,
        "evidence": evidence or "\n".join(f"- {t}" for t in topics),
        "confidence": 1.0,
    }
    meeting = _meeting_planner.generate_agenda(proposal)
    return meeting.to_dict()


@mcp.tool()
def create_agenda(meeting_id: str) -> dict:
    """Fetch the agenda and details for an existing meeting by id."""
    meeting = _store.get_meeting(meeting_id)
    if meeting is None:
        raise ValueError(f"No meeting found with id {meeting_id}")
    return meeting.to_dict()


@mcp.tool()
def save_meeting(meeting_id: str, transcript: str, attendees: list = None, channel: str = "") -> dict:
    """Process a meeting transcript and persist the extracted summary/decisions/action items."""
    _require_llm()
    meeting = _transcript_processor.process(
        transcript, meeting_id=meeting_id, channel=channel, attendees=attendees or []
    )
    return meeting.to_dict()


@mcp.tool()
def send_reminder(meeting_id: str) -> dict:
    """Send personalized Slack DM reminders for a meeting's action items."""
    from slack_sdk import WebClient

    meeting = _store.get_meeting(meeting_id)
    if meeting is None:
        raise ValueError(f"No meeting found with id {meeting_id}")
    if not config.slack_bot_token:
        raise RuntimeError("SLACK_BOT_TOKEN is not configured")

    slack_client = WebClient(token=config.slack_bot_token)
    sent = _reminder_agent.send_reminders(slack_client, meeting.action_items)
    return {"sent": sent}


@mcp.tool()
def search_history(query: str) -> dict:
    """Search past meetings for institutional knowledge (e.g. 'who organized last year's fundraiser?')."""
    _require_llm()
    return {"answer": _knowledge_agent.answer(query)}


if __name__ == "__main__":
    mcp.run()
