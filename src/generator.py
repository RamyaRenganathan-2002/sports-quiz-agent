import json
from google import genai
from google.genai import types

from src.config import GEMINI_API_KEY, GEMINI_MODEL
from src.database import query_historic_facts
from src.search import get_live_news_context


def compile_quiz_data(sport, difficulty):
    """
    1. Gathers context from ChromaDB (Historical).
    2. Gathers context from DuckDuckGo (Live news).
    3. Blends them inside a grounded prompt.
    4. Calls Gemini and returns structured quiz JSON + the context used.
    """
    # 1. Query ChromaDB for historic facts
    db_query = f"{sport} history championships rules records"
    db_matches = query_historic_facts(sport=sport, query_text=db_query, n_results=3)
    db_context = "\n".join(db_matches) if db_matches else "No offline historic data recorded."

    # 2. Query live web
    web_context = get_live_news_context(sport)

    # 3. Merge contexts
    unified_context = f"=== HISTORICAL FACTS ===\n{db_context}\n\n=== LIVE INTERNET NEWS ===\n{web_context}"

    # 4. Build prompt
    system_instruction = (
        "You are an expert sports quiz creator. Your job is to write multiple-choice quizzes "
        "relying strictly on the provided Context. Avoid hallucinations. Do not invent facts not "
        "found in the Context below. If facts are scarce, make do with what you have, "
        "but keep all details accurate to the text context.\n\n"
        f"CONTEXT DETAILS:\n{unified_context}"
    )

    user_prompt = (
        f"Generate exactly 4 unique multiple-choice questions for the sport: {sport}.\n"
        f"Difficulty target: {difficulty}.\n"
        "Return ONLY a JSON array. Each item must have exactly these keys: "
        "'question', 'options' (an object with keys A, B, C, D), 'correct_answer' (a single letter), "
        "and 'explanation' (a short reasoning grounded in the context)."
    )

    client = genai.Client(api_key=GEMINI_API_KEY)

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            temperature=0.7,
        ),
    )

    try:
        quiz_data = json.loads(response.text)
    except (json.JSONDecodeError, TypeError) as e:
        raise ValueError(f"Failed to parse Gemini's JSON output: {e}\nRaw output: {response.text}")

    return quiz_data, unified_context