FROM python:3
WORKDIR .

RUN pip install -U git+https://github.com/Rapptz/discord.py
RUN pip install -U fluent.runtime
RUN pip install -U google-api-python-client google-auth-httplib2 google-auth-oauthlib
RUN pip install -U Pillow
RUN pip install -U python.dotenv
RUN pip install -U pytz

COPY . .
CMD ["python", "./main.py"]
