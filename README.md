# KKR-Discord-Bot
A moderation bot made specifically to be used in NITKKR only servers

## Prerequisites
- Python 3.6+
- aiohttp (for [tag.py](https://github.com/GetPsyched/Project-Hyperlink/blob/main/cogs/tag.py))
- discord 1.7+
- googleapiclient (for [drive.py](https://github.com/GetPsyched/Project-Hyperlink/blob/main/cogs/drive.py))
- python.dotenv
- fluent.runtime

## Running a local instance

- Rename `.env.sample` to `.env`
- Replace `<your-token-here>` with your bot token

- Rename `db.sample` folder to `db`

### If you choose to use [verification.py](https://github.com/GetPsyched/Project-Hyperlink/blob/main/cogs/verification.py):
- Replace `<email-here>` with the Google email with which you want the verification emails to be sent
- Replace `<password-token-here>` with the password token of said email given by Google after turning on Developer Mode from [here](https://support.google.com/a/answer/10621196?hl=en)
