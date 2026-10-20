"""
Script untuk scraping Instagram @pemkab_okuselatan via Apify
dan menyimpan hasilnya ke Firebase Realtime Database.

Berjalan otomatis via GitHub Actions setiap hari jam 06:00 WIB.
"""

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

# Nama Actor Instagram Scraper (bisa diganti)
ACTOR_ID = "apify/instagram-scraper"

# URL target
INSTAGRAM_URL = "https://www.instagram.com/pemkab_okuselatan/"

# Jumlah post yang diambil
RESULTS_LIMIT = 12

# URL Firebase Realtime Database
FIREBASE_DB_URL = "https://sakajaya-af9d5-default-rtdb.asia-southeast1.firebasedatabase.app"

# Path di Firebase
FIREBASE_PATH = "berita_cache"


# ============================================================
# FUNGSI UTAMA
# ============================================================

def main():
    print("=" * 60)
    print("SAKA BERJAYA — Instagram Scraper")
    print("=" * 60)

    # Validasi environment
    if not APIFY_TOKEN:
        raise ValueError("APIFY_TOKEN tidak di-set di environment!")
    if not FIREBASE_SERVICE_ACCOUNT:
        raise ValueError("FIREBASE_SERVICE_ACCOUNT tidak di-set di environment!")

    # ----------------------------------------
    # 1. Jalankan Apify Actor
    # ----------------------------------------
    print("\n[1/3] Menjalankan Apify Actor...")
    posts = run_apify_actor()
    print(f"    ✅ Berhasil mengambil {len(posts)} post dari Instagram")

    if not posts:
        print("    ⚠️  Tidak ada post yang diambil. Batalkan.")
        return

    # ----------------------------------------
    # 2. Parse & bersihkan data
    # ----------------------------------------
    print("\n[2/3] Memproses data...")
    cleaned = [clean_post(p) for p in posts]
    print(f"    ✅ {len(cleaned)} post siap disimpan")

    # ----------------------------------------
    # 3. Simpan ke Firebase
    # ----------------------------------------
    print("\n[3/3] Menyimpan ke Firebase Realtime Database...")
    save_to_firebase(cleaned)
    print("    ✅ Data berhasil disimpan")

    print("\n" + "=" * 60)
    print("SELESAI")
    print("=" * 60)


def run_apify_actor():
    """Menjalankan Apify Actor dan mengembalikan daftar post."""
    client = ApifyClient(APIFY_TOKEN)

    # Input sesuai skema Actor Instagram Scraper
    run_input = {
        "directUrls": [INSTAGRAM_URL],
        "resultsType": "posts",
        "resultsLimit": RESULTS_LIMIT,
        "proxyConfiguration": {
            "useApifyProxy": True,
        },
    }

    print(f"    Actor: {ACTOR_ID}")
    print(f"    Target: {INSTAGRAM_URL}")
    print(f"    Limit: {RESULTS_LIMIT} post")

    # Jalankan Actor
    run = client.actor(ACTOR_ID).call(run_input=run_input)

    if not run:
        raise RuntimeError("Apify Actor gagal dijalankan")

    print(f"    Run ID: {run.get('id')}")
    print(f"    Status: {run.get('status')}")

    if run.get("status") != "SUCCEEDED":
        raise RuntimeError(f"Apify Actor tidak sukses: {run.get('status')}")

    # Ambil hasil dari dataset
    dataset_id = run.get("defaultDatasetId")
    items = list(client.dataset(dataset_id).iterate_items())

    return items


def clean_post(post):
    """Bersihkan & standarisasi field post."""
    # Coba berbagai kemungkinan nama field
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
    """Simpan data ke Firebase Realtime Database."""
    # Init Firebase
    cred = credentials.Certificate(json.loads(FIREBASE_SERVICE_ACCOUNT))
    firebase_admin.initialize_app(cred, {"databaseURL": FIREBASE_DB_URL})

    # Data yang akan disimpan
    data = {
        "updatedAt": int(time.time() * 1000),
        "updatedAtISO": datetime.now(timezone.utc).isoformat(),
        "count": len(posts),
        "posts": {p["id"]: p for p in posts if p["id"]},
    }

    # Simpan ke Firebase
    ref = db.reference(FIREBASE_PATH)
    ref.set(data)

    print(f"    Path Firebase: /{FIREBASE_PATH}")
    print(f"    Jumlah post: {len(posts)}")


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
