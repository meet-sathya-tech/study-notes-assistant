# 📚 Study Notes Assistant

An AI study assistant that turns PDFs and notes into summaries, key points,
flashcards and quizzes, and lets you chat with your notes with page citations.

**Live demo:** (add link after deployment)  |  **Demo video:** (add link)

## Features
- Upload multiple PDFs or paste text
- Summary styles (Simple, Exam revision, Detailed) and languages (English, Tamil, Hindi)
- Flashcards with Anki CSV export
- Auto-graded multiple-choice quiz
- Chat with your notes using RAG, with page-number sources
- User accounts, saved history, per-user data isolation

## How it works
PDF -> extract text per page -> chunk -> embeddings in ChromaDB
Question -> vector search (top 4 chunks) -> LLM answers using only those chunks -> cite pages

## Tech stack
Python, Streamlit, Groq API (gpt-oss), ChromaDB, SQLite, pypdf

## Run locally
```bash
git clone https://github.com/YOUR-USERNAME/study-notes-assistant.git
cd study-notes-assistant
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```
Create a `.env` file:
```
GROQ_API_KEY=your_key_here
```
Then run `streamlit run app.py`

## Limitations
- Scanned PDFs are not supported yet (no OCR)
- Login is learning-level: no password reset or email verification
- On free hosting, saved data may reset
- Notes are sent to the Groq API, so avoid sensitive documents

## Future work
OCR, chat memory, spaced repetition, agent-style tool calling

