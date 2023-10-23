# Project Hyperlink

A personal moderation bot made as a part of the NKSS project

## Running a local instance

Ideally, you'd invite [my instance](https://discord.com/oauth2/authorize?client_id=789474485555953694&scope=bot+applications.commands&permissions=284407639234 "Bot's invite link") of the bot. This allows it to always stay online and receive updates as they roll out.

Nevertheless, here are the installation steps:

1. **Clone the repository:** `git clone git@github.com:NIT-KKR-Student-Support-System/Project-Hyperlink.git`

2. **Installation:**

   - Install [nix: the package manager](https://nixos.org/download) if you haven't already.
   - Run `nix develop` to enter the shell environment which will auto-magically install all our required dependencies (including Python!).
   - If you prefer, we also support [`direnv`](https://github.com/direnv/direnv) for setting up the shell environment.

   **NOTE:** The above process only works on **non-Windows systems** (Windows as well IF you use WSL2). If you want to install this on Windows (please don't), refer the steps in the closed summary below:
   <details>
      <summary>Windows install without WSL2</summary>

      - Ensure that you have Python 3.10 or higher.
      - **Set up the virtual environment:** `python3 -m venv hyperlink-env`
         <br>
         To activate this environment:
         - using Command Prompt, run: `hyperlink-env\Scripts\activate.bat`
         - using PowerShell, run: `hyperlink-env\Scripts\Activate.ps1`
      - **Install the dependencies:** `pip install -U -r requirements.txt`
   </details>

3. **Configuration:**

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

4. **For [drive.py](cogs/drive.py 'Queries a linked Google Drive'):**<br>
   Follow the instructions given [here](https://developers.google.com/drive/api/v3/quickstart/python 'Setup instructions for the Google Drive API in Python') and store the resultant `.json` file in the `db` folder (generated automatically after the bot is run at least once) and rename it to `credentials.json`
