class KnowledgeAgent:
    """Preserves institutional memory: saves meetings and answers questions about them."""

    def __init__(self, llm_client, store):
        self._llm = llm_client
        self._store = store

    def save_meeting(self, meeting):
        return self._store.save_meeting(meeting)

    def answer(self, question: str) -> str:
        matches = self._store.search_meetings(question, top_k=5)
        if not matches:
            return "I couldn't find any past meetings related to that."

        context = "\n\n".join(
            f"Meeting: {m.title} ({m.created_at})\n"
            f"Summary: {m.summary}\n"
            f"Decisions: {'; '.join(m.decisions) or 'none recorded'}"
            for m in matches
        )
        system = (
            "You are the institutional memory for a student music organization's "
            "executive board. Answer the officer's question using only the provided "
            "meeting history. Cite meeting titles/dates. If the answer isn't in the "
            "history, say so plainly."
        )
        user = f"Question: {question}\n\nMeeting history:\n{context}"
        return self._llm.complete_text(system, user)
