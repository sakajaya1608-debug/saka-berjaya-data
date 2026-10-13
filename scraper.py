import json
import os
import requests
from bs4 import BeautifulSoup

# Username yang benar sesuai informasi Anda
USERNAME = "pemkab_okuselatan"
URL = f"https://www.picuki.com/profile/{USERNAME}"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
}


def scrape_picuki():
    print(f"Mulai mengambil data dari {URL}...")
    try:
        response = requests.get(URL, headers=HEADERS, timeout=10)
        print(f"Status Code: {response.status_code}")

        if response.status_code != 200:
            print(
                f"Gagal mengakses halaman. Server merespon dengan status: {response.status_code}"
            )
            return

        soup = BeautifulSoup(response.text, "html.parser")
        posts = []

        # Mencari kontainer postingan di Picuki (mendukung beberapa variasi class)
        post_cards = soup.select(".post-item, .box-photo, .content-profile")

        if not post_cards:
            print(
                "Peringatan: Tidak ditemukan elemen postingan. Kemungkinan struktur HTML Picuki berubah atau diblokir."
            )
            # Debugging kecil untuk melihat judul halaman
            print("Judul Halaman:", soup.title.string if soup.title else "No Title")

        for card in post_cards:
            try:
                link_elem = card.select_one("a.photo, a")
                link = link_elem["href"] if link_elem and "href" in link_elem.attrs else ""

                img_tag = card.select_one("img.post-image, img")
                img_url = img_tag["src"] if img_tag and "src" in img_tag.attrs else ""

                caption_tag = card.select_one(".photo-description, .text")
                caption = caption_tag.text.strip() if caption_tag else ""

                posts.append(
                    {
                        "link": link,
                        "image_url": img_url,
                        "caption": caption,
                    }
                )
            except Exception as e:
                print(f"Error parsing item: {e}")
                continue

        # Simpan ke folder data
        os.makedirs("data", exist_ok=True)
        file_path = "data/posts.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(posts, f, ensure_ascii=False, indent=4)

        print(f"Berhasil menyimpan {len(posts)} data ke {file_path}")

    except Exception as e:
        print(f"Terjadi kesalahan koneksi atau eksekusi: {e}")


if __name__ == "__main__":
    scrape_picuki()
