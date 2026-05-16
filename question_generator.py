import os, json, re
from groq import Groq

CATEGORIES = [
    "🌍 General Knowledge",
    "🔬 Science & Technology",
    "🎬 Movies & TV",
    "⚽ Sports",
    "🎵 Music",
    "🏛️ History",
    "🌐 Geography",
    "🎮 Video Games",
    "🍕 Food & Cooking",
    "🐾 Animals & Nature",
]

DIFFICULTY_LEVELS = ["Easy", "Medium", "Hard"]

def generate_questions(category: str, difficulty: str, num_questions: int = 10) -> list:
    api_key = os.environ.get("GROQ_API_KEY", "").strip()
    if not api_key:
        raise ValueError("GROQ_API_KEY not found in secrets.")
    
    client = Groq(api_key=api_key)
    
    prompt = f"""Generate exactly {num_questions} trivia questions about {category} at {difficulty} difficulty.

Return ONLY a valid JSON array. No explanation, no markdown, no extra text.
Each object must have exactly these fields:
{{
  "question": "the question text",
  "options": ["A) option1", "B) option2", "C) option3", "D) option4"],
  "answer": "A) option1",
  "explanation": "brief explanation of why this is correct"
}}

Rules:
- The answer must exactly match one of the options strings
- Make distractors plausible and interesting
- For Easy: well-known facts. Medium: requires some knowledge. Hard: specific/challenging.
- Vary the correct answer position (don't always put it as A)
"""
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=3000,
        temperature=0.7,
    )
    raw = response.choices[0].message.content.strip()
    raw = re.sub(r"^```json\s*", "", raw)
    raw = re.sub(r"^```\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    return json.loads(raw)
