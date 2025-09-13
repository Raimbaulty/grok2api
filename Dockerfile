FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

WORKDIR /app

RUN pip install --no-cache-dir flask requests curl_cffi werkzeug loguru dotenv playwright
run python -m playwright install --with-deps chromium

COPY . .

ENV PORT=5678
ENV SHOW_THINKING=False
ENV IS_CUSTOM_SSO=False
ENV MANAGER_SWITCH=False
ENV IS_TEMP_CONVERSATION=True
ENV ISSHOW_SEARCH_RESULTS=False

EXPOSE 5678

CMD ["python", "app.py"]
