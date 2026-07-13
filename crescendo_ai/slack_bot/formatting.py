import json


def meeting_suggestion_blocks(proposal: dict) -> list:
    topics = "\n".join(f"• {t}" for t in proposal["topics"])
    return [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    "*It looks like these topics have been discussed without a "
                    f"decision:*\n{topics}\n\nWould you like me to prepare a meeting?"
                ),
            },
        },
        {
            "type": "actions",
            "block_id": "crescendo_meeting_suggestion",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Prepare meeting"},
                    "style": "primary",
                    "action_id": "crescendo_prepare_meeting",
                    "value": json.dumps(proposal),
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Not now"},
                    "action_id": "crescendo_dismiss_meeting",
                },
            ],
        },
    ]


def agenda_blocks(meeting) -> list:
    agenda_lines = "\n".join(f"{i + 1}. {item}" for i, item in enumerate(meeting.agenda)) or "—"
    outcomes = "\n".join(f"• {o}" for o in meeting.expected_outcomes) or "—"
    return [
        {"type": "header", "text": {"type": "plain_text", "text": meeting.title}},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"*Estimated length:* {meeting.estimated_length_minutes} minutes\n\n"
                    f"*Agenda*\n{agenda_lines}\n\n*Expected outcomes*\n{outcomes}"
                ),
            },
        },
    ]


def transcript_summary_blocks(meeting) -> list:
    decisions = "\n".join(f"• {d}" for d in meeting.decisions) or "—"
    actions = (
        "\n".join(
            f"• {a.get('owner')}: {a.get('task')}"
            + (f" (due {a['deadline']})" if a.get("deadline") else "")
            for a in meeting.action_items
        )
        or "—"
    )
    risks = "\n".join(f"• {r}" for r in meeting.risks) or "—"
    return [
        {"type": "header", "text": {"type": "plain_text", "text": f"Meeting notes: {meeting.title}"}},
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*Summary*\n{meeting.summary or '—'}"}},
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*Decisions*\n{decisions}"}},
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*Action items*\n{actions}"}},
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*Risks*\n{risks}"}},
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Next meeting: {meeting.next_meeting_recommendation or 'TBD'}",
                }
            ],
        },
    ]
