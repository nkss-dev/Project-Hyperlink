FROM python:3
WORKDIR .

RUN pip install -U -r requirements.txt

COPY . .
CMD ["python", "./main.py"]
