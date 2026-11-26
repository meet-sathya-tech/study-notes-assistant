CHUNK_NOTES_PROMPT = """You are a study assistant.
Extract the important facts, definitions, and concepts from the text below
as concise notes. Do not add information that is not in the text.

TEXT:
{text}
"""

SUMMARY_PROMPT = """You are a study assistant.
Write a clear summary of the study material below.
Use only the given material.

MATERIAL:
{text}
"""

KEY_POINTS_PROMPT = """You are a study assistant.
List the most important key points from the material below as a bullet list,
one short line each. Use only the given material.

MATERIAL:
{text}
"""

FLASHCARDS_PROMPT = """You are a study assistant.
Create {n} flashcards from the material below.
Return ONLY valid JSON, no extra text, in this exact format:
[
  {{"question": "...", "answer": "..."}}
]
Questions should test understanding, and answers should be short.
Use only the given material.

MATERIAL:
{text}
"""

QUIZ_PROMPT = """You are a study assistant.
Create {n} multiple-choice questions from the material below.
Return ONLY valid JSON, no extra text, in this exact format:
[
  {{"question": "...", "options": ["A text", "B text", "C text", "D text"],
    "answer_index": 0, "explanation": "..."}}
]
Rules: exactly 4 options, only one correct, answer_index is the position (0 to 3)
of the correct option. Use only the given material.

MATERIAL:
{text}
"""

# ---------- Style and language options ----------
STYLES = {
    "Simple": "Explain in very simple words, like teaching a 15-year-old. Keep it short: summary of 4-5 sentences, 6-8 key points.",
    "Exam revision": "Focus on definitions, formulas, and likely exam questions. Summary of 5-8 sentences, 8-12 key points.",
    "Detailed": "Be thorough and cover sub-topics. Summary of 10-15 sentences, 12-18 key points.",
}

LANGUAGES = ["English", "Tamil", "Hindi"]

def extras(style: str, language: str) -> str:
    return (
        f"\n\nSTYLE: {STYLES[style]}"
        f"\nLANGUAGE: Write all the content in {language}. "
        f"If you return JSON, keep the JSON keys in English and only the values in {language}."
    )