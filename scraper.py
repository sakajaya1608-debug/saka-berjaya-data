import json
import os
import requests
from bs4 import BeautifulSoup

# Target username & URL Picuki.site
USERNAME = "pemkab_okuselatan"
# URL pencarian atau langsung ke profil di picuki.site
URL = f"https://picuki.site/id/profile/{USERNAME}"
# Alternatif jika menggunakan form search utama: "https://picuki.site/id/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://picuki.site/id/",
}


def scrape_picuki_site():
    print(f"Mulai mengambil data dari {URL}...")
    try:
        response = requests.get(URL, headers=HEADERS, timeout=15)
        print(f"Status Code: {response.status_code}")

        if response.status_code != 200:
            print(f"Gagal mengakses halaman. Status: {response.status_code}")
            return

        soup = BeautifulSoup(response.text, "html.parser")
        posts = []

        # Mencari elemen kartu postingan di picuki.site
        # (Menyesuaikan dengan berbagai class umum pada platform viewer)
        post_cards = soup.select(
            ".post-item, .box-photo, .content-profile, .row .col-md-4"
        )

        if not post_cards:
            print(
                "Peringatan: Elemen postingan tidak ditemukan. Struktur HTML mungkin memerlukan eksekusi JavaScript (Selenium)."
            )
            # Simpan HTML untuk debugging jika masih kosong
            os.makedirs("data", exist_ok=True)
            with open("data/debug_page.html", "w", encoding="utf-8") as f:
                f.write(response.text)
            print("File HTML disimpan ke data/debug_page.html untuk diperiksa.")
            return

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

                caption_tag = card.select_one(
                    ".photo-description, .text, p, .caption"
                )
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

        # Simpan ke file JSON
        os.makedirs("data", exist_ok=True)
        file_path = "data/posts.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(posts, f, ensure_ascii=False, indent=4)

        print(
            f"Berhasil memproses! Menyimpan {len(posts)} data ke {file_path}"
        )

    except Exception as e:
        print(f"Terjadi kesalahan: {e}")


if __name__ == "__main__":
    scrape_picuki_site()
