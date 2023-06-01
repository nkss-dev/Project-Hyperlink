bot_token = ""
dev_bot_token = ""
dev = True

owner_ids: tuple = ()  # allow users to have owner access to the bot
authorised_ids: tuple = ()  # allow users to invoke commands display values from the bot's database
dev_guild_ids: tuple = ()  # restrict dev only commands to dev guilds
log_url: str = ""  # Discord webhook URL where the bot can send warnings and errors

api_url = "https://nkss-backend.up.railway.app"
api_token = ""

# Email creds for verification.py
email = ""
password_token = ""
# For help on getting your password token, refer this article:
# https://support.google.com/mail/answer/185833


class DB:
    def __init__(self):
        self.database = ""
        self.host = ""
        self.password = ""
        self.port = 0
        self.user = ""

    @property
    def dsn(self):
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
