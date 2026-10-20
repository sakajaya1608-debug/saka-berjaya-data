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

# Menggunakan Actor Resmi Apify
ACTOR_ID = "apify/instagram-scraper"

# 👇 COOKIE SESSIONID ANDA SUDAH DIMASUKKAN DI SINI
INSTAGRAM_SESSION_ID = "16909757083%3ApjfdS3Itnvcmcy%3A7%3AAYnTfD1dx_Wn6b9lY5F3uUgmDI5cDpOx5LeAC87LHw"

INSTAGRAM_URL = "https://www.instagram.com/pemkab_okuselatan/"
RESULTS_LIMIT = 5 

FIREBASE_DB_URL = "https://sakajaya-af9d5-default-rtdb.asia-southeast1.firebasedatabase.app"
FIREBASE_PATH = "berita_cache/posts"


# ============================================================
# FUNGSI UTAMA
# ============================================================

def main():
    print("=" * 60)
    print("SAKA BERJAYA — Instagram Scraper (Dengan Cookie)")
    print("=" * 60)

    if not APIFY_TOKEN:
        raise ValueError("APIFY_TOKEN tidak di-set!")
    if not FIREBASE_SERVICE_ACCOUNT:
        raise ValueError("FIREBASE_SERVICE_ACCOUNT tidak di-set!")

    print("\n[1/3] Menjalankan Apify Actor...")
    posts = run_apify_actor()
    
    valid_posts = [p for p in posts if isinstance(p, dict)]
    print(f"    ✅ Berhasil mengambil {len(valid_posts)} post dari Instagram")

    if not valid_posts:
        print("    ⚠️ Tidak ada post yang diambil. Batalkan.")
        return

    print("\n[2/3] Memproses data...")
    cleaned = [clean_post(p) for p in valid_posts]
    
    cleaned = [p for p in cleaned if p.get("id")]
    print(f"    ✅ {len(cleaned)} post valid siap disimpan")

    if not cleaned:
        print("    ⚠️ Semua post tidak memiliki ID valid. Batalkan.")
        return

    print("\n[3/3] Menyimpan ke Firebase (Mode Komulatif)...")
    save_to_firebase(cleaned)
    print("    ✅ Data berhasil disimpan/diperbarui")

    print("\n" + "=" * 60)
    print("SELESAI")
    print("=" * 60)


def run_apify_actor():
    client = ApifyClient(APIFY_TOKEN)
    
    # Format input dengan Cookie
    run_input = {
        "directUrls": [INSTAGRAM_URL],
        "resultsType": "posts",
        "resultsLimit": RESULTS_LIMIT,
        "proxyConfiguration": {
            "useApifyProxy": True,
            "apifyProxyGroups": ["RESIDENTIAL"]
        },
        # Menyisipkan cookie sessionid
        "cookies": [
            {
                "name": "sessionid",
                "value": INSTAGRAM_SESSION_ID,
                "domain": ".instagram.com",
                "path": "/"
            }
        ]
    }

    run = client.actor(ACTOR_ID).call(run_input=run_input)

    if not run or run.get("status") != "SUCCEEDED":
        raise RuntimeError(f"Apify Actor gagal: {run.get('status')}")

    dataset_id = run.get("defaultDatasetId")
    return list(client.dataset(dataset_id).iterate_items())


def clean_post(post):
    post_id = post.get("id") or post.get("shortCode") or post.get("shortcode") or ""
    
    return {
        "id": post_id,
        "caption": post.get("caption") or "",
        "imageUrl": post.get("displayUrl") or post.get("imageUrl") or "",
        "postUrl": post.get("url") or f"https://www.instagram.com/p/{post_id}/",
        "timestamp": post.get("timestamp") or int(time.time()),
        "likeCount": post.get("likesCount") or post.get("likes") or 0,
        "commentCount": post.get("commentsCount") or post.get("comments") or 0,
        "ownerUsername": post.get("ownerUsername") or "pemkab_okuselatan",
    }


def save_to_firebase(posts):
    cred = credentials.Certificate(json.loads(FIREBASE_SERVICE_ACCOUNT))
    firebase_admin.initialize_app(cred, {"databaseURL": FIREBASE_DB_URL})

    meta_ref = db.reference("berita_cache")
    meta_ref.update({
        "updatedAt": int(time.time() * 1000),
        "updatedAtISO": datetime.now(timezone.utc).isoformat(),
    })

    updates = {}
    for p in posts:
        if p["id"]:
            updates[p["id"]] = p

    if not updates:
        print("    ⚠️ Tidak ada data valid untuk disimpan ke posts.")
        return

    posts_ref = db.reference(FIREBASE_PATH)
    posts_ref.update(updates)
    
    print(f"    Path Firebase: /{FIREBASE_PATH}")
    print(f"    Jumlah post diproses: {len(updates)}")


if __name__ == "__main__":
    main()
