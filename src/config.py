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


# Google Drive API
GOOGLE_REFRESH_TOKEN = os.getenv("GOOGLE_REFRESH_TOKEN")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

google_client_config = {
    "installed": {
        "client_id": GOOGLE_CLIENT_ID,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_secret": GOOGLE_CLIENT_SECRET,
    }
}

emojis = {
    # Utility
    "loading": "<a:loading:888054519160770621>",
    "no": "<:no:888054644033597520>",
    "not-verified": "<:notverified:888054519177543690>",
    "triggered": "<a:triggered:888054521648009237>",
    "verified": "<:verified:888054520045768704>",
    "yes": "<:yes:888054644981522433>",
    # Games
    "Age of Empires": "<a:aoe:853963799912644609>",
    "Among Us": "<a:amongus:853940323553247232>",
    "Apex Legends": "<:apexLegends:925731692059193355>",
    "Assassin's Creed": "<:ac:853973358719008798>",
    "Brawlhalla": "<:brawlhalla:942089191968354345>",
    "Chess": "<:chess:853937662666473482>",
    "Clash of Clans": "<:coc:853938375722795038>",
    "Clash Royale": "<a:clashRoyale:853939000515624971>",
    "Call of Duty": "<:cod:853946076482633728>",
    "CSGO": "<a:csgo:853949325688176670>",
    "Dead By Daylight": "<:deadByDaylight:925732842816827432>",
    "Fortnite": "<:fortnite:853951449934462976>",
    "Genshin Impact": "<:genshin:853950999160029194>",
    "GTAV": "<a:gtav:853953682781896744>",
    "Minecraft": "<:minecraft:853958189016285194>",
    "osu!": "<:osu:853958362592313344>",
    "Paladins": "<:paladins:853962608745644093>",
    "PUBG": "<:pubg:853959082053468201>",
    "Rise of Nations": "<:ron:853986005471723540>",
    "Rocket League": "<:rocketLeague:853959646451859486>",
    "skribbl.io": "<:skribbl:854709977989906472>",
    "Valorant": "<:valorant:853959955605618699>",
}
