import os
import time
import streamlit as st
from dotenv import load_dotenv
from groq import Groq

load_dotenv()


def _get_key():
    key = os.getenv("GROQ_API_KEY")          # local: from .env
    if key:
        return key
    try:
        return st.secrets["GROQ_API_KEY"]    # online: from Streamlit Secrets
    except Exception:
        return None


client = Groq(api_key=_get_key())

MODEL = "openai/gpt-oss-20b"
MAX_RETRIES = 5


def ask_llm(prompt: str) -> str:
    for attempt in range(MAX_RETRIES):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.choices[0].message.content
        except Exception as e:
            msg = str(e)
            temporary = any(code in msg for code in ["429", "502", "503", "rate_limit"])
            if temporary and attempt < MAX_RETRIES - 1:
                time.sleep(2 ** attempt * 3)
                continue
            raise