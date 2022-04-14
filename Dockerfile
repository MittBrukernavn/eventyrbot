FROM python:3.8-slim

WORKDIR /eventyrbot

RUN pip3 install --no-cache-dir discord requests

COPY *.py ./
COPY token.txt .

CMD ["python3", "-u", "main.py"]