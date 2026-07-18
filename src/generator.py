import json
import random
from google import genai
from google.genai import types

from src.config import GEMINI_API_KEY, GEMINI_MODEL
from src.database import query_historic_facts
from src.search import get_live_news_context


def compile_quiz_data(sport, difficulty, previous_questions=None):
    """
    1. Gathers context from ChromaDB (Historical) — with slight query variation for diversity.
    2. Gathers context from DuckDuckGo (Live news).
    3. Blends them inside a grounded prompt, explicitly avoiding previously asked questions.
    4. Calls Gemini and returns structured quiz JSON + the context used.
    """
    previous_questions = previous_questions or []

    # 1. Query ChromaDB — vary the query phrasing each call so different facts surface
    query_variants = [
        f"{sport} history championships rules records",
        f"{sport} famous players achievements milestones",
        f"{sport} tournament winners historic moments",
        f"{sport} records statistics notable events",
    ]
    db_query = random.choice(query_variants)
    db_matches = query_historic_facts(sport=sport, query_text=db_query, n_results=4)
    db_context = "\n".join(db_matches) if db_matches else "No offline historic data recorded."

    # 2. Query live web
    web_context = get_live_news_context(sport)

    # 3. Merge contexts
    unified_context = f"=== HISTORICAL FACTS ===\n{db_context}\n\n=== LIVE INTERNET NEWS ===\n{web_context}"

    # 4. Build prompt
    system_instruction = (
        "You are an expert sports quiz creator. Your job is to write multiple-choice quizzes "
        "relying strictly on the provided Context, but the Context is for YOUR eyes only — "
        "it must never be visible or referenced in the output. Avoid hallucinations. Do not invent facts not "
        "found in the Context below. If facts are scarce, make do with what you have, "
        "but keep all details accurate to the text context. If a piece of context is just page metadata "
        "(like a title or publish date) rather than a real sports fact, ignore it and don't build a question from it.\n\n"
        f"CONTEXT DETAILS:\n{unified_context}"
    )

    avoid_block = ""
    if previous_questions:
        formatted = "\n".join(f"- {q}" for q in previous_questions)
        avoid_block = (
            "\n\nIMPORTANT: Do NOT repeat or closely rephrase any of these previously asked questions:\n"
            f"{formatted}\nGenerate genuinely different questions, covering different facts or angles."
        )

    user_prompt = (
        f"Generate exactly 4 unique multiple-choice questions for the sport: {sport}.\n"
        f"Difficulty target: {difficulty}."
        f"{avoid_block}\n\n"
        "CRITICAL RULES for question writing:\n"
        "- Questions must test the player's sports knowledge directly (players, records, events, rules, history).\n"
        "- NEVER reference 'the context', 'the snippet', 'Web Source 1/2/3', 'the article', 'the passage', "
        "or any mention of where the information came from. The user should never know facts were retrieved.\n"
        "- Do NOT ask about publish dates, article titles, or metadata of a source — only ask about the sport itself.\n"
        "- Write each question as a standalone trivia question, exactly like it would appear in a real quiz app.\n\n"
        "Return ONLY a JSON array. Each item must have exactly these keys: "
        "'question', 'options' (an object with keys A, B, C, D), 'correct_answer' (a single letter), "
        "and 'explanation' (a short reasoning that teaches the fact — do not mention sources here either)."
    )

    client = genai.Client(api_key=GEMINI_API_KEY)

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            temperature=0.9,  # bumped up for more variety across regenerations
        ),
    )

    try:
        quiz_data = json.loads(response.text)
    except (json.JSONDecodeError, TypeError) as e:
        raise ValueError(f"Failed to parse Gemini's JSON output: {e}\nRaw output: {response.text}")

    return quiz_data, unified_context