import os

from dotenv import load_dotenv

load_dotenv()  # reads .env into process environment


class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///documents.db")
    GEMINI_API_KEY: str | None = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")


settings = Settings()
