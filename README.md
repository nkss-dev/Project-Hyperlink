# Project Hyperlink

A personal moderation bot made as a part of the NKSSS project

## Running a local instance

Ideally, you'd invite [my instance](https://discord.com/oauth2/authorize?client_id=789474485555953694&scope=bot+applications.commands&permissions=284407639234 "Bot's invite link") of the bot. This allows it to always stay online and receive updates as they roll out.

Nevertheless, here are the installation steps:

1. **Ensure that you have Python 3.10 or higher.**

2. **Clone the repository:** `git clone https://www.github.com/GetPsyched/Project-Hyperlink`

3. **Set up the virtual environment:** `python3 -m venv hyperlink-env`

   Activate it using one of the following:

   - On Unix or MacOS, using the bash shell: `source hyperlink-env/bin/activate`
   - On Unix or MacOS, using the csh shell: `source hyperlink-env/bin/activate.csh`
   - On Unix or MacOS, using the fish shell: `source hyperlink-env/bin/activate.fish`
   - On Windows using the Command Prompt: `path\to\hyperlink-env\Scripts\activate.bat`
   - On Windows using PowerShell: `path\to\hyperlink-env\Scripts\Activate.ps1`

4. **Install the dependencies:** `pip install -U -r requirements.txt`

5. **Setup configuration:** Rename the `config-sample.py` file in the root directory to `config.py` and populate it with the corresponding values.
