FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src

ENV PORT=8080
EXPOSE 8080

CMD ["uvicorn", "crypto_news_parser.main:app", "--app-dir", "src", "--host", "0.0.0.0", "--port", "8080"]
