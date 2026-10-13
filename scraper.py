import json
import os
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

USERNAME = "pemkab_okuselatan"
# Langsung gunakan URL pencarian spesifik picuki.site
SEARCH_URL = f"https://picuki.site/id/search?q={USERNAME}"


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


def scrape_picuki_direct_search():
    driver = get_driver()
    posts = []

    try:
        print(f"Membuka URL pencarian: {SEARCH_URL}")
        driver.get(SEARCH_URL)
        time.sleep(6)  # Beri waktu render halaman hasil pencarian

        # Scroll ke bawah untuk memastikan gambar termuat (lazy loading)
        driver.execute_script("window.scrollBy(0, 800);")
        time.sleep(3)

        soup = BeautifulSoup(driver.page_source, "html.parser")

        # Cari semua elemen gambar di halaman hasil pencarian
        img_tags = soup.find_all("img")
        print(f"Total tag <img> ditemukan: {len(img_tags)}")

        for img in img_tags:
            src = img.get("src", "")
            alt = img.get("alt", "")

            # Filter ketat untuk membuang aset bawaan web (logo, icon, photos.png, dll)
            if src and not any(
                x in src.lower()
                for x in [
                    "logo",
                    "avatar",
                    "icon",
                    "svg",
                    "404",
                    "error",
                    "photos.png",
                    "default",
                ]
            ):
                if src.startswith("/"):
                    src = "https://picuki.site" + src

                posts.append(
                    {
                        "image_url": src,
                        "caption": alt if alt else "Postingan Pemkab OKU Selatan",
                    }
                )

        # Simpan ke folder data/posts.json
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
    scrape_picuki_direct_search()
