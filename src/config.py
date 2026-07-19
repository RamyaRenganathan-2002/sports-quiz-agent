import os
from dotenv import load_dotenv

# Load variables from .env file into system environment
load_dotenv()

# Centralized configuration values
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Model name — using Gemini's fast, free-tier-friendly model
GEMINI_MODEL = "gemini-flash-latest"

if not GEMINI_API_KEY:
    print("[WARNING]: GEMINI_API_KEY is missing. Check your .env file setup!")