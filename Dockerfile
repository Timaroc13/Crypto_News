FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src

EXPOSE 8080

CMD ["sh", "-c", "uvicorn crypto_news_parser.main:app --app-dir src --host 0.0.0.0 --port ${PORT:-8080}"]
