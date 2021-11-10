from dotenv import dotenv_values
from sqlalchemy.engine import URL

config = dotenv_values(".env")

DATABASE_NAME: str = config.get("DATABASE_NAME", "./.data/flaskcardapp.db")
DATABASE_DRIVER: str = config.get("DATABASE_DRIVER", "sqlite")
DATABASE_USERNAME: str = config.get("DATABASE_USERNAME", None)
DATABASE_PASSWORD: str = config.get("DATABASE_PASSWORD", None)
DATABASE_HOST: str = config.get("DATABASE_HOST", None)
DATABASE_PORT: int = config.get("DATABASE_PORT", None)

SQLALCHEMY_DATABASE_URI: str = str(URL.create(DATABASE_DRIVER, username=DATABASE_USERNAME, password=DATABASE_PASSWORD, database=DATABASE_NAME, host=DATABASE_HOST, port=DATABASE_PORT))
SQLALCHEMY_ECHO: bool = config.get("SQLALCHEMY_ECHO", False)

APP_NAME: str = config.get("APP_NAME", "FlashcardApp")
SECRET_KEY: str = config.get("APP_SECRET", "892a32bb3d85ffe8b79a73d70f13817f")

LOG_FILE: str = config.get("LOG_FILE", "./logs/flashcard.log")
LOG_LEVEL: str = "DEBUG"
LOG_BACKTRACE: bool = True