class MusicAdvisorAgent:
    """Surfaces repertoire ideas, grants, festivals, and news via real-time search."""

    DEFAULT_QUERIES = [
        "classical music composer anniversaries this year",
        "music education grants deadlines for nonprofits",
        "youth orchestra and community music festival call for submissions",
        "concert repertoire ideas for student orchestras",
    ]

    def __init__(self, llm_client, search_client):
        self._llm = llm_client
        self._search = search_client

    def get_recommendations(self, topic: str | None = None) -> dict:
        queries = [topic] if topic else self.DEFAULT_QUERIES
        results = []
        errors = []
        for query in queries:
            try:
                results.extend(self._search.search(query, max_results=4))
            except Exception as exc:  # search backend may be unconfigured or down
                errors.append(str(exc))

        if not results:
            return {"items": [], "errors": errors}

        system = (
            "You are a music advisor for a student music organization's executive "
            "board. Summarize the search results into strict JSON with key 'items': "
            "an array of objects with 'headline' and 'detail', focused on actionable "
            "opportunities (repertoire, grants, festivals, anniversaries, news)."
        )
        user = "\n\n".join(f"{r['title']}: {r['snippet']} ({r['url']})" for r in results)
        summary = self._llm.complete_json(system, user)
        return {"items": summary.get("items", []), "errors": errors}
