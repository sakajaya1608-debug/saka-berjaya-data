"""
Scraper Instagram untuk berita Pemda OKU Selatan.
Menggunakan Playwright untuk meniru browser sungguhan.
"""

import json
import sys
import traceback
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

# ==========================================
# KONFIGURASI
# ==========================================
IG_USERNAME = "pemkab_okuselatan"
MAX_POSTS = 20
OUTPUT_FILE = "berita.json"


# ==========================================
# FUNGSI SCRAPING DENGAN PLAYWRIGHT
# ==========================================
def scrape():
    print(f"Mulai scraping Instagram @{IG_USERNAME} dengan Playwright...")

    berita_list = []

    with sync_playwright() as p:
        # Luncurkan browser Chromium (headless = tidak tampil GUI)
        browser = p.chromium.launch(headless=True)

        # Buat konteks browser dengan user-agent umum agar tidak dicurigai
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
            locale="id-ID",
        )

        page = context.new_page()

        try:
            # 1. Buka halaman profil Instagram
            url = f"https://www.instagram.com/{IG_USERNAME}/"
            print(f"Membuka {url} ...")
            page.goto(url, wait_until="networkidle", timeout=60000)
            page.wait_for_timeout(5000)  # tunggu tambahan agar JavaScript selesai

            # 2. Cari elemen postingan (link ke /p/ atau /reel/)
            # Selector ini mencari tautan postingan di halaman profil
            post_links = page.query_selector_all('a[href*="/p/"], a[href*="/reel/"]')

            # Kumpulkan shortcode unik
            shortcodes = set()
            for link in post_links[:MAX_POSTS * 2]:  # ambil lebih untuk jaga-jaga
                href = link.get_attribute("href")
                if href and ("/p/" in href or "/reel/" in href):
                    # Ekstrak shortcode dari URL, misal /p/ABC123/
                    parts = href.strip("/").split("/")
                    if len(parts) >= 2:
                        shortcodes.add(parts[-1])

            print(f"Ditemukan {len(shortcodes)} shortcode postingan.")

            # 3. Kunjungi setiap postingan untuk mengambil detail
            for sc in list(shortcodes)[:MAX_POSTS]:
                try:
                    post_url = f"https://www.instagram.com/p/{sc}/"
                    page.goto(post_url, wait_until="networkidle", timeout=30000)
                    page.wait_for_timeout(3000)

                    # Ambil caption dari meta description (paling stabil)
                    meta_desc = page.query_selector('meta[property="og:description"]')
                    caption = meta_desc.get_attribute("content") if meta_desc else ""

                    # Ambil URL gambar dari meta og:image
                    meta_img = page.query_selector('meta[property="og:image"]')
                    img_url = meta_img.get_attribute("content") if meta_img else ""

                    # Ambil judul dari caption (baris pertama)
                    judul = caption.split("\n")[0].strip() if caption else "(Tanpa judul)"
                    if len(judul) > 120:
                        judul = judul[:120] + "..."

                    berita_list.append({
                        "id": sc,
                        "judul": judul,
                        "caption": caption,
                        "url_gambar": img_url,
                        "url_post": f"https://www.instagram.com/p/{sc}/",
                        "timestamp": 0,  # Playwright tidak mudah ambil timestamp, bisa diisi manual
                        "likes": 0,
                        "comments": 0,
                    })
                    print(f"  ✓ Post {sc} diambil.")
                except Exception as e:
                    print(f"  ✗ Gagal ambil post {sc}: {e}")
                    continue

        except PlaywrightTimeout:
            print("ERROR: Timeout saat memuat halaman Instagram.")
        except Exception as e:
            print(f"ERROR: {e}")
            traceback.print_exc()
        finally:
            browser.close()

    print(f"Total berita berhasil diambil: {len(berita_list)}")
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
