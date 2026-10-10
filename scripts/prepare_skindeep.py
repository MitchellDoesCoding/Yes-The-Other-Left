#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from yes_other_left.dataset import index_downloads, load_ground_truth, resolve_image, sha256_file


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate an authorized local SkinDeep-542 download.")
    parser.add_argument("--ground-truth", required=True, type=Path)
    parser.add_argument("--images", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    records = load_ground_truth(args.ground_truth)
    images = index_downloads(args.images)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    matched = 0
    rows = []
    for record in records:
        path = resolve_image(record, images)
        if path:
            matched += 1
        rows.append(
            {
                "image_id": record.image_id,
                "original_filename": record.original_filename,
                "local_path": str(path.resolve()) if path else "",
                "sha256": sha256_file(path) if path else "",
                "status": "matched" if path else "missing",
            }
        )

    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps({"expected": len(records), "matched": matched, "missing": len(records) - matched, "manifest": str(args.output)}))
    return 0 if matched == len(records) else 2


if __name__ == "__main__":
    raise SystemExit(main())
