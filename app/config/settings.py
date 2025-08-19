# config/settings.py
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    OPENAI_API_KEY = os.getenv("OPEN_AI_KEY")

settings = Settings()