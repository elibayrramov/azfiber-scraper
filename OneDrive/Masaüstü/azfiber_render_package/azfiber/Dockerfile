FROM python:3.11-slim
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update       && apt-get install -y --no-install-recommends          wget ca-certificates unzip          chromium chromium-driver          tesseract-ocr          libnss3 libx11-6 libxss1 libasound2 libatk1.0-0 libcups2 libgtk-3-0 fonts-liberation       && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV CHROME_DRIVER_PATH=/usr/bin/chromedriver
ENV TESSERACT_CMD=/usr/bin/tesseract
ENV PORT=8000
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8000", "--workers", "1", "--timeout", "120"]
