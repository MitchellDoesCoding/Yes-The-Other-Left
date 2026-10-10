#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from yes_other_left.dataset import load_ground_truth


def opposite(label: str) -> str:
    return {"left": "right", "right": "left"}.get(label, label)


def ratio(n: int, d: int) -> float | None:
    return round(n / d, 6) if d else None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ground-truth", required=True, type=Path)
    parser.add_argument("--run", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    gt = {record.image_id: record.laterality for record in load_ground_truth(args.ground_truth)}
    args.output_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    pairs = defaultdict(dict)
    with args.run.open(encoding="utf-8") as handle:
        for source_row, line in enumerate(handle, 1):
            row = json.loads(line)
            base_gt = gt.get(row["image_id"])
            oriented_gt = opposite(base_gt) if row["orientation"] == "mirror" else base_gt
            answer = row.get("normalized_answer")
            scored = {
                **row,
                "ground_truth": oriented_gt,
                "correct": answer == oriented_gt,
                "committed": answer in {"left", "right"},
                "wrong_side": oriented_gt in {"left", "right"} and answer in {"left", "right"} and answer != oriented_gt,
                "source_row": source_row,
            }
            rows.append(scored)
            pairs[(row["image_id"], row["model"], row["prompt_style"], row["repeat"])][row["orientation"]] = scored

    fieldnames = sorted({key for row in rows for key in row if key != "usage"})
    with (args.output_dir / "scored_trials.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader(); writer.writerows(rows)

    by_model = defaultdict(list)
    for row in rows:
        by_model[row["model"]].append(row)
    summaries = []
    for model, group in by_model.items():
        valid = [r for r in group if r["status"] == "ok" and r["normalized_answer"] in {"left", "right", "utd"}]
        unilateral = [r for r in valid if r["ground_truth"] in {"left", "right"}]
        controls = [r for r in valid if r["ground_truth"] == "utd"]
        committed = [r for r in unilateral if r["committed"]]
        pair_group = [
            p for p in pairs.values()
            if p.get("original", {}).get("model") == model
            and {"original", "mirror"} <= p.keys()
        ]
        unilateral_pairs = [p for p in pair_group if p["original"]["ground_truth"] in {"left", "right"}]
        committed_pairs = [
            p for p in unilateral_pairs
            if p["original"]["committed"] and p["mirror"]["committed"]
        ]
        summaries.append({
            "model": model,
            "valid_trials": len(valid),
            "overall_accuracy": ratio(sum(r["correct"] for r in valid), len(valid)),
            "unilateral_accuracy": ratio(sum(r["correct"] for r in unilateral), len(unilateral)),
            "unilateral_coverage": ratio(len(committed), len(unilateral)),
            "unilateral_abstention": ratio(sum(r["normalized_answer"] == "utd" for r in unilateral), len(unilateral)),
            "committed_accuracy": ratio(sum(r["correct"] for r in committed), len(committed)),
            "wrong_side_rate": ratio(sum(r["wrong_side"] for r in unilateral), len(unilateral)),
            "control_abstention": ratio(sum(r["normalized_answer"] == "utd" for r in controls), len(controls)),
            "false_lateralization_controls": ratio(sum(r["committed"] for r in controls), len(controls)),
            "both_correct_pair_rate": ratio(
                sum(p["original"]["correct"] and p["mirror"]["correct"] for p in unilateral_pairs),
                len(unilateral_pairs),
            ),
            "correct_reversal_committed_pairs": ratio(
                sum(p["original"]["normalized_answer"] != p["mirror"]["normalized_answer"] for p in committed_pairs),
                len(committed_pairs),
            ),
            "error_count": sum(r["status"] != "ok" for r in group),
        })
    with (args.output_dir / "summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summaries[0]))
        writer.writeheader(); writer.writerows(summaries)
    print(json.dumps(summaries, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
