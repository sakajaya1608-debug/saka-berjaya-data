import json
import os
import re
import requests
from bs4 import BeautifulSoup

# Target username Picuki
USERNAME = "pemdaokuselatan"
URL = f"https://www.picuki.com/profile/{USERNAME}"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def scrape_picuki():
    print(f"Mulai mengambil data dari {URL}...")
    response = requests.get(URL, headers=HEADERS)

    if response.status_code != 200:
        print(f"Gagal mengakses halaman. Status code: {response.status_code}")
        return

    soup = BeautifulSoup(response.text, "html.parser")
    posts = []

    # Mengambil elemen-elemen postingan di Picuki
    post_cards = soup.select(".box-photos .box-photo")

    for card in post_cards:
        try:
            # Link ke detail postingan
            link = card.select_one("a.photo")["href"]
            # URL gambar/media
            img_tag = card.select_one("img.post-image")
            img_url = img_tag["src"] if img_tag else ""
            # Deskripsi/caption
            caption_tag = card.select_one(".photo-description")
            caption = caption_tag.text.strip() if caption_tag else ""
            # Jumlah likes & komentar
            likes = (
                card.select_one(".likes-photo-box").text.strip()
                if card.select_one(".likes-photo-box")
                else "0"
            )
            comments = (
                card.select_one(".comments-photo-box").text.strip()
                if card.select_one(".comments-photo-box")
                else "0"
            )

            posts.append(
                {
                    "link": link,
                    "image_url": img_url,
                    "caption": caption,
                    "likes": likes,
                    "comments": comments,
                }
            )
        except Exception as e:
            print(f"Error parsing card: {e}")
            continue

    # Simpan ke file JSON
    os.makedirs("data", exist_ok=True)
    file_path = "data/posts.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=4)

    print(
        f"Berhasil mengunduh {len(posts)} postingan dan disimpan ke {file_path}"
    )


if __name__ == "__main__":
    scrape_picuki()
