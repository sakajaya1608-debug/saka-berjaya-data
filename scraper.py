import json
import os
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

USERNAME = "pemkab_okuselatan"
URL = f"https://picuki.site/id/profile/{USERNAME}"


def get_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    # Stealth User-Agent
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=options
    )
    return driver


def debug_and_scrape():
    print(f"Mengakses {URL}...")
    driver = get_driver()

    try:
        driver.get(URL)
        time.sleep(7)  # Beri waktu render lebih lama

        os.makedirs("data", exist_ok=True)

        # 1. Simpan screenshot untuk melihat apakah ada Cloudflare/CAPTCHA
        driver.save_screenshot("data/debug_screenshot.png")
        print("Screenshot disimpan ke data/debug_screenshot.png")

        # 2. Simpan sumber HTML mentah
        html_content = driver.page_source
        with open("data/debug_page.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        print("HTML disimpan ke data/debug_page.html")

        soup = BeautifulSoup(html_content, "html.parser")

        # Cetak Judul Halaman
        print("Judul Halaman yang didapat:", driver.title)

        # Coba ambil semua tag <a> dan <img> untuk analisa fleksibel
        posts = []
        # Cari semua link yang mengandung kata /post/ atau gambar postingan
        images = soup.find_all("img")
        print(f"Total tag <img> di halaman: {len(images)}")

        for img in images:
            src = img.get("src", "")
            alt = img.get("alt", "")
            # Abaikan logo, avatar, atau ikon kecil
            if src and not any(
                x in src.lower() for x in ["logo", "avatar", "icon", "svg"]
            ):
                posts.append({"image_url": src, "caption": alt})

        file_path = "data/posts.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(posts, f, ensure_ascii=False, indent=4)

        print(f"Tersimpan {len(posts)} item ke {file_path}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.quit()


if __name__ == "__main__":
    debug_and_scrape()
