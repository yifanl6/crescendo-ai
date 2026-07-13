# Crescendo AI

Proactive Slack AI executive-board assistant for student music organizations,
orchestras, and community arts nonprofits. It monitors Slack conversations,
proposes meetings when planning discussions stall, drafts agendas, extracts
action items from meeting transcripts, sends personalized follow-up DMs, and
preserves institutional memory across officer transitions.

## Architecture

```
crescendo_ai/
  config.py              env-driven configuration
  llm/client.py           OpenAI wrapper (complete_json / complete_text)
  storage/                Meeting model + JSON file store
  search/                 Real-time search wrapper (Tavily)
  agents/
    conversation_monitor.py   tracks unresolved topics per channel
    meeting_planner.py        decides when a meeting is needed + drafts agenda
    transcript_processor.py   extracts summary/decisions/action items/risks
    reminder_agent.py         personalized Slack DM reminders
    music_advisor.py          repertoire/grants/festivals via real-time search
    knowledge_agent.py        institutional memory Q&A over past meetings
  slack_bot/              Slack Bolt event/command handlers + Block Kit formatting
  mcp/server.py            MCP server exposing the same agents as tools

main.py         Slack Bolt entrypoint (Socket Mode)
mcp_server.py   MCP server entrypoint
```

Every agent takes its dependencies (an `LLMClient`, a `JSONStore`, a search
client) as constructor arguments, so each is independently unit-testable with
a fake LLM client — see `tests/`.

## Setup

1. **Install dependencies**

   ```bash
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Create the Slack app**

   Use `slack_manifest.yaml` to create the app at https://api.slack.com/apps
   ("Create New App" → "From an app manifest"). This wires up:
   - Bot scopes: `chat:write`, `im:write`, `im:history`, `channels:history`,
     `groups:history`, `files:read`, `commands`, `users:read`
   - Socket Mode + an `app_token` (create one under **Basic Information →
     App-Level Tokens** with the `connections:write` scope)
   - Event subscriptions: `message.channels`, `message.groups`, `file_shared`
   - Slash commands: `/crescendo-ask`, `/crescendo-music`

   Install the app to your workspace and invite the bot to the channels you
   want it to monitor.

3. **Configure environment variables**

   ```bash
   cp .env.example .env
   ```

   Fill in `SLACK_BOT_TOKEN` (`xoxb-...`), `SLACK_APP_TOKEN` (`xapp-...`),
   `SLACK_SIGNING_SECRET`, `OPENAI_API_KEY`, and optionally `TAVILY_API_KEY`
   (get one free at https://tavily.com — powers the Music Advisor's
   real-time search).

4. **Map officers to Slack user IDs** (for personalized reminder DMs)

   ```bash
   cp data/officers.example.json data/officers.json
   ```

   Edit it with real Slack user IDs, e.g. `{"President": "U0123ABC"}`. Find a
   user ID via their Slack profile → "Copy member ID".

## Running

**Slack bot** (Socket Mode, no public URL needed):

```bash
python main.py
```

**MCP server** (exposes `create_meeting`, `create_agenda`, `save_meeting`,
`send_reminder`, `search_history` as tools to any MCP client, e.g. Claude
Desktop):

```bash
python mcp_server.py
```

Example Claude Desktop config entry:

```json
{
  "mcpServers": {
    "crescendo-ai": {
      "command": "python",
      "args": ["/absolute/path/to/mcp_server.py"]
    }
  }
}
```

## Using it

- Post in a monitored channel about unresolved planning ("We still need
  performers", "Has anyone booked the recital hall?"). After a topic is
  mentioned repeatedly by multiple people without a resolution, Crescendo AI
  posts a meeting suggestion with a "Prepare meeting" button that generates
  an agenda.
- Upload a `.txt` meeting transcript as a file in a channel — Crescendo AI
  extracts the summary/decisions/action items/risks, posts them back, saves
  the meeting to institutional memory, and DMs each owner their assigned
  tasks and deadlines.
- `/crescendo-ask has anyone booked the recital hall before?` — searches past
  meetings and answers from that history.
- `/crescendo-music` or `/crescendo-music grant deadlines` — live
  recommendations on repertoire, grants, festivals, and composer
  anniversaries.

## Tests

```bash
pytest
```

Every agent test uses a `FakeLLMClient` (see `tests/conftest.py`) with
scripted JSON/text responses, so the suite runs with no API keys and no
network access.

## Notes on this MVP

- Storage is a simple per-meeting JSON file store (`data/meetings/`) —
  swappable behind the same interface if this moves to a real database.
- `ConversationMonitorAgent`'s topic state is in-memory per process; restart
  the bot and it starts tracking fresh (persisted meetings are unaffected).
- The Music Advisor and real-time search require `TAVILY_API_KEY`; without
  it, `/crescendo-music` reports that live search is unavailable rather than
  failing silently.
