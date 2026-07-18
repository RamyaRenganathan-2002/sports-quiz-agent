import streamlit as st
from src.generator import compile_quiz_data
from src.database import setup_and_populate_db

# 1. Warm up and initialize the vector DB with offline facts on startup (runs once, cached)
@st.cache_resource
def prepare_knowledge_base():
    setup_and_populate_db()

prepare_knowledge_base()

# 2. Page configuration
st.set_page_config(page_title="Sports Quiz Agent", page_icon="🏆", layout="centered")

st.title("🏆 AI-Powered Sports Quiz Generator")
st.write("Generate factually grounded sports quizzes using RAG (ChromaDB + Live Web Search + Gemini).")

# 3. Sidebar controls
st.sidebar.header("Quiz Settings")
sport_choice = st.sidebar.selectbox(
    "Select Sport",
    ["Cricket", "Football", "Badminton", "Tennis", "Basketball", "Formula 1"]
)
difficulty = st.sidebar.select_slider("Select Difficulty", options=["Easy", "Medium", "Hard"])

# 4. Session state
if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = None
    st.session_state.quiz_context = None
    st.session_state.quiz_sport = None
    st.session_state.quiz_difficulty = None
    st.session_state.quiz_round = 0  # increments each generation, forces radio widgets to reset
    st.session_state.asked_questions = []  # tracks all questions asked so far, to avoid repeats

# 5. Generate button
if st.sidebar.button("Generate Fresh Quiz", use_container_width=True):
    with st.spinner("Retrieving historical facts & scouring the live web..."):
        try:
            quiz_data, context_used = compile_quiz_data(
                sport_choice, difficulty,
                previous_questions=st.session_state.asked_questions
            )
            st.session_state.quiz_data = quiz_data
            st.session_state.quiz_context = context_used
            st.session_state.quiz_sport = sport_choice
            st.session_state.quiz_difficulty = difficulty
            st.session_state.quiz_round += 1  # bump round so radio keys change -> fresh selections
            st.session_state.asked_questions.extend([q["question"] for q in quiz_data])
            st.success("Quiz generated successfully!")
        except Exception as e:
            st.error(f"Failed to generate quiz: {e}")

# 6. Display the quiz
if st.session_state.quiz_data:
    total_questions = len(st.session_state.quiz_data)
    answered_count = 0
    correct_count = 0

    st.subheader(f"📋 {st.session_state.quiz_sport} Quiz ({st.session_state.quiz_difficulty})")

    # First pass: render questions and collect answers
    user_selections = []
    for i, q in enumerate(st.session_state.quiz_data):
        st.markdown(f"**Q{i+1}. {q['question']}**")

        option_labels = [f"{key}) {value}" for key, value in q["options"].items()]
        selected = st.radio(
            "Choose your answer:",
            option_labels,
            key=f"q_{st.session_state.quiz_round}_{i}",  # round-scoped key = resets on regenerate
            index=None,
            label_visibility="collapsed"
        )
        user_selections.append(selected)

        if selected:
            answered_count += 1
            selected_letter = selected.split(")")[0]
            correct_letter = q["correct_answer"]

            if selected_letter == correct_letter:
                correct_count += 1
                st.success(f"✅ Correct! **{correct_letter}) {q['options'][correct_letter]}**")
            else:
                st.error(f"❌ Incorrect. Correct answer: **{correct_letter}) {q['options'][correct_letter]}**")

            st.info(f"💡 {q['explanation']}")

        st.divider()

    # 7. Progress + live score tracker (sidebar, updates as user answers)
    st.sidebar.divider()
    st.sidebar.subheader("📊 Progress")
    st.sidebar.progress(answered_count / total_questions if total_questions else 0)
    st.sidebar.write(f"Answered: {answered_count} / {total_questions}")

    if answered_count > 0:
        st.sidebar.metric("Score", f"{correct_count} / {answered_count}")

    if answered_count == total_questions:
        pct = round((correct_count / total_questions) * 100)
        st.sidebar.success(f"🎉 Quiz complete! Final score: {pct}%")

    # 8. Ground truth inspector
    with st.expander("🔍 Inspect Ground Truth (RAG Context Used)"):
        st.code(st.session_state.quiz_context, language="markdown")
else:
    st.info("👈 Select a sport and difficulty, then click **Generate Fresh Quiz** to begin.")