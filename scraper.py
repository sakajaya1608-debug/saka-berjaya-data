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


def scrape_picuki_correctly():
    driver = get_driver()
    posts = []

    try:
        print(f"Membuka {BASE_URL}...")
        driver.get(BASE_URL)
        time.sleep(3)

        # 1. Cari input pencarian dan masukkan username
        search_box = driver.find_element(
            By.CSS_SELECTOR, "input[type='text'], input"
        )
        search_box.clear()
        search_box.send_keys(USERNAME)
        search_box.send_keys(Keys.ENTER)

        print("Menunggu halaman hasil pencarian...")
        time.sleep(5)

        # 2. KLIK LINK PROFIL YANG MUNCUL PADA HASIL PENCARIAN
        # Berdasarkan gambar sebelumnya, kartu profil memiliki link yang mengarah ke profil akun
        try:
            profile_link = driver.find_element(
                By.XPATH, f"//a[contains(@href, '/profile/{USERNAME}')]"
            )
            print("Profil ditemukan, mengklik tautan profil...")
            profile_link.click()
            time.sleep(6)  # Tunggu halaman galeri profil terbuka
        except Exception as e:
            print(
                f"Gagal klik elemen profil otomatis, mencoba navigasi langsung URL: {e}"
            )
            driver.get(f"https://picuki.site/id/profile/{USERNAME}")
            time.sleep(6)

        # Scroll ke bawah agar postingan di tab 'POSTS' ter-load (lazy loading)
        driver.execute_script("window.scrollBy(0, 800);")
        time.sleep(3)

        # 3. Parse HTML dari halaman galeri postingan
        soup = BeautifulSoup(driver.page_source, "html.parser")
        img_tags = soup.find_all("img")

        print(f"Total tag <img> di halaman profil: {len(img_tags)}")

        for img in img_tags:
            src = img.get("src", "")
            alt = img.get("alt", "")

            # Filter ketat: Hanya ambil gambar postingan (biasanya dari CDN Instagram atau storage post)
            # Buang logo, avatar, ikon, dan error page
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

        # Simpan ke file JSON
        os.makedirs("data", exist_ok=True)
        file_path = "data/posts.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(posts, f, ensure_ascii=False, indent=4)

        print(
            f"BERHASIL! Menyimpan {len(posts)} data postingan asli ke {file_path}"
        )

    except Exception as e:
        print(f"Terjadi error saat proses scraping: {e}")
    finally:
        driver.quit()


if __name__ == "__main__":
    scrape_picuki_correctly()
