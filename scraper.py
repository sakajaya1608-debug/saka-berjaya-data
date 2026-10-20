import os
import json
import time
from datetime import datetime, timezone

import firebase_admin
from firebase_admin import credentials, db
from apify_client import ApifyClient

# ============================================================
# KONFIGURASI
# ============================================================

APIFY_TOKEN = os.environ.get("APIFY_TOKEN")
FIREBASE_SERVICE_ACCOUNT = os.environ.get("FIREBASE_SERVICE_ACCOUNT")

# Nama Actor Instagram Scraper
ACTOR_ID = "apify/instagram-scraper"

# URL target
INSTAGRAM_URL = "https://www.instagram.com/pemkab_okuselatan/"

# Jumlah post yang diambil per scraping
RESULTS_LIMIT = 12

# URL Firebase Realtime Database
FIREBASE_DB_URL = "https://sakajaya-af9d5-default-rtdb.asia-southeast1.firebasedatabase.app"

# Path di Firebase
FIREBASE_PATH = "berita_cache/posts"


# ============================================================
# FUNGSI UTAMA
# ============================================================

def main():
    print("=" * 60)
    print("SAKA BERJAYA — Instagram Scraper (Komulatif)")
    print("=" * 60)

    if not APIFY_TOKEN:
        raise ValueError("APIFY_TOKEN tidak di-set!")
    if not FIREBASE_SERVICE_ACCOUNT:
        raise ValueError("FIREBASE_SERVICE_ACCOUNT tidak di-set!")

    # 1. Ambil data dari Apify
    print("\n[1/3] Menjalankan Apify Actor...")
    posts = run_apify_actor()
    print(f"    ✅ Berhasil mengambil {len(posts)} post dari Instagram")

    if not posts:
        print("    ⚠️ Tidak ada post yang diambil. Batalkan.")
        return

    # 2. Proses data
    print("\n[2/3] Memproses data...")
    cleaned = [clean_post(p) for p in posts]
    
    # 3. Simpan ke Firebase secara komulatif (Update per ID)
    print("\n[3/3] Menyimpan ke Firebase (Mode Komulatif)...")
    save_to_firebase(cleaned)
    print("    ✅ Data berhasil disimpan/diperbarui")

    print("\n" + "=" * 60)
    print("SELESAI")
    print("=" * 60)


def run_apify_actor():
    client = ApifyClient(APIFY_TOKEN)
    run_input = {
        "directUrls": [INSTAGRAM_URL],
        "resultsType": "posts",
        "resultsLimit": RESULTS_LIMIT,
        "proxyConfiguration": {"useApifyProxy": True},
    }

    run = client.actor(ACTOR_ID).call(run_input=run_input)

    if not run or run.get("status") != "SUCCEEDED":
        raise RuntimeError(f"Apify Actor gagal: {run.get('status')}")

    dataset_id = run.get("defaultDatasetId")
    return list(client.dataset(dataset_id).iterate_items())


def clean_post(post):
    """Bersihkan & standarisasi field post."""
    return {
        "id": post.get("id") or post.get("shortCode") or "",
        "caption": post.get("caption") or "",
        "imageUrl": post.get("displayUrl") or post.get("imageUrl") or "",
        "postUrl": post.get("url") or f"https://www.instagram.com/p/{post.get('shortCode', '')}/",
        "timestamp": post.get("timestamp") or int(time.time()),
        "likeCount": post.get("likesCount") or post.get("likes") or 0,
        "commentCount": post.get("commentsCount") or post.get("comments") or 0,
        "ownerUsername": post.get("ownerUsername") or "pemkab_okuselatan",
    }


def save_to_firebase(posts):
    """Simpan data ke Firebase secara komulatif (tidak menimpa ID lama)."""
    cred = credentials.Certificate(json.loads(FIREBASE_SERVICE_ACCOUNT))
    firebase_admin.initialize_app(cred, {"databaseURL": FIREBASE_DB_URL})

    # 1. Update metadata waktu sync
    meta_ref = db.reference("berita_cache")
    meta_ref.update({
        "updatedAt": int(time.time() * 1000),
        "updatedAtISO": datetime.now(timezone.utc).isoformat(),
    })

    # 2. Simpan/Update setiap post berdasarkan ID-nya
    posts_ref = db.reference(FIREBASE_PATH)
    updates = {}
    
    for p in posts:
        if p["id"]:
            # Gunakan ID post sebagai key di Firebase
            updates[p["id"]] = p

    # Simpan sekaligus (update akan menambahkan jika ID baru, atau menimpa jika ID sama)
    posts_ref.update(updates)
    
    print(f"    Path Firebase: /{FIREBASE_PATH}")
    print(f"    Jumlah post diproses: {len(updates)}")


if __name__ == "__main__":
    main()
