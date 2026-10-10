from __future__ import annotations

import csv
import hashlib
from dataclasses import dataclass
from pathlib import Path

from .skindeep_masking import IMAGE_EXTENSIONS


@dataclass(frozen=True)
class SkinDeepRecord:
    image_id: str
    original_filename: str
    master_filename: str
    body_part: str
    laterality: str
    determinability: str


def normalize_label(laterality: str, determinability: str = "") -> str:
    label = str(laterality or "").strip().casefold().replace("-", "_").replace(" ", "_")
    determ = str(determinability or "").strip().casefold()
    if label in {"left", "right"}:
        return label
    if label in {"bilateral", "midline", "not_applicable", "unable_to_determine", "utd"}:
        return "utd"
    if any(token in determ for token in ("bilateral", "midline", "unable", "not_determinable")):
        return "utd"
    raise ValueError(f"Unrecognized laterality label: {laterality!r} ({determinability!r})")


def load_ground_truth(path: str | Path) -> list[SkinDeepRecord]:
    records: list[SkinDeepRecord] = []
    seen: set[str] = set()
    with Path(path).open("r", newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            image_id = str(row.get("image_id") or "").strip().upper()
            if not image_id or image_id in seen:
                raise ValueError(f"Missing or duplicate image_id: {image_id!r}")
            seen.add(image_id)
            records.append(
                SkinDeepRecord(
                    image_id=image_id,
                    original_filename=str(row.get("original_skindeep_filename") or row.get("source_filename") or "").strip(),
                    master_filename=str(row.get("master_filename") or f"{image_id}.jpg").strip(),
                    body_part=str(row.get("body_part") or "").strip(),
                    laterality=normalize_label(str(row.get("laterality") or ""), str(row.get("laterality_determinability") or "")),
                    determinability=str(row.get("laterality_determinability") or "").strip(),
                )
            )
    return records


def index_downloads(image_dir: str | Path) -> dict[str, list[Path]]:
    index: dict[str, list[Path]] = {}
    for path in Path(image_dir).rglob("*"):
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS:
            index.setdefault(path.stem.casefold(), []).append(path)
    return index


def resolve_image(record: SkinDeepRecord, image_index: dict[str, list[Path]]) -> Path | None:
    candidates = {
        Path(record.original_filename).stem.casefold(),
        Path(record.master_filename).stem.casefold(),
        record.image_id.casefold(),
    }
    hits = {path for key in candidates for path in image_index.get(key, [])}
    if len(hits) > 1:
        raise ValueError(f"Ambiguous downloaded files for {record.image_id}: {sorted(map(str, hits))}")
    return next(iter(hits), None)


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
