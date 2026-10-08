"""
Scraper Instagram untuk berita Pemda OKU Selatan.
Menggunakan library instaloader dengan login untuk menghindari blokir.
"""

import json
import sys
import traceback
import os
import instaloader

try:
    from instaloader import Profile, Post
except ImportError:
    print("ERROR: library instaloader tidak terinstall.")
    sys.exit(1)

# ==========================================
# KONFIGURASI
# ==========================================
# Username Instagram Pemda OKU Selatan
IG_USERNAME = "pemkab_okuselatan"

# Kredensial login diambil dari Environment Variables
IG_LOGIN_USER = os.getenv("IG_LOGIN_USER")
IG_LOGIN_PASS = os.getenv("IG_LOGIN_PASS")

MAX_POSTS = 20
OUTPUT_FILE = "berita.json"

# ==========================================
# FUNGSI SCRAPING
# ==========================================
def scrape():
    print(f"Memulai scraping Instagram @{IG_USERNAME} ...")
    
    # Inisialisasi Instaloader
    L = instaloader.Instaloader()
    
    try:
        # Login menggunakan akun dari environment variables
        if IG_LOGIN_USER and IG_LOGIN_PASS:
            print(f"Login sebagai @{IG_LOGIN_USER} ...")
            L.login(IG_LOGIN_USER, IG_LOGIN_PASS)
        else:
            print("Peringatan: Tidak ada kredensial login. Mencoba akses anonim (risiko tinggi diblokir).")
        
        # Ambil profil target
        profile = Profile.from_username(L.context, IG_USERNAME)
        print(f"Berhasil mengambil profil @{IG_USERNAME}.")
        
        # Ambil postingan
        posts = profile.get_posts()
        
        berita_list = []
        for i, post in enumerate(posts):
            if i >= MAX_POSTS:
                break
                
            try:
                shortcode = post.shortcode
                caption = post.caption or ""
                display_url = post.url or ""
                
                # Ambil judul dari baris pertama caption
                judul = caption.split("\n")[0].strip() if caption else "(Tanpa judul)"
                if len(judul) > 120:
                    judul = judul[:120] + "..."
                
                # Timestamp dalam format Unix (detik)
                timestamp = int(post.date_utc.timestamp()) if post.date_utc else 0
                
                berita_list.append({
                    "id": shortcode,
                    "judul": judul,
                    "caption": caption,
                    "url_gambar": display_url,
                    "url_post": f"https://www.instagram.com/p/{shortcode}/",
                    "timestamp": timestamp,
                    "likes": post.likes,
                    "comments": post.comments,
                })
            except Exception as e:
                print(f"Skip post: {e}")
                continue
        
        print(f"Berhasil parsing {len(berita_list)} berita.")
        return berita_list
        
    except Exception as e:
        print(f"ERROR scraping: {e}")
        traceback.print_exc()
        return []

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
