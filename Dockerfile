FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

WORKDIR /app

RUN pip install --no-cache-dir flask requests curl_cffi werkzeug loguru dotenv playwright
run python -m playwright install --with-deps chromium

COPY . .

ENV PORT=5200
EXPOSE 5200

CMD ["python", "app.py"]