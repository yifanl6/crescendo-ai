import logging

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from crescendo_ai.agents.conversation_monitor import ConversationMonitorAgent
from crescendo_ai.agents.knowledge_agent import KnowledgeAgent
from crescendo_ai.agents.meeting_planner import MeetingPlannerAgent
from crescendo_ai.agents.music_advisor import MusicAdvisorAgent
from crescendo_ai.agents.reminder_agent import ReminderAgent
from crescendo_ai.agents.transcript_processor import TranscriptProcessorAgent
from crescendo_ai.config import config
from crescendo_ai.llm.client import OpenAIClient
from crescendo_ai.search.realtime_search import RealTimeSearch
from crescendo_ai.slack_bot.handlers import AppContext, register_handlers
from crescendo_ai.storage.store import JSONStore

logging.basicConfig(level=logging.INFO)


def build_app() -> App:
    if not config.slack_bot_token or not config.slack_app_token:
        raise RuntimeError("SLACK_BOT_TOKEN and SLACK_APP_TOKEN must be set")

    llm = OpenAIClient(config.openai_api_key, config.openai_model)
    search = RealTimeSearch(config.tavily_api_key)
    store = JSONStore(config.data_dir)

    ctx = AppContext(
        monitor=ConversationMonitorAgent(llm),
        planner=MeetingPlannerAgent(llm, store, config.meeting_confidence_threshold),
        transcript_processor=TranscriptProcessorAgent(llm, store),
        reminder_agent=ReminderAgent(config.officers),
        music_advisor=MusicAdvisorAgent(llm, search),
        knowledge_agent=KnowledgeAgent(llm, store),
        config=config,
    )

    app = App(token=config.slack_bot_token, signing_secret=config.slack_signing_secret)
    register_handlers(app, ctx)
    return app


if __name__ == "__main__":
    slack_app = build_app()
    SocketModeHandler(slack_app, config.slack_app_token).start()
