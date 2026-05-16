app_code = '''
import os, sys, time
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(__file__))

from question_generator import CATEGORIES, DIFFICULTY_LEVELS, generate_questions
from game_logic import GAME_CONFIG, init_game_state, submit_answer, get_grade

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="🎮 AI Trivia Quiz",
    page_icon="🧠",
    layout="centered",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  .hero { text-align:center; padding:2rem 0 1rem; }
  .hero h1 { font-size:3rem; margin-bottom:0; }
  .hero p  { font-size:1.1rem; opacity:.75; }

  .q-card {
    background:linear-gradient(135deg,#1a1a2e,#16213e);
    color:white; border-radius:16px;
    padding:1.5rem 2rem; margin:1rem 0;
  }
  .q-number { font-size:.85rem; opacity:.6; margin-bottom:.5rem; }
  .q-text   { font-size:1.25rem; font-weight:600; line-height:1.5; }

  .opt-btn {
    width:100%; text-align:left; padding:.75rem 1.25rem;
    margin:.3rem 0; border-radius:10px; border:2px solid #e0e0e0;
    background:white; cursor:pointer; font-size:1rem;
    transition:all .2s;
  }
  .opt-btn:hover { background:#f0f4ff; border-color:#667eea; }

  .correct-box {
    background:#e8f5e9; border-left:5px solid #4CAF50;
    padding:1rem; border-radius:8px; margin:.5rem 0;
  }
  .wrong-box {
    background:#ffebee; border-left:5px solid #F44336;
    padding:1rem; border-radius:8px; margin:.5rem 0;
  }

  .score-big {
    font-size:4rem; font-weight:700; text-align:center;
    background:linear-gradient(135deg,#667eea,#764ba2);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
  }
  .stat-row  { display:flex; justify-content:center; gap:2rem; margin:1rem 0; }
  .stat-box  {
    text-align:center; background:#f8f9ff;
    padding:1rem 1.5rem; border-radius:12px; min-width:90px;
  }
  .stat-num  { font-size:1.8rem; font-weight:700; }
  .stat-lbl  { font-size:.8rem; opacity:.6; }

  div[data-testid="stButton"] > button {
    width:100%; border-radius:10px; padding:.6rem 1rem;
    font-size:1rem; font-weight:500;
  }
</style>
""", unsafe_allow_html=True)


# ── Session State Init ────────────────────────────────────────────────────────
for k, v in [
    ("game",        None),
    ("phase",       "home"),     # home | loading | playing | feedback | result
    ("feedback",    None),
    ("leaderboard", []),
    ("player_name", ""),
]:
    if k not in st.session_state:
        st.session_state[k] = v


# ─────────────────────────────────────────────────────────────────────────────
# SCREEN 1 — HOME
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.phase == "home":
    st.markdown("""
    <div class=\'hero\'>
      <h1>🧠 AI Trivia Quiz</h1>
      <p>Powered by Groq + Llama 3.3 &nbsp;|&nbsp; Fresh questions every game</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # API key
    api_key = st.text_input(
        "🔑 Groq API Key",
        value=os.environ.get("GROQ_API_KEY", ""),
        type="password",
        placeholder="gsk_...",
        help="Free key at console.groq.com"
    )
    if api_key:
        os.environ["GROQ_API_KEY"] = api_key

    name = st.text_input("👤 Your name", placeholder="Enter your name...",
                         value=st.session_state.player_name)
    category   = st.selectbox("📚 Category",   CATEGORIES)
    difficulty = st.selectbox("⚡ Difficulty", DIFFICULTY_LEVELS)
    num_q      = st.slider("❓ Number of questions", 5, 15, 10)

    pts = GAME_CONFIG["points"][difficulty]
    st.info(f"🎯  Each correct answer = **{pts} pts** + time bonus  |  ⏱️ {GAME_CONFIG[\'time_per_question\']}s per question")

    if st.button("🚀 Start Quiz!", type="primary"):
        if not os.environ.get("GROQ_API_KEY"):
            st.error("Please enter your Groq API key first.")
        elif not name.strip():
            st.error("Please enter your name.")
        else:
            st.session_state.player_name = name.strip()
            st.session_state._start_params = (category, difficulty, num_q)
            st.session_state.phase = "loading"
            st.rerun()

    # Leaderboard
    if st.session_state.leaderboard:
        st.markdown("---")
        st.markdown("### 🏆 Leaderboard")
        board = sorted(st.session_state.leaderboard, key=lambda x: x["score"], reverse=True)[:10]
        for i, entry in enumerate(board, 1):
            medal = ["🥇","🥈","🥉"].pop(0) if i <= 3 else f"{i}."
            st.markdown(f"{medal} **{entry[\'name\']}** — {entry[\'score\']} pts | {entry[\'category\']} | {entry[\'difficulty\']} | {entry[\'correct\']}/{entry[\'total\']} correct")


# ─────────────────────────────────────────────────────────────────────────────
# SCREEN 2 — LOADING
# ─────────────────────────────────────────────────────────────────────────────
elif st.session_state.phase == "loading":
    cat, diff, num_q = st.session_state._start_params
    st.markdown(f"### 🤖 Generating {num_q} questions about **{cat}** at **{diff}** difficulty...")
    st.markdown("*Llama 3.3 is crafting fresh questions just for you — won\'t take long!*")
    with st.spinner("Thinking..."):
        questions = generate_questions(cat, diff, num_q)
        st.session_state.game = init_game_state(questions, cat, diff)
        st.session_state.feedback = None
        st.session_state.phase = "playing"
    st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# SCREEN 3 — PLAYING
# ─────────────────────────────────────────────────────────────────────────────
elif st.session_state.phase in ("playing", "feedback"):
    g = st.session_state.game
    total = len(g["questions"])
    idx   = g["current_index"]

    # Header stats
    c1, c2, c3 = st.columns(3)
    c1.metric("Score",    g["score"])
    c2.metric("Correct",  f"{g[\'correct_count\']} / {idx}")
    c3.metric("Question", f"{min(idx+1, total)} / {total}")

    # Progress bar
    st.progress(idx / total if total else 0)

    # ── FEEDBACK MODE (just answered) ─────────────────────────────────────────
    if st.session_state.phase == "feedback" and st.session_state.feedback:
        fb  = st.session_state.feedback
        ans = g["answers_given"][-1]

        if fb["is_correct"]:
            st.markdown(f"<div class=\'correct-box\'>✅ <b>Correct!</b> +{fb[\'points\']} points | ⏱️ {ans[\'time_taken\']}s</div>",
                        unsafe_allow_html=True)
        else:
            st.markdown(f"<div class=\'wrong-box\'>❌ <b>Wrong!</b> Correct answer: <b>{fb[\'correct_answer\']}}</b></div>",
                        unsafe_allow_html=True)

        st.info(f"💡 {ans[\'explanation\']}")

        label = "Next Question ▶" if idx < total else "See Results 🏆"
        if st.button(label, type="primary"):
            if g["game_phase"] == "result":
                st.session_state.phase = "result"
            else:
                st.session_state.phase = "playing"
                st.session_state.feedback = None
            st.rerun()

    # ── QUESTION MODE ─────────────────────────────────────────────────────────
    elif st.session_state.phase == "playing" and idx < total:
        q = g["questions"][idx]

        st.markdown(f"""
        <div class=\'q-card\'>
          <div class=\'q-number\'>Question {idx+1} of {total} &nbsp;•&nbsp; {g[\'category\']} &nbsp;•&nbsp; {g[\'difficulty\']}</div>
          <div class=\'q-text\'>{q[\'question\']}</div>
        </div>
        """, unsafe_allow_html=True)

        for opt in q["options"]:
            if st.button(opt, key=f"opt_{idx}_{opt}"):
                result = submit_answer(g, opt)
                st.session_state.feedback = result
                st.session_state.phase    = "feedback"
                st.rerun()

        # Timer display
        elapsed = time.time() - g["question_start"]
        remaining = max(0, GAME_CONFIG["time_per_question"] - elapsed)
        color = "green" if remaining > 10 else ("orange" if remaining > 5 else "red")
        st.markdown(f"<p style=\'color:{color};font-weight:600;\'>⏱️ {remaining:.0f}s remaining</p>",
                    unsafe_allow_html=True)

        # Auto-submit if time runs out
        if remaining <= 0:
            result = submit_answer(g, "")
            st.session_state.feedback = {"is_correct": False, "points": 0,
                                         "correct_answer": g["questions"][idx]["answer"]}
            st.session_state.feedback["is_correct"] = False
            st.session_state.phase = "feedback"
            st.rerun()

        time.sleep(1)
        st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# SCREEN 4 — RESULTS
# ─────────────────────────────────────────────────────────────────────────────
elif st.session_state.phase == "result":
    g = st.session_state.game
    total  = len(g["questions"])
    grade  = get_grade(g["score"], total, g["difficulty"])

    st.markdown(f"<div class=\'score-big\'>{grade[\'emoji\']} {g[\'score\']} pts</div>",
                unsafe_allow_html=True)
    st.markdown(f"<h3 style=\'text-align:center\'>{grade[\'msg\']} (Grade {grade[\'grade\']})</h3>",
                unsafe_allow_html=True)

    st.markdown(f"""
    <div class=\'stat-row\'>
      <div class=\'stat-box\'><div class=\'stat-num\'>{g[\'correct_count\']}</div><div class=\'stat-lbl\'>Correct</div></div>
      <div class=\'stat-box\'><div class=\'stat-num\'>{total - g[\'correct_count\']}</div><div class=\'stat-lbl\'>Wrong</div></div>
      <div class=\'stat-box\'><div class=\'stat-num\'>{round(g[\'correct_count\']/total*100)}%</div><div class=\'stat-lbl\'>Accuracy</div></div>
    </div>
    """, unsafe_allow_html=True)

    # Save to leaderboard
    already_saved = any(
        e["name"] == st.session_state.player_name and e["score"] == g["score"]
        for e in st.session_state.leaderboard
    )
    if not already_saved:
        st.session_state.leaderboard.append({
            "name":       st.session_state.player_name,
            "score":      g["score"],
            "correct":    g["correct_count"],
            "total":      total,
            "category":   g["category"],
            "difficulty": g["difficulty"],
            "grade":      grade["grade"],
        })

    # Answer Review
    st.markdown("---")
    st.markdown("### 📋 Answer Review")
    for i, ans in enumerate(g["answers_given"], 1):
        icon = "✅" if ans["is_correct"] else "❌"
        with st.expander(f"{icon} Q{i}: {ans[\'question\']} ({ans[\'time_taken\']}s)"):
            st.write(f"**Your answer:** {ans[\'chosen\'] or \'(time ran out)\'}")  
            if not ans["is_correct"]:
                st.write(f"**Correct answer:** {ans[\'correct\']}")
            st.info(f"💡 {ans[\'explanation\']}")
            if ans["is_correct"]:
                st.success(f"Points earned: {ans[\'points\']}")

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
'''

with open('trivia_app/app.py', 'w') as f:
    f.write(app_code)

print('✅ trivia_app/app.py written!')
print()
print('Now run this in your terminal:')
print('   streamlit run trivia_app/app.py')
