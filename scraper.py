"""
Scraper Instagram untuk berita Pemda OKU Selatan.
Menggunakan library instagram-hindsight (scraping tanpa login).
"""

import json
import sys
import traceback

try:
    from instagram_hindsight import scrape_account
except ImportError:
    print("ERROR: library instagram-hindsight tidak terinstall.")
    sys.exit(1)

# ==========================================
# KONFIGURASI
# ==========================================
# GANTI dengan username Instagram Pemda OKU Selatan yang benar
IG_USERNAME = "pemkab_okuselatan"

MAX_POSTS = 20  # jumlah berita yang diambil

OUTPUT_FILE = "berita.json"


# ==========================================
# FUNGSI SCRAPING
# ==========================================
def scrape():
    print(f"Scraping Instagram @{IG_USERNAME} ...")

    try:
        data = scrape_account(IG_USERNAME, max_pages=2)
    except Exception as e:
        print(f"ERROR scraping: {e}")
        traceback.print_exc()
        return []

    posts = data.get("posts", [])
    print(f"Ditemukan {len(posts)} post mentah.")

    berita_list = []
    for post in posts[:MAX_POSTS]:
        try:
            shortcode = post.get("shortcode") or post.get("code") or ""
            caption = post.get("caption") or ""
            display_url = post.get("display_url") or post.get("thumbnail_url") or ""

            # Ambil judul dari baris pertama caption
            judul = caption.split("\n")[0].strip() if caption else "(Tanpa judul)"
            if len(judul) > 120:
                judul = judul[:120] + "..."

            timestamp = post.get("taken_at_timestamp") or post.get("taken_at") or 0

            berita_list.append({
                "id": shortcode,
                "judul": judul,
                "caption": caption,
                "url_gambar": display_url,
                "url_post": f"https://www.instagram.com/p/{shortcode}/",
                "timestamp": timestamp,
                "likes": post.get("like_count", 0),
                "comments": post.get("comment_count", 0),
            })
        except Exception as e:
            print(f"Skip post: {e}")
            continue

    print(f"Berhasil parsing {len(berita_list)} berita.")
    return berita_list


# ==========================================
# MAIN
# ==========================================
def main():
    berita = scrape()

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(berita, f, ensure_ascii=False, indent=2)

    print(f"✅ Disimpan ke {OUTPUT_FILE} ({len(berita)} berita).")


if __name__ == "__main__":
    main()
