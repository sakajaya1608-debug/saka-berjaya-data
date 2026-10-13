import json
import os
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

USERNAME = "pemkab_okuselatan"
BASE_URL = "https://picuki.site/id/"


def get_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=options
    )
    return driver


def scrape_picuki_from_search():
    driver = get_driver()
    posts = []

    try:
        print(f"Membuka {BASE_URL}...")
        driver.get(BASE_URL)
        time.sleep(3)

        # 1. Cari input box di halaman Picuki dan masukkan username
        search_box = driver.find_element(
            By.CSS_SELECTOR, "input[type='text'], input[placeholder*='Search']"
        )
        search_box.clear()
        search_box.send_keys(USERNAME)
        search_box.send_keys(Keys.ENTER)

        print("Menunggu hasil pencarian dimuat...")
        time.sleep(6)  # Beri waktu JS merender 'Hasil pencarian'

        # Scroll sedikit ke bawah agar postingan ter-load (lazy loading)
        driver.execute_script("window.scrollBy(0, 500);")
        time.sleep(3)

        # 2. Parse HTML yang sudah dirender oleh JavaScript
        soup = BeautifulSoup(driver.page_source, "html.parser")

        # Cari semua gambar postingan di bawah area hasil pencarian
        # Mengabaikan foto profil (logo OKU Selatan)
        img_tags = soup.find_all("img")

        print(f"Total tag <img> ditemukan: {len(img_tags)}")

        for img in img_tags:
            src = img.get("src", "")
            alt = img.get("alt", "")

            # Filter agar hanya mengambil gambar postingan, bukan avatar / logo / icon
            if src and not any(
                x in src.lower()
                for x in ["logo", "avatar", "icon", "svg", "404", "error"]
            ):
                # Ambil URL penuh jika src berupa path relatif
                if src.startswith("/"):
                    src = "https://picuki.site" + src

                posts.append(
                    {
                        "image_url": src,
                        "caption": alt if alt else "Postingan Pemkab OKU Selatan",
                    }
                )

        # Simpan hasil ke data/posts.json
        os.makedirs("data", exist_ok=True)
        file_path = "data/posts.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(posts, f, ensure_ascii=False, indent=4)

        print(
            f"BERHASIL! Menyimpan {len(posts)} data postingan ke {file_path}"
        )

    except Exception as e:
        print(f"Terjadi error saat proses scraping: {e}")
    finally:
        driver.quit()


if __name__ == "__main__":
    scrape_picuki_from_search()
