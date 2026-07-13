import json
import logging

import requests

from crescendo_ai.slack_bot.formatting import (
    agenda_blocks,
    meeting_suggestion_blocks,
    transcript_summary_blocks,
)

logger = logging.getLogger(__name__)


class AppContext:
    def __init__(
        self,
        monitor,
        planner,
        transcript_processor,
        reminder_agent,
        music_advisor,
        knowledge_agent,
        config,
    ):
        self.monitor = monitor
        self.planner = planner
        self.transcript_processor = transcript_processor
        self.reminder_agent = reminder_agent
        self.music_advisor = music_advisor
        self.knowledge_agent = knowledge_agent
        self.config = config
        self._suggested_topics = set()


def register_handlers(app, ctx: AppContext) -> None:
    @app.event("message")
    def handle_message(event, client):
        if event.get("subtype") or event.get("bot_id"):
            return
        channel = event.get("channel")
        user = event.get("user")
        text = event.get("text", "")
        ts = event.get("ts")
        if not text or not channel or not user:
            return

        try:
            ctx.monitor.ingest_message(channel, user, text, ts)
        except Exception:
            logger.exception("Failed to process message for conversation monitor")
            return

        proposal = ctx.planner.find_proposal(ctx.monitor, channel)
        if not proposal:
            return

        key = (channel, tuple(sorted(proposal["topics"])))
        if key in ctx._suggested_topics:
            return
        ctx._suggested_topics.add(key)

        client.chat_postMessage(
            channel=channel,
            text="It looks like a meeting might help resolve some open topics.",
            blocks=meeting_suggestion_blocks(proposal),
        )

    @app.action("crescendo_prepare_meeting")
    def handle_prepare_meeting(ack, body, client):
        ack()
        proposal = json.loads(body["actions"][0]["value"])
        meeting = ctx.planner.generate_agenda(proposal)
        client.chat_postMessage(
            channel=proposal["channel"],
            text=f"Draft agenda ready: {meeting.title}",
            blocks=agenda_blocks(meeting),
        )

    @app.action("crescendo_dismiss_meeting")
    def handle_dismiss_meeting(ack):
        ack()

    @app.event("file_shared")
    def handle_file_shared(event, client):
        file_info = client.files_info(file=event["file_id"])["file"]
        if not file_info.get("mimetype", "").startswith("text/"):
            return

        headers = {"Authorization": f"Bearer {ctx.config.slack_bot_token}"}
        resp = requests.get(file_info["url_private_download"], headers=headers, timeout=15)
        resp.raise_for_status()
        transcript = resp.text
        channel = (file_info.get("channels") or [None])[0]

        meeting = ctx.transcript_processor.process(transcript, channel=channel or "")
        ctx.knowledge_agent.save_meeting(meeting)

        if channel:
            client.chat_postMessage(
                channel=channel,
                text=f"Processed meeting transcript: {meeting.title}",
                blocks=transcript_summary_blocks(meeting),
            )

        sent = ctx.reminder_agent.send_reminders(client, meeting.action_items)
        logger.info("Sent %d reminder DMs for meeting %s", len(sent), meeting.id)

    @app.command("/crescendo-ask")
    def handle_ask(ack, respond, command):
        ack()
        question = command.get("text", "").strip()
        if not question:
            respond("Ask me something like: has anyone booked the recital hall before?")
            return
        respond(ctx.knowledge_agent.answer(question))

    @app.command("/crescendo-music")
    def handle_music(ack, respond, command):
        ack()
        topic = command.get("text", "").strip() or None
        recs = ctx.music_advisor.get_recommendations(topic)
        if not recs["items"]:
            respond("I couldn't find any current recommendations right now.")
            return
        lines = [f"*{item.get('headline')}* — {item.get('detail')}" for item in recs["items"]]
        respond("\n".join(lines))
