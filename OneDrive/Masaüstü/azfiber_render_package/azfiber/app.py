from flask import Flask, render_template_string, request, jsonify
import time
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image
import pytesseract
import tempfile
import os
import traceback

# === CONFIG - adjust if needed ===
CHROME_DRIVER_PATH = r"C:\Users\Eli\OneDrive\Masaüstü\chromedriver.exe"
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
LOGIN_URL = "https://customer.azfiber.net/index.php?module=index"
USERNAME = "ali"
PASSWORD = "Welcome2024!"
MAX_ATTEMPTS = 5
# ================================

pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

app = Flask(__name__)

HTML_PAGE = '''
<!doctype html>
<html lang="az">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>AzFiber Scraper</title>
    <style>
      body{font-family:Inter,system-ui,Arial;margin:24px}
      button{padding:10px 16px;font-size:16px}
      pre{white-space:pre-wrap;background:#f7f7f7;padding:12px;border-radius:6px}
      #spinner{display:none}
    </style>
  </head>
  <body>
    <h2>AzFiber — Axtar və Scrape et</h2>
    <p>Sadəcə <strong>Axtar</strong> düyməsinə basın, serverdə scraping işə düşəcək və nəticələr nümayiş olunacaq.</p>

    <button id="scrapeBtn">Axtar</button>
    <span id="spinner">⏳ İşlənir...</span>
    <h3>Nəticə</h3>
    <pre id="output">(hələ bir şey yox)</pre>

    <script>
      const btn = document.getElementById('scrapeBtn');
      const out = document.getElementById('output');
      const spinner = document.getElementById('spinner');

      btn.addEventListener('click', async () => {
        btn.disabled = true;
        spinner.style.display = 'inline';
        out.textContent = 'İşlənir — serverdə scraping aparılır...';
        try {
          const resp = await fetch('/scrape', { method: 'POST' });
          const data = await resp.json();
          if (data.success) {
            out.textContent = data.pages.join('\n\n--- PAGE BREAK ---\n\n');
          } else {
            out.textContent = 'Xəta: ' + (data.error || 'Naməlum xəta');
          }
        } catch (e) {
          out.textContent = 'Network xətası: ' + e.toString();
        }
        spinner.style.display = 'none';
        btn.disabled = false;
      });
    </script>
  </body>
</html>
'''


def attempt_login(driver):
    driver.get(LOGIN_URL)
    time.sleep(1)

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "txtLogin"))
        )

        driver.find_element(By.NAME, "txtLogin").clear()
        driver.find_element(By.NAME, "txtLogin").send_keys(USERNAME)
        driver.find_element(By.NAME, "txtPwd").clear()
        driver.find_element(By.NAME, "txtPwd").send_keys(PASSWORD)

        # CAPTCHA şəkilini götür
        captcha_img = driver.find_element(By.XPATH, '//img[contains(@src, "captcha")]')
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmpf:
            captcha_path = tmpf.name
        captcha_img.screenshot(captcha_path)
        img = Image.open(captcha_path)
        captcha_code = pytesseract.image_to_string(
            img, config="--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        ).strip()

        # Temiz biçim
        captcha_code = ''.join(ch for ch in captcha_code if ch.isalnum())[:10]

        print("🧠 CAPTCHA kodu (OCR):", captcha_code)

        driver.find_element(By.ID, "txtCaptcha").clear()
        driver.find_element(By.ID, "txtCaptcha").send_keys(captcha_code)
        driver.find_element(By.NAME, "txtPwd").send_keys(Keys.RETURN)
        time.sleep(3)

        # Uğurlu login yoxlaması
        page_source = driver.page_source.lower()
        if "dashboard" in page_source or "logout" in page_source:
            try:
                os.remove(captcha_path)
            except Exception:
                pass
            return True
        try:
            os.remove(captcha_path)
        except Exception:
            pass
        return False

    except Exception as e:
        print("❌ Giriş səhifəsi tapılmadı:", e)
        return False


def scrape_customers():
    chrome_driver_path = CHROME_DRIVER_PATH

    options = webdriver.ChromeOptions()
    # Başsız rejim (serverdə çalışdırmaq üçün)
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    service = Service(chrome_driver_path)
    driver = webdriver.Chrome(service=service, options=options)

    success = False
    try:
        for i in range(1, MAX_ATTEMPTS + 1):
            print(f"🔁 Giriş cəhdi {i}")
            if attempt_login(driver):
                print("✅ Uğurlu giriş!")
                success = True
                break
            else:
                print("❌ Yanlış CAPTCHA, yenidən cəhd edilir.")
                time.sleep(2)

        if not success:
            driver.quit()
            return None

        # manage_accounts səhifəsinə keç
        driver.get("https://customer.azfiber.net/index.php?module=manage_accounts")
        time.sleep(3)

        all_customers = []

        while True:
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, '//*[@id="form1"]/main/div[3]'))
                )
                time.sleep(1)

                table_body = driver.find_element(
                    By.XPATH,
                    '//*[@id="form1"]/main/div[3]/div[2]/div/div/div[2]/div[1]//table[contains(@id, "_manage_accounts")]/tbody'
                )
                all_customers.append(table_body.text)

                # Next düyməsi yoxlanacaq (əgər varsa, kliklənəcək)
                next_buttons = driver.find_elements(By.XPATH, '//a[contains(text(), "Next")]')
                if next_buttons:
                    next_buttons[0].click()
                    time.sleep(2)
                else:
                    break
            except Exception:
                break

        driver.quit()
        return all_customers
    except Exception as e:
        try:
            driver.quit()
        except Exception:
            pass
        raise


@app.route('/')
def index():
    return render_template_string(HTML_PAGE)


@app.route('/scrape', methods=['POST'])
def scrape_route():
    try:
        # Directly call the scraping function (synchronous)
        pages = scrape_customers()
        if pages is None:
            return jsonify({'success': False, 'error': 'Login alınmadı. CAPTCHA və ya hesab məlumatlarını yoxla.'})
        return jsonify({'success': True, 'pages': pages})
    except Exception as e:
        tb = traceback.format_exc()
        print(tb)
        return jsonify({'success': False, 'error': str(e), 'trace': tb})


if __name__ == '__main__':
    # Lokal inkişaf üçün
    app.run(host='0.0.0.0', port=5000, debug=True)
