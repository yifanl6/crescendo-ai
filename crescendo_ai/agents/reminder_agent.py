class ReminderAgent:
    """Turns action items into personalized Slack DMs and tracks who owns what."""

    def __init__(self, officers: dict):
        self._officers = officers  # display name/role -> Slack user id

    def group_by_owner(self, action_items: list) -> dict:
        grouped: dict = {}
        for item in action_items:
            owner = item.get("owner", "Unassigned")
            grouped.setdefault(owner, []).append(item)
        return grouped

    def build_dm_text(self, owner: str, items: list) -> str:
        lines = [f"Hi {owner}, here's what's on your plate from the latest meeting:"]
        for item in items:
            deadline = item.get("deadline")
            deadline_text = f" (due {deadline})" if deadline else ""
            lines.append(f"- {item.get('task')}{deadline_text}")
        return "\n".join(lines)

    def send_reminders(self, slack_client, action_items: list) -> list:
        sent = []
        for owner, items in self.group_by_owner(action_items).items():
            text = self.build_dm_text(owner, items)
            user_id = self._officers.get(owner)
            if not user_id:
                sent.append({"owner": owner, "status": "skipped_no_slack_id", "text": text})
                continue
            dm = slack_client.conversations_open(users=[user_id])
            channel_id = dm["channel"]["id"]
            slack_client.chat_postMessage(channel=channel_id, text=text)
            sent.append({"owner": owner, "status": "sent", "text": text})
        return sent
