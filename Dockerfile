FROM python:3.8-slim

WORKDIR /eventyrbot

RUN pip3 install --no-cache-dir discord

COPY main.py .
COPY token.txt .

CMD ["python3", "-u", "main.py"]