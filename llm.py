import os
import time
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

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
                time.sleep(2 ** attempt * 3)   # 3s, 6s, 12s, 24s
                continue
            raise