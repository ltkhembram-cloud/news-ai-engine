from groq import Groq
from .database import get_top_interests, DB_FILE


class RecommendationEngine:
    """Synthesizes personalized daily briefing topics from user search history."""

    def __init__(self, groq_api_key: str):
        self.groq_client = Groq(api_key=groq_api_key)
        self.model = "openai/gpt-oss-120b"

    def get_personalized_topic(self, chat_id: int, db_path: str = DB_FILE) -> str:
        interests = get_top_interests(chat_id, limit=3, db_path=db_path)
        if not interests:
            return "India Science Technology Major News"

        prompt = f"""Based on the user's top searched topics: {', '.join(interests)},
create ONE specific, timely 3-4 word English news search query for their morning intelligence briefing.
Output ONLY the search query without quotes or punctuation."""
        try:
            resp = self.groq_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=20
            )
            return resp.choices[0].message.content.strip().replace('"', '')
        except Exception:
            return f"{interests[0]} latest updates"
