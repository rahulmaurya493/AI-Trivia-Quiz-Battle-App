import time

GAME_CONFIG = {
    "num_questions"    : 10,
    "time_per_question": 20,
    "points": {"Easy": 10, "Medium": 20, "Hard": 30},
    "time_bonus": True,
}

def calculate_score(difficulty, time_taken, time_limit):
    base = GAME_CONFIG["points"][difficulty]
    time_remaining = max(0, time_limit - time_taken)
    time_bonus = int((time_remaining / time_limit) * base * 0.5)
    return base + time_bonus

def get_grade(score, total_questions, difficulty):
    max_score = GAME_CONFIG["points"][difficulty] * total_questions
    pct = (score / max_score * 100) if max_score > 0 else 0
    if pct >= 90:   return {"grade": "S", "emoji": "🏆", "msg": "Legendary! You are a trivia master!",   "color": "#FFD700"}
    elif pct >= 75: return {"grade": "A", "emoji": "🥇", "msg": "Excellent! You really know your stuff!", "color": "#4CAF50"}
    elif pct >= 60: return {"grade": "B", "emoji": "🥈", "msg": "Good job! Solid performance!",           "color": "#2196F3"}
    elif pct >= 40: return {"grade": "C", "emoji": "🥉", "msg": "Not bad! Keep practicing!",              "color": "#FF9800"}
    else:           return {"grade": "D", "emoji": "😅", "msg": "Better luck next time! Try again!",      "color": "#F44336"}

def init_game_state(questions, category, difficulty):
    return {
        "questions"      : questions,
        "category"       : category,
        "difficulty"     : difficulty,
        "current_index"  : 0,
        "score"          : 0,
        "correct_count"  : 0,
        "answers_given"  : [],
        "question_start" : time.time(),
        "game_phase"     : "playing",
    }

def submit_answer(state, chosen_option):
    q          = state["questions"][state["current_index"]]
    time_taken = time.time() - state["question_start"]
    is_correct = (chosen_option == q["answer"])
    points     = 0
    if is_correct:
        points = calculate_score(state["difficulty"], time_taken, GAME_CONFIG["time_per_question"])
        state["score"]         += points
        state["correct_count"] += 1
    state["answers_given"].append({
        "question"   : q["question"],
        "chosen"     : chosen_option,
        "correct"    : q["answer"],
        "explanation": q["explanation"],
        "is_correct" : is_correct,
        "points"     : points,
        "time_taken" : round(time_taken, 1),
    })
    state["current_index"] += 1
    state["question_start"] = time.time()
    if state["current_index"] >= len(state["questions"]):
        state["game_phase"] = "result"
    return {"is_correct": is_correct, "points": points, "correct_answer": q["answer"]}
