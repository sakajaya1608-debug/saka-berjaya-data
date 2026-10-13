import json
import os
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
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


def scrape_picuki_click_search():
    driver = get_driver()
    posts = []

    try:
        print(f"Membuka {BASE_URL}...")
        driver.get(BASE_URL)
        time.sleep(3)

        # 1. Ketik username pada input form
        print("Mencari kolom input pencarian...")
        search_input = driver.find_element(
            By.CSS_SELECTOR, "input.main-form__input"
        )
        search_input.click()
        search_input.clear()
        for char in USERNAME:
            search_input.send_keys(char)
            time.sleep(0.05)

        print(f"Berhasil mengetik username: {USERNAME}")

        # 2. Klik tombol pencarian (ikon kaca pembesar) secara eksplisit
        print("Mengklik tombol pencarian...")
        search_btn = driver.find_element(
            By.CSS_SELECTOR, "button.main-form__field-download"
        )
        search_btn.click()

        print("Menunggu hasil pencarian dimuat oleh JavaScript (12 detik)...")
        time.sleep(12)  # Beri waktu render hasil pencarian muncul

        # Scroll ke bawah untuk memicu lazy loading tambahan
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
        time.sleep(4)

        # 3. Parsing HTML hasil render
        soup = BeautifulSoup(driver.page_source, "html.parser")
        items = soup.select("li.profile-media-list__item")
        print(f"Ditemukan {len(items)} item postingan di halaman profil.")

        for item in items:
            try:
                img_tag = item.select_one("img.media-content__image")
                img_url = (
                    img_tag["src"] if img_tag and "src" in img_tag.attrs else ""
                )

                caption_tag = item.select_one("p.media-content__caption")
                caption = (
                    caption_tag.text.strip()
                    if caption_tag
                    else "Postingan Pemkab OKU Selatan"
                )

                likes_tag = item.select_one("p.media-content__meta-like")
                likes = likes_tag.text.strip() if likes_tag else "0"

                time_tag = item.select_one("p.media-content__meta-time")
                post_time = time_tag.text.strip() if time_tag else ""

                download_btn = item.select_one("a.download-btn")
                download_url = (
                    download_btn["href"]
                    if download_btn and "href" in download_btn.attrs
                    else ""
                )

                if img_url:
                    posts.append(
                        {
                            "image_url": img_url,
                            "caption": caption,
                            "likes": likes,
                            "time": post_time,
                            "download_url": download_url,
                        }
                    )
            except Exception as e:
                print(f"Error saat memparsing item: {e}")
                continue

        # Simpan ke folder data/posts.json
        os.makedirs("data", exist_ok=True)
        file_path = "data/posts.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(posts, f, ensure_ascii=False, indent=4)

        print(
            f"BERHASIL! Menyimpan {len(posts)} data postingan ke {file_path}"
        )

    except Exception as e:
        print(f"Terjadi error saat proses interaksi: {e}")
    finally:
        driver.quit()


if __name__ == "__main__":
    scrape_picuki_click_search()
