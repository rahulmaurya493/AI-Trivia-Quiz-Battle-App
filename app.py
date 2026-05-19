import os, time, json
import streamlit as st
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

from question_generator import CATEGORIES, DIFFICULTY_LEVELS, generate_questions
from game_logic import GAME_CONFIG, init_game_state, submit_answer, get_grade

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="🎮 AI Trivia Quiz",
    page_icon="🧠",
    layout="centered",
)

# ── Supabase client ───────────────────────────────────────────────────────────
@st.cache_resource
def get_supabase():
    url = os.environ.get("SUPABASE_URL") or st.secrets.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY") or st.secrets.get("SUPABASE_KEY")
    return create_client(url, key)

def load_leaderboard():
    try:
        sb = get_supabase()
        res = sb.table("leaderboard").select("*").order("score", desc=True).limit(10).execute()
        return res.data
    except:
        return []

def save_score(name, score, correct, total, category, difficulty, grade):
    try:
        sb = get_supabase()
        sb.table("leaderboard").insert({
            "name": name, "score": score, "correct": correct,
            "total": total, "category": category,
            "difficulty": difficulty, "grade": grade
        }).execute()
    except Exception as e:
        st.warning(f"Could not save score: {e}")

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@400;500;600;700&display=swap');

  html, body, [data-testid="stAppViewContainer"] {
    background: #040610 !important;
    color: #e0e8ff !important;
  }

  [data-testid="stAppViewContainer"] {
    background:
      radial-gradient(ellipse 80% 40% at 50% 0%, rgba(99,40,255,0.18) 0%, transparent 70%),
      radial-gradient(ellipse 60% 30% at 80% 100%, rgba(0,230,180,0.10) 0%, transparent 60%),
      #040610 !important;
  }

  [data-testid="block-container"] { padding-top: 2rem !important; }

  body, p, li, span, div, label {
    font-family: 'Rajdhani', sans-serif !important;
    letter-spacing: 0.02em;
  }

  h1, h2, h3 {
    font-family: 'Orbitron', monospace !important;
    letter-spacing: 0.06em;
  }

  .hero { text-align: center; padding: 2.5rem 0 1.5rem; }

  .hero h1 {
    font-family: 'Orbitron', monospace !important;
    font-size: 2.8rem;
    font-weight: 900;
    margin-bottom: 0.4rem;
    background: linear-gradient(90deg, #00e6b4, #7b5cff, #ff4fa3);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    filter: drop-shadow(0 0 24px rgba(123,92,255,0.5));
    animation: flicker 4s infinite alternate;
  }

  @keyframes flicker {
    0%, 95%, 100% { opacity: 1; }
    96% { opacity: 0.85; }
    97% { opacity: 1; }
    98% { opacity: 0.9; }
  }

  .hero p {
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 1rem;
    color: #7b8cc8;
    letter-spacing: 0.12em;
    text-transform: uppercase;
  }

  hr {
    border: none !important;
    border-top: 1px solid rgba(123,92,255,0.25) !important;
    margin: 1.5rem 0 !important;
  }

  .q-card {
    background: linear-gradient(135deg, rgba(10,12,40,0.95), rgba(18,10,50,0.90));
    border: 1px solid rgba(123,92,255,0.5);
    border-left: 4px solid #7b5cff;
    border-radius: 12px;
    padding: 1.6rem 2rem;
    margin: 1rem 0;
    position: relative;
    overflow: hidden;
    box-shadow: 0 0 30px rgba(123,92,255,0.15), inset 0 0 60px rgba(0,0,0,0.4);
  }

  .q-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, #7b5cff, #00e6b4, transparent);
  }

  .q-number {
    font-family: 'Orbitron', monospace !important;
    font-size: 0.7rem;
    color: #7b5cff;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin-bottom: 0.7rem;
  }

  .q-text {
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 1.3rem;
    font-weight: 600;
    line-height: 1.55;
    color: #dde6ff;
    letter-spacing: 0.03em;
  }

  .correct-box {
    background: linear-gradient(135deg, rgba(0,230,150,0.08), rgba(0,180,100,0.05));
    border: 1px solid rgba(0,230,150,0.4);
    border-left: 4px solid #00e696;
    padding: 1rem 1.2rem;
    border-radius: 8px;
    margin: 0.5rem 0;
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 1.05rem;
    font-weight: 600;
    color: #00e696;
    letter-spacing: 0.04em;
  }

  .wrong-box {
    background: linear-gradient(135deg, rgba(255,60,100,0.08), rgba(180,20,60,0.05));
    border: 1px solid rgba(255,60,100,0.4);
    border-left: 4px solid #ff3c64;
    padding: 1rem 1.2rem;
    border-radius: 8px;
    margin: 0.5rem 0;
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 1.05rem;
    font-weight: 600;
    color: #ff6b8a;
    letter-spacing: 0.04em;
  }

  .score-big {
    font-family: 'Orbitron', monospace !important;
    font-size: 4.5rem;
    font-weight: 900;
    text-align: center;
    background: linear-gradient(135deg, #00e6b4, #7b5cff, #ff4fa3);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    filter: drop-shadow(0 0 20px rgba(123,92,255,0.6));
    margin: 1.5rem 0 0.5rem;
    animation: pulse-glow 2s ease-in-out infinite;
  }

  @keyframes pulse-glow {
    0%, 100% { filter: drop-shadow(0 0 20px rgba(123,92,255,0.6)); }
    50%       { filter: drop-shadow(0 0 35px rgba(0,230,180,0.7)); }
  }

  .stat-row {
    display: flex;
    justify-content: center;
    gap: 1.2rem;
    margin: 1.2rem 0;
    flex-wrap: wrap;
  }

  .stat-box {
    text-align: center;
    background: rgba(10,12,40,0.8);
    border: 1px solid rgba(123,92,255,0.3);
    padding: 1rem 1.4rem;
    border-radius: 12px;
    min-width: 90px;
    position: relative;
    overflow: hidden;
  }

  .stat-box::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, #7b5cff, #00e6b4);
  }

  .stat-num {
    font-family: 'Orbitron', monospace !important;
    font-size: 1.8rem;
    font-weight: 700;
    color: #dde6ff;
  }

  .stat-lbl {
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 0.75rem;
    color: #7b8cc8;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-top: 2px;
  }

  .lb-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.75rem 1rem;
    border-radius: 10px;
    margin: 0.35rem 0;
    background: rgba(10,12,40,0.75);
    border: 1px solid rgba(123,92,255,0.2);
    transition: border-color 0.2s;
  }

  .lb-row:hover { border-color: rgba(123,92,255,0.5); }

  .lb-rank  { font-size: 1.3rem; width: 40px; }

  .lb-name {
    font-family: 'Rajdhani', sans-serif !important;
    font-weight: 700;
    font-size: 1rem;
    color: #dde6ff;
    flex: 1;
    letter-spacing: 0.04em;
  }

  .lb-score {
    font-family: 'Orbitron', monospace !important;
    font-weight: 700;
    color: #7b5cff;
    font-size: 1rem;
  }

  .lb-meta {
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 0.78rem;
    color: #7b8cc8;
    margin-left: 1rem;
    letter-spacing: 0.03em;
  }

  div[data-testid="stButton"] > button {
    width: 100% !important;
    border-radius: 8px !important;
    padding: 0.65rem 1rem !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 1.05rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    background: rgba(10,12,40,0.8) !important;
    border: 1px solid rgba(123,92,255,0.5) !important;
    color: #b0bcff !important;
    transition: all 0.18s ease !important;
  }

  div[data-testid="stButton"] > button:hover {
    background: rgba(123,92,255,0.15) !important;
    border-color: #7b5cff !important;
    color: #ffffff !important;
    box-shadow: 0 0 20px rgba(123,92,255,0.35) !important;
    transform: translateY(-1px) !important;
  }

  div[data-testid="stButton"] > button[kind="primary"] {
    background: linear-gradient(135deg, #7b5cff, #5b3cdd) !important;
    border-color: #9b7cff !important;
    color: #ffffff !important;
    box-shadow: 0 0 18px rgba(123,92,255,0.4) !important;
  }

  div[data-testid="stButton"] > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #9b7cff, #7b5cff) !important;
    box-shadow: 0 0 30px rgba(123,92,255,0.6) !important;
    transform: translateY(-2px) !important;
  }

  [data-testid="metric-container"] {
    background: rgba(10,12,40,0.75) !important;
    border: 1px solid rgba(123,92,255,0.25) !important;
    border-radius: 10px !important;
    padding: 0.8rem 1rem !important;
  }

  [data-testid="metric-container"] label {
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 0.75rem !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    color: #7b8cc8 !important;
  }

  [data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-family: 'Orbitron', monospace !important;
    font-size: 1.5rem !important;
    font-weight: 700 !important;
    color: #dde6ff !important;
  }

  [data-testid="stProgressBar"] > div {
    background: rgba(123,92,255,0.15) !important;
    border-radius: 4px !important;
    height: 6px !important;
  }

  [data-testid="stProgressBar"] > div > div {
    background: linear-gradient(90deg, #7b5cff, #00e6b4) !important;
    border-radius: 4px !important;
    box-shadow: 0 0 10px rgba(0,230,180,0.4) !important;
  }

  [data-testid="stAlert"] {
    border-radius: 8px !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-weight: 500 !important;
    letter-spacing: 0.02em !important;
  }

  input[type="text"], .stTextInput input {
    background: rgba(10,12,40,0.8) !important;
    border: 1px solid rgba(123,92,255,0.35) !important;
    border-radius: 8px !important;
    color: #dde6ff !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 1rem !important;
  }

  input[type="text"]:focus, .stTextInput input:focus {
    border-color: #7b5cff !important;
    box-shadow: 0 0 12px rgba(123,92,255,0.3) !important;
  }

  [data-testid="stSelectbox"] > div > div {
    background: rgba(10,12,40,0.8) !important;
    border: 1px solid rgba(123,92,255,0.35) !important;
    border-radius: 8px !important;
    color: #dde6ff !important;
    font-family: 'Rajdhani', sans-serif !important;
  }

  [data-testid="stExpander"] {
    background: rgba(10,12,40,0.6) !important;
    border: 1px solid rgba(123,92,255,0.2) !important;
    border-radius: 8px !important;
    font-family: 'Rajdhani', sans-serif !important;
  }

  .stTextInput label, .stSelectbox label, .stSlider label {
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 0.9rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
    color: #8892c8 !important;
  }

  [data-testid="stSidebar"]    { display: none !important; }
  [data-testid="collapsedControl"] { display: none !important; }

  .timer-glow { font-family: 'Orbitron', monospace; letter-spacing: 0.08em; }
</style>
""", unsafe_allow_html=True)

# ── Session State ─────────────────────────────────────────────────────────────
for k, v in [
    ("game",        None),
    ("phase",       "home"),
    ("feedback",    None),
    ("player_name", ""),
]:
    if k not in st.session_state:
        st.session_state[k] = v

# ── Check API key ─────────────────────────────────────────────────────────────
groq_key = os.environ.get("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY", "")
if groq_key:
    os.environ["GROQ_API_KEY"] = groq_key
else:
    st.error("❌ GROQ_API_KEY missing from Streamlit Secrets.")
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# SCREEN 1 — HOME
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.phase == "home":
    st.markdown("""
    <div class='hero'>
      <h1>🧠 AI Trivia Quiz</h1>
      <p>Powered by Groq + Llama 3.3 &nbsp;|&nbsp; Fresh questions every game</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    name       = st.text_input("👤 Your name", placeholder="Enter your name...", value=st.session_state.player_name)
    category   = st.selectbox("📚 Category",   CATEGORIES)
    difficulty = st.selectbox("⚡ Difficulty", DIFFICULTY_LEVELS)
    num_q      = st.slider("❓ Number of questions", 5, 15, 10)

    pts = GAME_CONFIG["points"][difficulty]
    st.info(f"🎯 Each correct answer = **{pts} pts** + time bonus  |  ⏱️ {GAME_CONFIG['time_per_question']}s per question")

    if st.button("🚀 Start Quiz!", type="primary"):
        if not name.strip():
            st.error("Please enter your name.")
        else:
            st.session_state.player_name   = name.strip()
            st.session_state._start_params = (category, difficulty, num_q)
            st.session_state.phase         = "loading"
            st.rerun()

    # ── Leaderboard ───────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 🏆 Global Leaderboard")
    board = load_leaderboard()
    if board:
        medals = ["🥇", "🥈", "🥉"]
        for i, entry in enumerate(board, 1):
            medal = medals[i-1] if i <= 3 else f"{i}."
            diff_color = {"Easy": "#00e696", "Medium": "#ffaa00", "Hard": "#ff3c64"}.get(entry.get("difficulty",""), "#7b8cc8")
            grade_emoji = {"S":"🏆","A":"🥇","B":"🥈","C":"🥉","D":"😅"}.get(entry.get("grade",""), "")
            st.markdown(f"""
            <div class='lb-row'>
              <div class='lb-rank'>{medal}</div>
              <div class='lb-name'>{entry['name']} {grade_emoji}</div>
              <div class='lb-score'>{entry['score']} pts</div>
              <div class='lb-meta'>{entry.get('correct',0)}/{entry.get('total',0)} correct &nbsp;|&nbsp;
                <span style='color:{diff_color}'>{entry.get('difficulty','')}</span> &nbsp;|&nbsp;
                {entry.get('category','')}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("<p style='color:#7b8cc8; font-family:Rajdhani,sans-serif; letter-spacing:0.05em;'>*No scores yet — be the first to play!* 🎮</p>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# SCREEN 2 — LOADING
# ─────────────────────────────────────────────────────────────────────────────
elif st.session_state.phase == "loading":
    cat, diff, num_q = st.session_state._start_params
    st.markdown(f"### 🤖 Generating {num_q} questions about **{cat}** at **{diff}** difficulty...")
    st.markdown("*Llama 3.3 is crafting fresh questions just for you — won't take long!*")
    with st.spinner("Thinking..."):
        questions = generate_questions(cat, diff, num_q)
        st.session_state.game     = init_game_state(questions, cat, diff)
        st.session_state.feedback = None
        st.session_state.phase    = "playing"
    st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# SCREEN 3 — PLAYING / FEEDBACK
# ─────────────────────────────────────────────────────────────────────────────
elif st.session_state.phase in ("playing", "feedback"):
    g     = st.session_state.game
    total = len(g["questions"])
    idx   = g["current_index"]

    c1, c2, c3 = st.columns(3)
    c1.metric("Score",    g["score"])
    c2.metric("Correct",  f"{g['correct_count']} / {idx}")
    c3.metric("Question", f"{min(idx+1, total)} / {total}")
    st.progress(idx / total if total else 0)

    if st.session_state.phase == "feedback" and st.session_state.feedback:
        fb  = st.session_state.feedback
        ans = g["answers_given"][-1]
        if fb["is_correct"]:
            st.markdown(f"<div class='correct-box'>✅ &nbsp;CORRECT! &nbsp;+{fb['points']} points &nbsp;|&nbsp; ⏱️ {ans['time_taken']}s</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='wrong-box'>❌ &nbsp;WRONG! &nbsp;Correct answer: <b>{fb['correct_answer']}</b></div>", unsafe_allow_html=True)
        st.info(f"💡 {ans['explanation']}")

        label = "Next Question ▶" if idx < total else "See Results 🏆"
        if st.button(label, type="primary"):
            if g["game_phase"] == "result":
                st.session_state.phase = "result"
            else:
                st.session_state.phase    = "playing"
                st.session_state.feedback = None
            st.rerun()

    elif st.session_state.phase == "playing" and idx < total:
        q = g["questions"][idx]
        st.markdown(f"""
        <div class='q-card'>
          <div class='q-number'>Question {idx+1} of {total} &nbsp;•&nbsp; {g['category']} &nbsp;•&nbsp; {g['difficulty']}</div>
          <div class='q-text'>{q['question']}</div>
        </div>
        """, unsafe_allow_html=True)

        for opt in q["options"]:
            if st.button(opt, key=f"opt_{idx}_{opt}"):
                result = submit_answer(g, opt)
                st.session_state.feedback = result
                st.session_state.phase    = "feedback"
                st.rerun()

        elapsed   = time.time() - g["question_start"]
        remaining = max(0, GAME_CONFIG["time_per_question"] - elapsed)
        color     = "#00e696" if remaining > 10 else ("#ffaa00" if remaining > 5 else "#ff3c64")
        st.markdown(f"<p class='timer-glow' style='color:{color};font-weight:700;font-size:1.05rem;'>⏱ {remaining:.0f}s remaining</p>", unsafe_allow_html=True)

        if remaining <= 0:
            submit_answer(g, "")
            st.session_state.feedback = {"is_correct": False, "points": 0, "correct_answer": q["answer"]}
            st.session_state.phase    = "feedback"
            st.rerun()

        time.sleep(1)
        st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# SCREEN 4 — RESULTS
# ─────────────────────────────────────────────────────────────────────────────
elif st.session_state.phase == "result":
    g     = st.session_state.game
    total = len(g["questions"])
    grade = get_grade(g["score"], total, g["difficulty"])

    st.markdown(f"<div class='score-big'>{grade['emoji']} {g['score']} pts</div>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align:center; font-family:Rajdhani,sans-serif; color:#b0bcff; letter-spacing:0.05em;'>{grade['msg']} (Grade {grade['grade']})</h3>", unsafe_allow_html=True)

    st.markdown(f"""
    <div class='stat-row'>
      <div class='stat-box'><div class='stat-num'>{g['correct_count']}</div><div class='stat-lbl'>Correct</div></div>
      <div class='stat-box'><div class='stat-num'>{total - g['correct_count']}</div><div class='stat-lbl'>Wrong</div></div>
      <div class='stat-box'><div class='stat-num'>{round(g['correct_count']/total*100)}%</div><div class='stat-lbl'>Accuracy</div></div>
    </div>
    """, unsafe_allow_html=True)

    # Save to Supabase
    save_score(
        st.session_state.player_name,
        g["score"], g["correct_count"], total,
        g["category"], g["difficulty"], grade["grade"]
    )
    st.success("✅ Score saved to global leaderboard!")

    st.markdown("---")
    st.markdown("### 📋 Answer Review")
    for i, ans in enumerate(g["answers_given"], 1):
        icon = "✅" if ans["is_correct"] else "❌"
        with st.expander(f"{icon} Q{i}: {ans['question']} ({ans['time_taken']}s)"):
            st.write(f"**Your answer:** {ans['chosen'] or '(time ran out)'}")
            if not ans["is_correct"]:
                st.write(f"**Correct answer:** {ans['correct']}")
            st.info(f"💡 {ans['explanation']}")
            if ans["is_correct"]:
                st.success(f"Points earned: {ans['points']}")

    st.markdown("---")
    c1, c2 = st.columns(2)
    if c1.button("🔄 Play Again", type="primary"):
        st.session_state.phase    = "home"
        st.session_state.game     = None
        st.session_state.feedback = None
        st.rerun()
    if c2.button("🏠 Home"):
        st.session_state.phase    = "home"
        st.session_state.game     = None
        st.session_state.feedback = None
        st.rerun()
