# 🏆 AI-Powered Sports Quiz Generation Agent

An AI agent that generates factually grounded, multiple-choice sports quizzes using **Retrieval-Augmented Generation (RAG)** — combining a local vector knowledge base (ChromaDB) with live web search, then grounding an LLM (Gemini) to avoid hallucinated facts.


---

## ✨ Features

- **Any sport, not just a fixed list** — free-text input, not a limited dropdown
- **Adjustable difficulty** — Easy / Medium / Hard
- **RAG-grounded generation** — combines offline historic facts + live web search context
- **Anti-hallucination prompting** — LLM is explicitly instructed to only use retrieved context
- **No repeated questions** — tracks previously asked questions per session and steers the LLM away from them
- **Live score tracker** — sidebar shows progress and running score as you answer
- **Ground truth inspector** — expandable panel shows exactly what context grounded each quiz, for transparency/auditability

---

## 🏗️ Architecture
```text
       [User selects Sport + Difficulty]
                       │
                       ▼
             ┌────────────────────┐
             │    Streamlit UI    │  (app.py)
             └─────────┬──────────┘
                       │
                       ▼
         ┌────────────────────────────┐
         │      RAG Orchestrator      │  (src/generator.py)
         └───────┬──────────────┬─────┘
                 │              │
                 ▼              ▼
       ┌──────────────────┐  ┌────────────────────┐
       │     ChromaDB     │  │  Live Web Search   │
       │ (offline facts)  │  │ (DuckDuckGo/ddgs)  │
       └─────────┬────────┘  └──────────┬─────────┘
                 │                      │
                 └──────────┬───────────┘
                            ▼
                 Merged Context + Prompt
                            │
                            ▼
                 ┌───────────────────┐
                 │    Gemini API     │  (gemini-flash-latest)
                 │ (structured JSON) │
                 └──────────┬────────┘
                            │
                            ▼
               Quiz rendered in Streamlit
          (with score tracking + explanations)
```

**Why RAG instead of asking the LLM directly?** A general LLM can hallucinate sports facts or go stale on recent events. By retrieving verified offline facts (ChromaDB) and fresh web results (DuckDuckGo) *before* generation, and instructing the model to only use that retrieved context, we ground every question in something real and checkable — the "Inspect Ground Truth" panel in the UI shows exactly what was retrieved for full transparency.

---

## 📁 Project Structure

```text
sports-quiz-agent/
│
├── .env                  # API keys (not committed)
├── requirements.txt      # Dependencies
├── README.md
│
├── data/
│   └── sports_facts.json # Offline knowledge base (36 facts, 6 sports)
│
├── chroma_db/            # Auto-generated vector store (not committed)
│
├── src/
│   ├── __init__.py
│   ├── config.py         # Loads Gemini API key
│   ├── database.py       # ChromaDB setup, populate, query
│   ├── search.py         # Live web search via ddgs
│   └── generator.py      # RAG orchestration + Gemini call
│
└── app.py                # Streamlit dashboard
```

---

## ⚙️ Setup Instructions

### Prerequisites
- Python 3.9–3.11
- A free [Gemini API key](https://aistudio.google.com/apikey) (no credit card required)

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd sports-quiz-agent
```

### 2. Create and activate a virtual environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Add your API key
Create a `.env` file in the project root:
GEMINI_API_KEY=your_key_here

### 5. Run the app
```bash
streamlit run app.py
```
The app opens automatically at `http://localhost:8501`.

---

## 🎮 Usage

1. Type a sport in the sidebar (offline knowledge base covers Cricket, Football, Badminton, Tennis, Basketball, Formula 1 — other sports work too, relying purely on live web search)
2. Choose a difficulty level
3. Click **Generate Fresh Quiz**
4. Answer each question — get instant feedback + explanation
5. Track your live score in the sidebar
6. Click **Generate Fresh Quiz** again anytime for a new, non-repeating quiz

---

## 🔑 Key Design Decisions

- **Gemini over OpenAI**: OpenAI's API has no meaningful free tier; Gemini's free tier is generous and sufficient for this use case, with no card required.
- **`gemini-flash-latest` alias over a pinned model version**: Google frequently deprecates specific model versions (`gemini-2.0-flash`, `gemini-2.5-flash` were both deprecated for new users during development). Using the `-latest` alias future-proofs the app against this churn.
- **Structured JSON output** (`response_mime_type: application/json`) instead of regex-parsing free text — more reliable, avoids the parsing-failure pitfalls of format-dependent text parsing.
- **`ddgs` instead of the deprecated `duckduckgo-search` package** — the original package is unmaintained and was renamed.
- **Free-text sport input instead of a fixed dropdown** — the assignment lists sports as examples, not a hard constraint; the app gracefully falls back to web-search-only grounding for sports outside the offline knowledge base.
- **Explicit anti-source-leakage prompting** — early versions of the generator sometimes asked about *where* a fact came from (e.g., "According to Web Source 2...") instead of the sport itself. The prompt was tightened to forbid this entirely.

---

## 🧪 Known Limitations

- With only 6 facts per sport in the offline knowledge base, heavy repeated regeneration (15+ times) for the same sport may eventually produce overlapping questions.
- `ddgs` is a scraping-based library (no official API), so live search snippets can occasionally be rate-limited or return generic SEO content rather than rich facts — the app falls back gracefully in these cases.

---

## 👩‍💻 Author

Ramya Renganathan