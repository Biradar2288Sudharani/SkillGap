import os
from dotenv import load_dotenv
from urllib.parse import quote_plus

load_dotenv()  # reads variables from a .env file into the environment


class Config:
    """
    All app configuration lives here, pulled from environment variables.
    Keeping secrets out of the code is a basic security practice worth
    mentioning in the interview.
    """

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-me")

    # ---- MySQL connection ----
    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DB = os.getenv("MYSQL_DB", "skillgap_db")
    MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")

    _ENCODED_PASSWORD = quote_plus(MYSQL_PASSWORD)

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{MYSQL_USER}:{_ENCODED_PASSWORD}"
        f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ---- AI provider ----
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "") 
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash") 
