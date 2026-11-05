from groq import Groq
from openai import OpenAI


class EditorialEngine:
    """3-Stage Fact Verification, Editorial Synthesis, and Translation Engine."""

    def __init__(self, groq_api_key: str, openrouter_api_key: str = None):
        self.groq_client = Groq(api_key=groq_api_key)
        self.openrouter_client = None
        if openrouter_api_key and openrouter_api_key.strip():
            self.openrouter_client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=openrouter_api_key,
                default_headers={
                    "HTTP-Referer": "https://github.com/mardi-7x/news-ai-engine",
                    "X-Title": "News AI Engine"
                }
            )
        self.model_primary = "openai/gpt-oss-120b"
        self.model_fallback = "openai/gpt-oss-20b"
        self.model_nemotron = "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free"

    def _call_groq(self, prompt: str, max_tokens: int = 1800, temperature: float = 0.2) -> str:
        try:
            resp = self.groq_client.chat.completions.create(
                model=self.model_primary,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens
            )
            return resp.choices[0].message.content.strip()
        except Exception:
            resp = self.groq_client.chat.completions.create(
                model=self.model_fallback,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens
            )
            return resp.choices[0].message.content.strip()

    def optimize_intent(self, raw_user_input: str) -> str:
        """ইউজারের অগোছালো ইনপুট থেকে নিখুঁত সার্চ কোয়েরি তৈরি করে।"""
        prompt = f"""You are a search intent optimizer for a news verification engine.
Convert the user's raw input into a crisp, unambiguous 2-5 word English search query.
Resolve spelling mistakes or entity ambiguities (e.g., 'Space x' -> 'SpaceX Starship aerospace', 'wb hs exam' -> 'WBCHSE Higher Secondary exam').
Output ONLY the search query string without quotes or punctuation.

User Input: {raw_user_input}"""
        try:
            optimized = self._call_groq(prompt, max_tokens=25, temperature=0.1)
            return optimized.replace('"', '').replace("'", "").strip()
        except Exception:
            return raw_user_input

    def verify_facts(self, target_topic: str, news_items: list) -> str:
        """একাধিক সোর্স ক্রস-চেক করে সত্য তথ্য ও কনফিডেন্স লেভেল বের করে।"""
        formatted_sources = "\n\n".join([
            f"Source [{i+1}] ({item['source']}):\nHeadline: {item['title']}\nDetails: {item['summary'][:400]}"
            for i, item in enumerate(news_items)
        ])

        prompt = f"""You are a Chief Fact-Checker. Analyze the provided news sources about '{target_topic}':
1. ENTITY FILTER: Immediately discard any source that talks about an unrelated entity or coincidental name match.
2. CROSS-VERIFICATION: Compare claims across the remaining independent sources.
3. CONFIDENCE TAGGING: Extract the core factual developments into bullet points. Tag each bullet as [Confirmed by Multiple Sources] or [Single Source Report].
4. CONFLICT CHECK: If two sources contradict each other on dates or numbers, explicitly note the discrepancy.

News Data:
{formatted_sources}"""
        return self._call_groq(prompt, max_tokens=1000, temperature=0.1)

    def write_structured_briefing(self, verified_facts: str) -> str:
        """যাচাইকৃত তথ্যের ওপর ভিত্তি করে এক্সিকিউটিভ বুলেট-পয়েন্ট ব্রিফিং লেখে।"""
        prompt = f"""You are a Senior Intelligence Columnist. Write a sharp, structured news briefing strictly based on the verified facts below:
- Start with a bold, factual Headline (📰).
- Present the key verified developments in clear bullet points (•). Include concrete facts, dates, and figures.
- Add a final section titled '⚖️ Editorial Observation:' (2-3 sentences analyzing the real-world impact).
- Do NOT invent URLs or add fake citations inside the text.

Verified Facts:
{verified_facts}"""
        return self._call_groq(prompt, max_tokens=1500, temperature=0.2)

    def translate_briefing(self, english_text: str, target_language: str) -> str:
        if target_language.lower() in ["english", "en"]:
            return english_text

        prompt = f"""You are an expert journalistic translator.
Translate the following news intelligence briefing into natural, high-standard {target_language}.
Keep all bullet points (•), emojis (📰, ⚖️), and structure intact.
Translate every single sentence completely without cutting off:

{english_text}"""
        if self.openrouter_client:
            try:
                resp = self.openrouter_client.chat.completions.create(
                    model=self.model_nemotron,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2
                )
                if resp.choices[0].message.content:
                    return resp.choices[0].message.content.strip()
            except Exception:
                pass
        return self._call_groq(prompt, max_tokens=3500, temperature=0.2)

    def generate(self, news_items: list, target_language: str = "Bengali", query: str = "") -> dict:
        if not news_items:
            return {
                "editorial": "❌ কোনো নির্ভরযোগ্য সংবাদ সূত্র পাওয়া যায়নি। অনুগ্রহ করে বিষয়টি আরেকটু স্পষ্ট করে লিখুন।",
                "verified_facts": "",
                "sources": []
            }

        # ধাপ ১: ক্রস-ভেরিফিকেশন
        verified_facts = self.verify_facts(query, news_items)

        # ধাপ ২: বুলেট-পয়েন্ট ব্রিফিং ড্রাফট
        english_briefing = self.write_structured_briefing(verified_facts)

        # ধাপ ৩: ভাষা রূপান্তর
        final_body = self.translate_briefing(english_briefing, target_language)

        # ধাপ ৪: পাইথন দিয়ে নিচে নিশ্চিতভাবে আসল সোর্স ইউআরএল যুক্ত করা
        source_lines = []
        for idx, item in enumerate(news_items, 1):
            src_name = item.get("source", "Verified Source")
            title = item.get("title", "News Link")
            url = item.get("url", "")
            if url:
                source_lines.append(f"{idx}. [{src_name}] {title}\n   🔗 {url}")

        sources_block = "\n\n".join(source_lines)
        header_label = (
            "🔗 **যাচাইকৃত আসল খবরের সূত্রসমূহ (Verified Sources):**"
            if target_language.lower() == "bengali"
            else "🔗 **Verified Authentic Sources:**"
        )

        complete_output = (
            f"{final_body}\n\n"
            f"---\n"
            f"{header_label}\n"
            f"{sources_block}"
        )

        return {
            "editorial": complete_output,
            "verified_facts": verified_facts,
            "sources": news_items
        }
