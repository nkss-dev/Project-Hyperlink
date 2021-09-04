FROM python:3
WORKDIR .
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install -U git+https://github.com/Rapptz/discord.py
COPY . .
CMD ["python", "./main.py"]
