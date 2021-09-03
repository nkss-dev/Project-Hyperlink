# KKR-Discord-Bot
A moderation bot made specifically to be used in NITKKR only servers

## Prerequisites
- Python 3.6+
- discord.py 2.0
- fluent.runtime
- [googleapiclient](https://developers.google.com/docs/api/quickstart/python) (for [drive.py](https://github.com/GetPsyched/Project-Hyperlink/blob/main/cogs/drive.py))
- python.dotenv

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

### In [db.sample](https://github.com/GetPsyched/Project-Hyperlink/tree/main/db.sample)
- Rename `db.sample` to `db`
