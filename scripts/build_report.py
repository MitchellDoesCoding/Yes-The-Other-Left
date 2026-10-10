#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path


def pct(value: str) -> str:
    return "—" if value in ("", "None") else f"{float(value) * 100:.1f}%"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    with args.summary.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    lines = [
        "# SkinDeep-542 laterality evaluation report", "",
        "> Generated from locally authorized DFTB Skin Deep images. No source or masked image is included in this report.", "",
        "## Model-level results", "",
        "| Model | Overall | Unilateral accuracy | Coverage | Committed accuracy | Wrong-side rate | Control abstention | Both-correct mirror pairs | Correct reversal |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append("| " + " | ".join([
            row["model"], pct(row["overall_accuracy"]), pct(row["unilateral_accuracy"]), pct(row["unilateral_coverage"]),
            pct(row["committed_accuracy"]), pct(row["wrong_side_rate"]), pct(row["control_abstention"]),
            pct(row["both_correct_pair_rate"]), pct(row["correct_reversal_committed_pairs"]),
        ]) + " |")
    lines += ["", "## Interpretation guardrails", "", "- Treat UTD on a left/right-determinable image as incorrect for unilateral accuracy.", "- Report accuracy among committed LEFT/RIGHT answers together with coverage.", "- Pair accuracy requires both the original and mirror predictions to match their orientation-specific ground truths.", "- Do not redistribute source images or locally generated masked derivatives."]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
