#!/usr/bin/env python3
"""Create a SHA-256 manifest for all deliverable files in the pack.

The manifest files themselves are excluded to avoid circular hashing.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime
from pathlib import Path

EXCLUDE = {
    "06_quality/package_manifest.csv",
    "06_quality/package_manifest.sha256",
    "06_quality/package_manifest_summary.json",
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("pack_dir", type=Path)
    args = parser.parse_args()
    root = args.pack_dir.resolve()
    q = root / "06_quality"
    q.mkdir(parents=True, exist_ok=True)
    rows = []
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = path.relative_to(root).as_posix()
        if rel in EXCLUDE:
            continue
        rows.append({"relative_path": rel, "size_bytes": path.stat().st_size, "sha256": sha256_file(path)})
    manifest = q / "package_manifest.csv"
    with manifest.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["relative_path", "size_bytes", "sha256"])
        w.writeheader(); w.writerows(rows)
    manifest_hash = sha256_file(manifest)
    (q / "package_manifest.sha256").write_text(f"{manifest_hash}  package_manifest.csv\n", encoding="utf-8")
    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "file_count_excluding_manifest_files": len(rows),
        "total_size_bytes_excluding_manifest_files": sum(r["size_bytes"] for r in rows),
        "manifest_sha256": manifest_hash,
    }
    (q / "package_manifest_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
