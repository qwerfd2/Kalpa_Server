import os
import json
import requests
import base64
import gzip
import io
import re

from concurrent.futures import ThreadPoolExecutor, as_completed

asset_dirs = [
    "mapfiles", "asset/text", "asset/bundle/kalpa_mobile/remote_v1/Android", "audfiles",
    "midifiles", "covfiles", "iconfiles", "eventbanner", "notice"
]

BASE_URL = "https://d1h9358u1aon5f.cloudfront.net/"

FILE = "catalog.bin"
with open(FILE, "rb") as f:
    data = f.read()

pattern = rb"pcstoryremote_[^/\x00\r\n]*?\.bundle"
matches = re.findall(pattern, data)
PC_ASSET_ANDROID = [m.decode("ascii") for m in matches]

def ensure_dirs():
    for d in asset_dirs:
        os.makedirs(d, exist_ok=True)

def download_file(session, url, dest_path):
    try:
        r = session.get(url, timeout=30)
        r.raise_for_status()
        with open(dest_path, "wb") as f:
            f.write(r.content)
        return f"Downloaded: {dest_path}"
    except Exception as e:
        return f"Failed {url}: {e}"

def run_downloads(tasks, max_workers=8):
    with requests.Session() as session:
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = [
                pool.submit(download_file, session, url, path)
                for url, path in tasks
            ]
            for f in as_completed(futures):
                print(f.result())

def main():
    ensure_dirs()

    # Decode JSON
    with open("b64.txt", "r") as f:
        binary_data = base64.b64decode(f.read())

    with gzip.open(io.BytesIO(binary_data), "rt", encoding="utf-8") as gz:
        data = json.loads(gz.read())

    tasks = []

    # Tracks
    for track in data["tracks"]:
        for key in ("audioFileName", "audioPreviewFileName"):
            name = track.get(key)
            if name:
                path = f"audfiles/{name}"
                if not os.path.exists(path):
                    tasks.append((f"{BASE_URL}audfiles/{name}", path))

        midi = track.get("midiFileName")
        if midi and midi != "NULL":
            path = f"midifiles/{midi}"
            if not os.path.exists(path):
                tasks.append((f"{BASE_URL}midifiles/{midi}", path))

        for key in ("coverFileName", "blurredCoverFileName", "thumbnailFileName"):
            name = track.get(key)
            if name:
                path = f"covfiles/{name}"
                if not os.path.exists(path):
                    tasks.append((f"{BASE_URL}covfiles/{name}", path))

    # Maps
    for m in data["maps"]:
        name = m.get("mapFileName")
        if name:
            path = f"mapfiles/{name}"
            if not os.path.exists(path):
                tasks.append((f"{BASE_URL}mapfiles/{name}", path))

    # Event banners
    for b in data["eventBanners"]:
        name = b.get("fileName")
        if name:
            path = f"eventbanner/{name}"
            if not os.path.exists(path):
                tasks.append((f"{BASE_URL}eventbanner/{name}", path))

    for file in PC_ASSET_ANDROID:
        path = f"asset/bundle/kalpa_mobile/remote_v1/Android/{file}"
        if not os.path.exists(path):
            tasks.append((f"{BASE_URL}asset/bundle/kalpa_mobile/remote_v1/Android/{file}", path))

    # Misc
    if data.get("packIconAtlasFilename"):
        name = data["packIconAtlasFilename"]
        path = f"iconfiles/{name}"
        if not os.path.exists(path):
            tasks.append((f"{BASE_URL}iconfiles/{name}", path))

    if data.get("localizationEntryFilename"):
        name = data["localizationEntryFilename"]
        path = f"asset/text/{name}"
        if not os.path.exists(path):
            tasks.append((f"{BASE_URL}asset/text/{name}", path))

    print(f"Starting {len(tasks)} downloads...")
    run_downloads(tasks, max_workers=8)

if __name__ == "__main__":
    main()
