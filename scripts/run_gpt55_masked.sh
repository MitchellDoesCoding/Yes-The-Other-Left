#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "$0")/.." && pwd)"
python_bin="${PYTHON_BIN:-python3}"
export PYTHONPATH="$repo_dir/src${PYTHONPATH:+:$PYTHONPATH}"

if [[ -z "${OPENAI_API_KEY:-}" ]]; then
  echo "OPENAI_API_KEY is not set; refusing to start the paid run." >&2
  exit 2
fi

exec "$python_bin" "$repo_dir/scripts/run_inference.py" \
  --ground-truth "$repo_dir/data/annotations/SkinDeep_ground_truth_complete.csv" \
  --resolved-manifest "$repo_dir/data/private/resolved_images.csv" \
  --masks "$repo_dir/data/annotations/skindeep_mask_annotations_export.json" \
  --output "$repo_dir/runs/gpt-5.5_masked/trials.jsonl" \
  --base-url "https://api.openai.com/v1" \
  --model "gpt-5.5" \
  --api-key-env "OPENAI_API_KEY" \
  --prompt-style all \
  --repeats 5 \
  --reasoning-effort none \
  --max-tokens 512 \
  --timeout 180
