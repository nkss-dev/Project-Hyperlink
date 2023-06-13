import os

from dotenv import load_dotenv

load_dotenv()


# Token
BOT_TOKEN = os.getenv("BOT_TOKEN")
assert BOT_TOKEN is not None

# Developer options
TESTING_MODE = bool(os.getenv("TESTING_MODE"))
TESTING_BOT_TOKEN = os.getenv("TESTING_BOT_TOKEN") or BOT_TOKEN
if TESTING_MODE:
    assert TESTING_BOT_TOKEN is not None

DEV_GUILD_IDS = (975907920812339200,)  # List of dev guilds for dev-guild-only commands

LOG_URL = os.getenv("LOG_URL")  # Discord webhook URL for warnings and errors
if not TESTING_MODE:
    assert LOG_URL is not None

# IDs
OWNER_IDS: tuple = (534651911903772674, 555580364068880414)

# API
API_URL = "https://breadboard.up.railway.app"
API_TOKEN = os.getenv("BREADBOARD_API_TOKEN")

# Email
EMAIL = os.getenv("EMAIL_ADDRESS")
EMAIL_TOKEN = os.getenv("EMAIL_PASSWORD")
# For help on getting your password token, refer this article:
# https://support.google.com/mail/answer/185833


# PostgreSQL
class DB:
    def __init__(self):
        self.DATABASE = os.getenv("PGDATABASE")
        self.HOST = os.getenv("PGHOST")
        self.PASSWORD = os.getenv("PGPASSWORD")
        self.PORT = os.getenv("PGPORT")
        self.USER = os.getenv("PGUSER")

        for variable, value in self.__dict__.items():
            if value is None:
                raise Exception(f"PostgreSQL variable for `{variable}` is not set")

    @property
    def DSN(self):
        return f"postgresql://{self.USER}:{self.PASSWORD}@{self.HOST}:{self.PORT}/{self.DATABASE}"
