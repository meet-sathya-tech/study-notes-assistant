import json
import streamlit as st
from llm import ask_llm
from prompts import (CHUNK_NOTES_PROMPT, SUMMARY_PROMPT, KEY_POINTS_PROMPT,
                     FLASHCARDS_PROMPT, QUIZ_PROMPT, extras)

CHUNK_SIZE = 8000
OVERLAP = 300
MAX_CHUNKS = 8


def split_text(text: str) -> list[str]:
    chunks, start = [], 0
    while start < len(text):
        chunks.append(text[start:start + CHUNK_SIZE])
        start += CHUNK_SIZE - OVERLAP
    return chunks


def parse_json(raw: str):
    """Models sometimes wrap JSON in ``` fences. Strip them, then parse."""
    raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return []


@st.cache_data(show_spinner=False)
def condense(text: str) -> str:
    chunks = split_text(text)[:MAX_CHUNKS]
    if len(chunks) == 1:
        return text
    notes = [ask_llm(CHUNK_NOTES_PROMPT.format(text=c)) for c in chunks]
    return "\n".join(notes)


def get_summary(material, style, language):
    return ask_llm(SUMMARY_PROMPT.format(text=material) + extras(style, language))


def get_key_points(material, style, language):
    return ask_llm(KEY_POINTS_PROMPT.format(text=material) + extras(style, language))


def get_flashcards(material, n, style, language):
    raw = ask_llm(FLASHCARDS_PROMPT.format(text=material, n=n) + extras(style, language))
    data = parse_json(raw)
    return [c for c in data if isinstance(c, dict) and "question" in c and "answer" in c]


def get_quiz(material, n, style, language):
    raw = ask_llm(QUIZ_PROMPT.format(text=material, n=n) + extras(style, language))
    clean = []
    for q in parse_json(raw):
        try:
            options = q["options"]
            answer = int(q["answer_index"])
            if len(options) == 4 and 0 <= answer < 4:
                clean.append({
                    "question": q["question"],
                    "options": options,
                    "answer_index": answer,
                    "explanation": q.get("explanation", ""),
                })
        except (KeyError, TypeError, ValueError):
            continue   # skip malformed questions
    return clean


@st.cache_data(show_spinner=False)
def process(text, n_cards, style, language, with_quiz):
    """Cached: the same text + settings never calls the API twice."""
    material = condense(text)
    return {
        "summary": get_summary(material, style, language),
        "points": get_key_points(material, style, language),
        "cards": get_flashcards(material, n_cards, style, language),
        "quiz": get_quiz(material, 5, style, language) if with_quiz else [],
    }