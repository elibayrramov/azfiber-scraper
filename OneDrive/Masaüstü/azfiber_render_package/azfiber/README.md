# AzFiber Scraper — Render deployment package

This repository contains a Flask app that uses Selenium + headless Chromium + Tesseract
to scrape the AzFiber customer management pages. It's prepared for deployment to Render
using a Dockerfile (Chrome + chromedriver + tesseract included).

## Files included
- app.py       : Flask application (synchronous scrape endpoint `/scrape`)
- Dockerfile   : Docker image with Chromium, chromedriver, and tesseract
- requirements.txt
- netlify.toml : (optional) Netlify redirect to route `/api/scrape` to the Render app
- .gitignore

## Quick local test with Docker
```bash
docker build -t azfiber-scraper .
docker run -e AZF_USER=ali -e AZF_PASS=Welcome2024! -p 8000:8000 azfiber-scraper
# open http://localhost:8000
```

## Deploy to Render
1. Create a GitHub repo and push these files.
2. Sign in to Render (https://render.com) and create a new **Web Service**.
   - Connect your GitHub repository
   - Select **Docker** as the environment (Render will use the Dockerfile)
   - Set Environment Variables in Render dashboard:
     - AZF_USER = your_username
     - AZF_PASS = your_password
     - (optional) LOGIN_URL, MAX_ATTEMPTS
3. Deploy and test the public URL provided by Render.

## Security & notes
- Do NOT commit real credentials to git. Use Render's environment variables.
- CAPTCHA OCR often fails; consider manual CAPTCHA flow or a third-party solver if needed.
- For production, consider moving scraping to background jobs (Redis + RQ/Celery) to avoid blocking web workers.
