#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import csv
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

from PIL import Image, ImageOps

from yes_other_left.dataset import load_ground_truth
from yes_other_left.skindeep_masking import apply_mask, image_to_bytes, load_mask_specs

PROMPTS = {
    "landmark_justified": (
        "You are an expert clinician specializing in human anatomy. "
        "Determine the laterality of the human part shown in the photo. "
        "If laterality cannot be determined reliably from the image, answer unable_to_determine. "
        "First line: answer with exactly one word, either left, right, or unable_to_determine. "
        "Second line: give one brief landmark-based justification."
    ),
    "clinician_direct": (
        "You are an expert clinician specializing in human anatomy. "
        "Determine the laterality of the human part shown in the photo. "
        "Answer with exactly one word: left, right, or unable_to_determine."
    ),
    "minimal_direct": "Determine laterality. Reply with exactly one word: left, right, or unable_to_determine.",
}


class FatalAPIError(RuntimeError):
    pass


def normalize_answer(text: str) -> str:
    cleaned = text.strip().lower().replace("-", "_").replace(" ", "_")
    for token in reversed(cleaned.replace(".", "").splitlines()):
        token = token.strip(" *_:`[]{}()")
        if token in {"left", "right"}:
            return token
        if token in {"utd", "unable_to_determine", "cannot_determine", "indeterminate"}:
            return "utd"
    return "unparsed"


def call_api(base_url: str, api_key: str, model: str, prompt: str, png: bytes, temperature: float | None, max_tokens: int, timeout: int, reasoning_effort: str) -> tuple[str, dict]:
    encoded = base64.b64encode(png).decode("ascii")
    is_openai = "api.openai.com" in base_url
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{encoded}"}},
        ]}],
    }
    if is_openai:
        payload["max_completion_tokens"] = max_tokens
        payload["reasoning_effort"] = reasoning_effort
    else:
        payload["max_tokens"] = max_tokens
    if temperature is not None:
        payload["temperature"] = temperature
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:2000]
        lowered = detail.lower()
        if any(token in lowered for token in ("insufficient_quota", "credit_balance_exhausted", "no credits remaining", "invalid_api_key")):
            raise FatalAPIError(f"Fatal OpenAI API response {exc.code}: {detail}") from exc
        raise RuntimeError(f"API response {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise FatalAPIError(f"Inference server unavailable: {exc}") from exc
    text = str(body["choices"][0]["message"].get("content") or "")
    if not text.strip():
        finish_reason = body.get("choices", [{}])[0].get("finish_reason")
        raise RuntimeError(f"Empty model output (finish_reason={finish_reason!r})")
    return text, body


def clean_and_index_existing_output(path: Path) -> tuple[set[tuple], int]:
    """Keep only scoreable successes so empty/error trials are retried on resume."""
    if not path.exists():
        return set(), 0
    valid_by_key: dict[tuple, dict] = {}
    total = 0
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            total += 1
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            key = (row.get("image_id"), row.get("orientation"), row.get("repeat"), row.get("prompt_style"))
            if (
                row.get("status") == "ok"
                and str(row.get("raw_response") or "").strip()
                and row.get("normalized_answer") in {"left", "right", "utd"}
            ):
                valid_by_key[key] = row
    if len(valid_by_key) != total:
        temporary = path.with_suffix(path.suffix + ".cleaning")
        with temporary.open("w", encoding="utf-8") as handle:
            for row in valid_by_key.values():
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        temporary.replace(path)
    return set(valid_by_key), total - len(valid_by_key)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run masked SkinDeep-542 inference through an OpenAI-compatible endpoint.")
    parser.add_argument("--ground-truth", required=True, type=Path)
    parser.add_argument("--resolved-manifest", required=True, type=Path)
    parser.add_argument("--masks", required=True, type=Path)
    parser.add_argument("--image-ids-file", type=Path, help="Optional text file containing one image_id per line.")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--base-url", default="http://127.0.0.1:1234/v1")
    parser.add_argument("--model", required=True)
    parser.add_argument("--api-key-env", default="VLM_API_KEY")
    parser.add_argument("--prompt-style", choices=["all", *sorted(PROMPTS)], default="all")
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--temperature", type=float, default=None)
    parser.add_argument("--max-tokens", type=int, default=512)
    parser.add_argument("--reasoning-effort", choices=["none", "low", "medium", "high", "xhigh"], default="none")
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--no-mirror", action="store_true")
    args = parser.parse_args()

    ground_truth = {record.image_id: record for record in load_ground_truth(args.ground_truth)}
    with args.resolved_manifest.open(newline="", encoding="utf-8") as handle:
        local_paths = {row["image_id"]: Path(row["local_path"]) for row in csv.DictReader(handle) if row.get("status") == "matched"}
    if args.image_ids_file:
        requested_ids = {
            line.strip() for line in args.image_ids_file.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        }
        unknown_ids = sorted(requested_ids - set(local_paths))
        if unknown_ids:
            raise ValueError(f"Requested image IDs are absent from the resolved manifest: {unknown_ids[:10]}")
        local_paths = {image_id: path for image_id, path in local_paths.items() if image_id in requested_ids}
    masks = load_mask_specs(args.masks)
    missing_masks = sorted(set(local_paths) - set(masks))
    if missing_masks:
        raise ValueError(f"Resolved images lack mask annotations: {missing_masks[:10]}")
    api_key = os.getenv(args.api_key_env, "").strip()
    if "api.openai.com" in args.base_url and not api_key:
        raise RuntimeError(f"{args.api_key_env} is not set; refusing to start a paid OpenAI run")
    if not api_key:
        api_key = "lm-studio"
    args.output.parent.mkdir(parents=True, exist_ok=True)

    completed, removed_invalid = clean_and_index_existing_output(args.output)
    if removed_invalid:
        print(f"Removed {removed_invalid} invalid/empty prior records; they will be retried.", flush=True)

    prompt_styles = list(PROMPTS) if args.prompt_style == "all" else [args.prompt_style]
    with args.output.open("a", encoding="utf-8") as output:
        for image_id, path in local_paths.items():
            spec = masks[image_id]
            with Image.open(path) as source_image:
                prepared = apply_mask(source_image, spec)
            for prompt_style in prompt_styles:
                for orientation in (["original"] if args.no_mirror else ["original", "mirror"]):
                    image = prepared if orientation == "original" else ImageOps.mirror(prepared)
                    for repeat in range(1, args.repeats + 1):
                        key = (image_id, orientation, repeat, prompt_style)
                        if key in completed:
                            continue
                        started = time.time()
                        row = {
                        "image_id": image_id,
                        "source_filename": ground_truth[image_id].original_filename,
                        "model": args.model,
                        "prompt_style": prompt_style,
                        "orientation": orientation,
                        "repeat": repeat,
                        "mask_preset": spec.mask_preset,
                        "raw_response": "",
                        "normalized_answer": "error",
                        "status": "error",
                        "error": "",
                    }
                        try:
                            text, body = call_api(args.base_url, api_key, args.model, PROMPTS[prompt_style], image_to_bytes(image), args.temperature, args.max_tokens, args.timeout, args.reasoning_effort)
                            row.update(raw_response=text, normalized_answer=normalize_answer(text), status="ok", usage=body.get("usage"))
                        except FatalAPIError:
                            raise
                        except Exception as exc:
                            row["error"] = f"{type(exc).__name__}: {exc}"
                        row["elapsed_seconds"] = round(time.time() - started, 3)
                        output.write(json.dumps(row, ensure_ascii=False) + "\n")
                        output.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
