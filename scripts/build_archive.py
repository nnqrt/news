"""Build legacy/editions.json and ensure archive.js is wired into every edition HTML."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone, timedelta

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEGACY_DIR = os.path.join(REPO_ROOT, "legacy")
KST = timezone(timedelta(hours=9))


def extract_meta(html: str, rel_path: str, edition_id: str, is_current: bool = False) -> dict:
    title_m = re.search(r"<title>(.*?)</title>", html, re.DOTALL | re.IGNORECASE)
    title = re.sub(r"\s+", " ", title_m.group(1)).strip() if title_m else rel_path

    h1_m = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.DOTALL | re.IGNORECASE)
    headline = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", h1_m.group(1))).strip() if h1_m else title

    deck_m = re.search(r'<p class="(?:masthead-deck|deck)"[^>]*>(.*?)</p>', html, re.DOTALL | re.IGNORECASE)
    deck = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", deck_m.group(1))).strip() if deck_m else ""
    if len(deck) > 160:
        deck = deck[:157].rstrip() + "..."

    fmt = "v2" if "dateline-actions" in html else "v1"
    label = f"{edition_id[:4]}-{edition_id[4:6]}-{edition_id[6:8]} {edition_id[8:10]}:{edition_id[10:12]} KST"

    return {
        "id": edition_id,
        "label": label,
        "path": rel_path.replace("\\", "/"),
        "title": title,
        "headline": headline,
        "deck": deck,
        "format": fmt,
        "isCurrent": is_current,
    }


def detect_root_index_id(html: str) -> str:
    m = re.search(r"(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일.*?(\d{1,2}):(\d{2})\s*KST", html[:4000], re.DOTALL)
    if m:
        y, mo, d, h, mi = m.groups()
        return f"{int(y):04d}{int(mo):02d}{int(d):02d}{int(h):02d}{int(mi):02d}"
    return datetime.now(KST).strftime("%Y%m%d%H%M")


def ensure_archive_script(file_path: str, script_src: str) -> bool:
    with open(file_path, encoding="utf-8") as f:
        html = f.read()

    # Remove any older injected archive.js tag with different path if needed, then ensure exact tag
    tag = f'<script src="{script_src}" defer></script>'
    if tag in html:
        return False

    cleaned = re.sub(r'\s*<script src="(?:\.\./)?archive\.js"[^>]*></script>\s*', "\n", html)
    if "</body>" in cleaned.lower():
        new_html = re.sub(r"</body>", f"{tag}\n</body>", cleaned, count=1, flags=re.IGNORECASE)
    else:
        new_html = cleaned.rstrip() + f"\n{tag}\n"

    with open(file_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(new_html)
    return True


def main() -> None:
    editions = []
    wired = 0

    root_index = os.path.join(REPO_ROOT, "index.html")
    if os.path.exists(root_index):
        if ensure_archive_script(root_index, "archive.js"):
            wired += 1
        with open(root_index, encoding="utf-8") as f:
            root_html = f.read()
        root_id = detect_root_index_id(root_html)
        editions.append(extract_meta(root_html, "index.html", root_id, is_current=True))

    for name in sorted(os.listdir(LEGACY_DIR)):
        m = re.match(r"^index_(\d{12})\.html$", name)
        if not m:
            continue
        ed_id = m.group(1)
        full_path = os.path.join(LEGACY_DIR, name)
        if ensure_archive_script(full_path, "../archive.js"):
            wired += 1
        with open(full_path, encoding="utf-8") as f:
            html = f.read()
        editions.append(extract_meta(html, f"legacy/{name}", ed_id, is_current=False))

    editions.sort(key=lambda e: (e["id"], 1 if e["isCurrent"] else 0), reverse=True)

    manifest = {
        "generatedAt": datetime.now(KST).isoformat(),
        "count": len(editions),
        "editions": editions,
    }
    manifest_path = os.path.join(LEGACY_DIR, "editions.json")
    with open(manifest_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"Generated {manifest_path} with {len(editions)} editions (wired archive.js in {wired} files).")


if __name__ == "__main__":
    main()
