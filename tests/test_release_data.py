import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ANNOTATIONS = ROOT / "data" / "annotations"


def test_public_ground_truth_is_complete_and_sanitized():
    path = ANNOTATIONS / "SkinDeep_ground_truth_complete.csv"
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fields = set(reader.fieldnames or [])

    assert len(rows) == 542
    assert len({row["image_id"] for row in rows}) == 542
    assert len({row["original_skindeep_filename"] for row in rows}) == 542
    assert {row["laterality"] for row in rows} <= {"left", "right", "bilateral", "not_applicable"}
    assert not fields & {
        "annotator_id", "annotation_source_file", "batch_id", "notes",
        "started_at", "updated_at", "original_relative_path",
    }


def test_public_mask_annotations_are_complete_and_sanitized():
    path = ANNOTATIONS / "skindeep_mask_annotations_export.json"
    rows = json.loads(path.read_text(encoding="utf-8"))
    assert len(rows) == 542
    assert len({row["image_id"] for row in rows}) == 542
    assert all(row["annotation_complete"] for row in rows)
    assert all(row["mask_preset"] in {"none", "bottom", "right", "both"} for row in rows)
    assert not set(rows[0]) & {
        "notes", "saved_at", "artifact_location", "original_final_patient_laterality",
        "original_final_body_region", "final_patient_laterality", "final_body_region",
    }
