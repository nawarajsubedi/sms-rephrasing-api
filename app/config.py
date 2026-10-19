import os

from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPEN_AI_SECRET")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
