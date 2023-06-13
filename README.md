# Project Hyperlink

A personal moderation bot made as a part of the NKSSS project

## Running a local instance

Ideally, you'd invite [my instance](https://discord.com/oauth2/authorize?client_id=789474485555953694&scope=bot+applications.commands&permissions=284407639234 "Bot's invite link") of the bot. This allows it to always stay online and receive updates as they roll out.

Nevertheless, here are the installation steps:

1. **Ensure that you have Python 3.10 or higher.**

2. **Clone the repository:** `git clone git@github.com:NIT-KKR-Student-Support-System/Project-Hyperlink.git`

3. **Set up the virtual environment:** `python3 -m venv hyperlink-env`

   <details>
      <summary>Activation Instructions</summary>

      - On Unix or MacOS, using the bash shell: `source hyperlink-env/bin/activate`
      - On Unix or MacOS, using the csh shell: `source hyperlink-env/bin/activate.csh`
      - On Unix or MacOS, using the fish shell: `source hyperlink-env/bin/activate.fish`
      - On Windows using the Command Prompt: `hyperlink-env\Scripts\activate.bat`
      - On Windows using PowerShell: `hyperlink-env\Scripts\Activate.ps1`
   </details>

4. **Install the dependencies:** `pip install -U -r requirements.txt`

5. **Configuration:**

   Following are the environment variables needed for this project. You can paste these into an `.env` file and it will auto-load.
   ```properties
   # Token
   BOT_TOKEN=""

   # Developer options
   TESTING_MODE=1
   TESTING_BOT_TOKEN=""
   LOG_URL="https://discord.com/api/webhooks/.../..."

   # API
   BREADBOARD_API_TOKEN=""

   # Email
   EMAIL_ADDRESS="foo@bar.com"
   EMAIL_PASSWORD=""

   # PostgreSQL
   PGDATABASE=""
   PGHOST=""
   PGPASSWORD=""
   PGPORT=""
   PGUSER=""
   ```

   Additionally, there are some non-secret configuration options in [config.py](/config.py), you may want to look at those too.

   Note: Some of these are optional, but may break the bot's functionality, if left empty.

6. **For [drive.py](cogs/drive.py 'Queries a linked Google Drive'):**<br>
   Follow the instructions given [here](https://developers.google.com/drive/api/v3/quickstart/python 'Setup instructions for the Google Drive API in Python') and store the resultant `.json` file in the `db` folder (generated automatically after the bot is run at least once) and rename it to `credentials.json`
