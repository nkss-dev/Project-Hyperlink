# KKR-Discord-Bot
A moderation bot made specifically to be used in NITKKR only servers

## Prerequisites
- Python 3.9+
- discord.py 2.0
- fluent.runtime
- [googleapiclient](https://developers.google.com/docs/api/quickstart/python) (for [drive.py](https://github.com/GetPsyched/Project-Hyperlink/blob/main/cogs/drive.py))
- Pillow
- python.dotenv
- pytz

## Running a local instance

### In [.env.sample](https://github.com/GetPsyched/Project-Hyperlink/blob/main/.env.sample)
- Rename `.env.sample` to `.env`
- Replace `<bot-token>` with your bot token
- Replace `<ID>` with any user ID that you want to be added as a bot owner
    - Remove any extra `<ID>` placeholder
    - Trailing commas are not allowed
- If you choose to use [verification.py](https://github.com/GetPsyched/Project-Hyperlink/blob/main/cogs/verification.py):
    - Replace `<email-here>` with the Google email with which you want the verification emails to be sent
    - Replace `<password-token-here>` with the password token of said email given by Google after turning on Developer Mode from [here](https://support.google.com/a/answer/10621196?hl=en)
- If you choose to use [drive.py](https://github.com/GetPsyched/Project-Hyperlink/blob/main/cogs/drive.py):
    - Follow the instructions given [here](https://developers.google.com/drive/api/v3/quickstart/python) and store the resultant json file in the `db` folder (generated automatically after the bot is run at least once) and rename it to `credentials.json`
