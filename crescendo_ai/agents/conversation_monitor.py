from dataclasses import dataclass, field


@dataclass
class TopicThread:
    label: str
    mentions: int = 0
    participants: set = field(default_factory=set)
    messages: list = field(default_factory=list)
    resolved: bool = False
    last_ts: str = ""


class ConversationMonitorAgent:
    """Observes Slack messages and tracks unresolved planning topics per channel."""

    def __init__(self, llm_client):
        self._llm = llm_client
        self._channels: dict = {}

    def ingest_message(self, channel: str, user: str, text: str, ts: str) -> dict:
        classification = self._classify(text)
        if not classification.get("is_planning_topic"):
            return classification

        label = (classification.get("topic_label") or "general planning").strip()
        key = label.lower()
        channel_topics = self._channels.setdefault(channel, {})
        thread = channel_topics.setdefault(key, TopicThread(label=label))
        thread.mentions += 1
        thread.participants.add(user)
        thread.messages.append(text)
        thread.last_ts = ts
        if classification.get("resolved"):
            thread.resolved = True
        return classification

    def _classify(self, text: str) -> dict:
        system = (
            "You monitor Slack messages for a student music organization's executive "
            "board. Classify the message and return strict JSON with keys: "
            "is_planning_topic (bool), topic_label (short string or null), "
            "resolved (bool, true only if this message states a clear decision or "
            "completion of that topic), sentiment (one of 'positive', 'neutral', "
            "'negative', 'uncertain')."
        )
        return self._llm.complete_json(system, text)

    def open_topics(self, channel: str) -> list:
        return [t for t in self._channels.get(channel, {}).values() if not t.resolved]

    def confidence(self, thread: TopicThread) -> float:
        mention_score = min(thread.mentions / 4, 1.0)
        participant_score = min(len(thread.participants) / 3, 1.0)
        return round(0.6 * mention_score + 0.4 * participant_score, 2)
