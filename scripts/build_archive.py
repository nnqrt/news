"""Promote the latest legacy edition to index.html, wire archive.js, and build legacy/editions.json."""

from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timezone, timedelta

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEGACY_DIR = os.path.join(REPO_ROOT, "legacy")
KST = timezone(timedelta(hours=9))
ARCHIVE_SCRIPT_RE = re.compile(r'\s*<script src="(?:\.\./)?archive\.js"[^>]*></script>\s*')


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


def detect_root_index_id(html: str) -> str | None:
    m = re.search(r"(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일.*?(\d{1,2}):(\d{2})\s*KST", html[:4000], re.DOTALL)
    if m:
        y, mo, d, h, mi = m.groups()
        return f"{int(y):04d}{int(mo):02d}{int(d):02d}{int(h):02d}{int(mi):02d}"
    return None


def strip_archive_script(html: str) -> str:
    return ARCHIVE_SCRIPT_RE.sub("", html).strip()


def content_digest(html: str) -> str:
    return hashlib.sha256(strip_archive_script(html).encode("utf-8")).hexdigest()


def apply_archive_script(html: str, script_src: str) -> str:
    tag = f'<script src="{script_src}" defer></script>'
    if tag in html and ARCHIVE_SCRIPT_RE.sub("", html) != html:
        # Check whether only the exact desired tag is present
        others = [m.group(0) for m in ARCHIVE_SCRIPT_RE.finditer(html)]
        if len(others) == 1 and tag in others[0]:
            return html

    cleaned = ARCHIVE_SCRIPT_RE.sub("\n", html)
    if "</body>" in cleaned.lower():
        return re.sub(r"</body>", f"{tag}\n</body>", cleaned, count=1, flags=re.IGNORECASE)
    return cleaned.rstrip() + f"\n{tag}\n"


def write_if_changed(file_path: str, content: str) -> bool:
    if os.path.exists(file_path):
        with open(file_path, encoding="utf-8") as f:
            if f.read() == content:
                return False
    with open(file_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    return True


def collect_legacy_files() -> dict[str, str]:
    legacy_files: dict[str, str] = {}
    for name in sorted(os.listdir(LEGACY_DIR)):
        m = re.match(r"^index_(\d{12})\.html$", name)
        if m:
            legacy_files[m.group(1)] = os.path.join(LEGACY_DIR, name)
    return legacy_files


def main() -> None:
    wired = 0
    promoted = False
    archived_root = False

    legacy_files = collect_legacy_files()
    legacy_contents: dict[str, str] = {}
    legacy_digests: set[str] = set()
    for ed_id, full_path in sorted(legacy_files.items()):
        with open(full_path, encoding="utf-8") as f:
            raw_html = f.read()
        legacy_contents[ed_id] = raw_html
        legacy_digests.add(content_digest(raw_html))

    root_index = os.path.join(REPO_ROOT, "index.html")

    # Preserve existing root index.html in legacy/ only if its content is not already archived
    if os.path.exists(root_index):
        with open(root_index, encoding="utf-8") as f:
            root_html = f.read()
        if content_digest(root_html) not in legacy_digests:
            root_id = detect_root_index_id(root_html)
            if root_id and root_id not in legacy_files:
                legacy_copy_path = os.path.join(LEGACY_DIR, f"index_{root_id}.html")
                legacy_copy_html = apply_archive_script(root_html, "../archive.js")
                if write_if_changed(legacy_copy_path, legacy_copy_html):
                    archived_root = True
                legacy_files[root_id] = legacy_copy_path
                legacy_contents[root_id] = legacy_copy_html
                legacy_digests.add(content_digest(legacy_copy_html))

    # Wire ../archive.js into every legacy edition
    for ed_id, full_path in sorted(legacy_files.items()):
        updated_html = apply_archive_script(legacy_contents[ed_id], "../archive.js")
        if write_if_changed(full_path, updated_html):
            wired += 1
        legacy_contents[ed_id] = updated_html

    editions = []
    if legacy_files:
        latest_id = max(legacy_files.keys())
        latest_html_for_root = apply_archive_script(legacy_contents[latest_id], "archive.js")
        if write_if_changed(root_index, latest_html_for_root):
            promoted = True

        editions.append(extract_meta(latest_html_for_root, "index.html", latest_id, is_current=True))
        for ed_id in sorted(legacy_files.keys(), reverse=True):
            if ed_id == latest_id:
                continue
            name = os.path.basename(legacy_files[ed_id])
            editions.append(extract_meta(legacy_contents[ed_id], f"legacy/{name}", ed_id, is_current=False))
    elif os.path.exists(root_index):
        with open(root_index, encoding="utf-8") as f:
            root_html = f.read()
        updated_root = apply_archive_script(root_html, "archive.js")
        if write_if_changed(root_index, updated_root):
            wired += 1
        fallback_id = detect_root_index_id(updated_root) or datetime.now(KST).strftime("%Y%m%d%H%M")
        editions.append(extract_meta(updated_root, "index.html", fallback_id, is_current=True))

    manifest = {
        "generatedAt": datetime.now(KST).isoformat(),
        "count": len(editions),
        "editions": editions,
    }
    manifest_path = os.path.join(LEGACY_DIR, "editions.json")
    manifest_text = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    write_if_changed(manifest_path, manifest_text)

    print(
        f"Generated {manifest_path} with {len(editions)} editions "
        f"(promoted={promoted}, archived_root={archived_root}, wired={wired})."
    )


if __name__ == "__main__":
    main()
