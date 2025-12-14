#!/usr/bin/env python3
import csv
import os
import re
import sys
import time
from urllib.parse import urlparse

import requests

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"


def slugify(s: str) -> str:
    s = (s or "").strip()
    s = re.sub(r"\s+", "_", s)
    s = re.sub(r"[^a-zA-Z0-9_.-]+", "", s)
    return (s[:180] or "doc").strip("._-")


def choose_url(row: dict) -> str:
    # Preferir o link oficial direto (PDF/download etc.)
    for key in ("official_link", "raw_url"):
        v = (row.get(key) or "").strip()
        if v:
            return v
    return ""


def choose_title(row: dict, i: int) -> str:
    for key in ("doc_title", "raw_title", "official_domain", "issuer"):
        v = (row.get(key) or "").strip()
        if v:
            return v
    return f"doc_{i}"


def pick_ext(url: str, content_type: str) -> str:
    path = urlparse(url).path
    ext = os.path.splitext(path)[1].lower()
    if ext in [".pdf", ".htm", ".html", ".txt", ".doc", ".docx"]:
        return ext
    if "pdf" in (content_type or "").lower():
        return ".pdf"
    if "html" in (content_type or "").lower():
        return ".html"
    if "text/plain" in (content_type or "").lower():
        return ".txt"
    return ".bin"


def main():
    if len(sys.argv) < 3:
        print("Usage: python import_data.py <csv_path> <out_dir>")
        sys.exit(1)

    csv_path = sys.argv[1]
    out_dir = sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)

    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    sess = requests.Session()
    sess.headers.update({"User-Agent": UA})

    for i, row in enumerate(rows, start=1):
        url = choose_url(row)
        title = choose_title(row, i)
        if not url:
            print(f"[{i}] SKIP (no url): {title}")
            continue

        try:
            print(f"[{i}] GET {url}")
            resp = sess.get(url, allow_redirects=True, timeout=45)
            resp.raise_for_status()

            ct = resp.headers.get("Content-Type", "")
            ext = pick_ext(url, ct)

            # Nome do arquivo: prefixo com índice + título + tipo
            doc_type = slugify(row.get("doc_type") or "")
            name = slugify(title)
            base = f"{i:03d}_{name}"
            if doc_type:
                base += f"__{doc_type}"
            out_path = os.path.join(out_dir, base + ext)

            with open(out_path, "wb") as out:
                out.write(resp.content)

            print(f"     -> saved {out_path} ({len(resp.content)} bytes) [{ct}]")
            time.sleep(0.2)

        except Exception as e:
            print(f"[{i}] ERROR {url}: {e}")

    print("Done.")


if __name__ == "__main__":
    main()
