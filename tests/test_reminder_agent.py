from crescendo_ai.agents.reminder_agent import ReminderAgent


class FakeSlackClient:
    def __init__(self):
        self.opened = []
        self.posted = []

    def conversations_open(self, users):
        self.opened.append(users)
        return {"channel": {"id": f"D-{users[0]}"}}

    def chat_postMessage(self, channel, text):
        self.posted.append((channel, text))


def test_send_reminders_groups_by_owner_and_sends_dm():
    officers = {"President": "U1", "Treasurer": "U2"}
    agent = ReminderAgent(officers)
    slack = FakeSlackClient()
    action_items = [
        {"owner": "President", "task": "Reserve recital hall", "deadline": "Friday"},
        {"owner": "Treasurer", "task": "Finalize budget", "deadline": "Wednesday"},
    ]

    result = agent.send_reminders(slack, action_items)

    assert len(slack.posted) == 2
    assert {r["status"] for r in result} == {"sent"}


def test_send_reminders_skips_unknown_owner():
    agent = ReminderAgent({})
    slack = FakeSlackClient()

    result = agent.send_reminders(slack, [{"owner": "Mystery Officer", "task": "Do something"}])

    assert result[0]["status"] == "skipped_no_slack_id"
    assert not slack.posted


def test_build_dm_text_includes_deadline():
    agent = ReminderAgent({})
    text = agent.build_dm_text("President", [{"task": "Reserve recital hall", "deadline": "Friday"}])

    assert "Reserve recital hall" in text
    assert "Friday" in text
