import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
ENV_PATH = Path("/opt/interview-mentor/.env")
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)

APP_NAME = os.getenv("APP_NAME", "The Interview Mentor AI")
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8060"))
BASE_PATH = os.getenv("BASE_PATH", "/interview").rstrip("/")

SECRET_KEY = os.getenv("SECRET_KEY", "interview-mentor-production-secret-guard-token")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = int(os.getenv("ACCESS_TOKEN_EXPIRE_DAYS", "30"))

INTERVIEW_PASSWORD = os.getenv("INTERVIEW_PASSWORD", "ChangeThisPassword123!")
INTERVIEW_ALT_PASSWORD = os.getenv("INTERVIEW_ALT_PASSWORD", "")

# Gemini API configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
DEFAULT_GEMINI_MODEL = os.getenv("DEFAULT_GEMINI_MODEL", "gemini-pro-latest")
FAST_GEMINI_MODEL = os.getenv("FAST_GEMINI_MODEL", "gemini-flash-lite-latest")
PREVIEW_GEMINI_MODEL = os.getenv("PREVIEW_GEMINI_MODEL", "gemini-3.1-pro-preview")

AGENTS_DIR = Path(os.getenv("AGENTS_DIR", "/opt/interview-mentor/agents"))
DB_PATH = Path(os.getenv("DB_PATH", "/opt/interview-mentor/interview_mentor.db"))
STATIC_DIR = Path("/opt/interview-mentor/app/static")
