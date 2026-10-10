#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "$0")/.." && pwd)"
python_bin="${PYTHON_BIN:-python3}"
export PYTHONPATH="$repo_dir/src${PYTHONPATH:+:$PYTHONPATH}"

exec "$python_bin" "$repo_dir/scripts/run_inference.py" \
  --ground-truth "$repo_dir/data/annotations/SkinDeep_ground_truth_complete.csv" \
  --resolved-manifest "$repo_dir/data/private/resolved_images.csv" \
  --masks "$repo_dir/data/annotations/skindeep_mask_annotations_export.json" \
  --output "$repo_dir/runs/google-gemma-4-31b_masked/trials.jsonl" \
  --base-url "http://127.0.0.1:1234/v1" \
  --model "google/gemma-4-31b" \
  --prompt-style all \
  --repeats 5 \
  --max-tokens 6000 \
  --timeout 300
