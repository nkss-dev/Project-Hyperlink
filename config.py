import os

from dotenv import load_dotenv

load_dotenv()


# Token
bot_token = os.getenv("BOT_TOKEN")
assert bot_token is not None

# Developer options
dev = bool(os.getenv("DEV"))  # Toggle testing mode
dev_bot_token = os.getenv("DEV_BOT_TOKEN")
if dev:
    assert dev_bot_token is not None

dev_guild_ids = (975907920812339200,)  # List of dev guilds for dev-guild-only commands

log_url = os.getenv("LOG_URL")  # Discord webhook URL for warnings and errors
if not dev:
    assert log_url is not None

# IDs
owner_ids: tuple = (534651911903772674, 555580364068880414)

# API
api_url = "https://breadboard.up.railway.app"
api_token = os.getenv("BREADBOARD_API_TOKEN")

# Email
email = os.getenv("EMAIL_ADDRESS")
password_token = os.getenv("EMAIL_PASSWORD")
# For help on getting your password token, refer this article:
# https://support.google.com/mail/answer/185833


# PostgreSQL
class DB:
    def __init__(self):
        self.database = os.getenv("PGDATABASE")
        self.host = os.getenv("PGHOST")
        self.password = os.getenv("PGPASSWORD")
        self.port = os.getenv("PGPORT")
        self.user = os.getenv("PGUSER")

        for variable, value in self.__dict__.items():
            if value is None:
                raise Exception(f"PostgreSQL variable for `{variable}` is not set")

    @property
    def dsn(self):
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
