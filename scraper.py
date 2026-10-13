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
    options.add_argument("--headless")  # Wajib untuk GitHub Actions (tanpa GUI)
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=options
    )
    return driver


def scrape_picuki_selenium():
    print(f"Membuka browser headless untuk mengakses {URL}...")
    driver = get_driver()

    try:
        driver.get(URL)
        # Beri waktu beberapa detik agar JavaScript selesai merender halaman
        time.sleep(5)

        # Ambil halaman HTML yang sudah dirender
        html_content = driver.page_source
        soup = BeautifulSoup(html_content, "html.parser")

        posts = []
        # Cari elemen postingan (menyesuaikan struktur umum grid card)
        post_cards = soup.select(".post-item, .box-photo, .content-profile")

        print(f"Ditemukan {len(post_cards)} elemen kartu postingan.")

        for card in post_cards:
            try:
                link_elem = card.select_one("a")
                link = (
                    link_elem["href"] if link_elem and "href" in link_elem.attrs else ""
                )

                img_tag = card.select_one("img")
                img_url = (
                    img_tag["src"] if img_tag and "src" in img_tag.attrs else ""
                )

                caption_tag = card.select_one(".photo-description, .text, p")
                caption = caption_tag.text.strip() if caption_tag else ""

                if link or img_url:
                    posts.append(
                        {
                            "link": link,
                            "image_url": img_url,
                            "caption": caption,
                        }
                    )
            except Exception as e:
                print(f"Error parsing card: {e}")
                continue

        # Simpan ke folder data
        os.makedirs("data", exist_ok=True)
        file_path = "data/posts.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(posts, f, ensure_ascii=False, indent=4)

        print(
            f"Berhasil! Menyimpan {len(posts)} data postingan ke {file_path}"
        )

    except Exception as e:
        print(f"Terjadi kesalahan saat menjalankan Selenium: {e}")
    finally:
        driver.quit()


if __name__ == "__main__":
    scrape_picuki_selenium()
