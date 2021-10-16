# Project Hyperlink

A moderation bot made specifically to be used in NITKKR-only servers.

## Running a local instance

Ideally, you'd invite [my instance](https://discord.com/api/oauth2/authorize?client_id=789474485555953694&permissions=275834711254&scope=bot "Bot's invite link") of the bot. This allows it to always stay online and receive updates as they roll out.

Nevertheless, here are the installation steps:

1. **Ensure that you have Python 3.9 or higher.**

2. **Set up the virtual environment:** `python 3.9 -m venv venv`<br>
    Activate it using: `source venv/bin/activate`

3. **Install the dependencies:** `pip install -U -r requirements.txt`

4. **Setup configuration:**<br>
    Rename the `config-sample.py` file in the root directory to `config.py` and populate it with the corresponding values.

5. **For [drive.py](cogs/drive.py "Queries a linked Google Drive"):**<br>
    Follow the instructions given [here](https://developers.google.com/drive/api/v3/quickstart/python "Setup instructions for the Google Drive API in Python") and store the resultant `.json` file in the `db` folder (generated automatically after the bot is run at least once) and rename it to `credentials.json`
