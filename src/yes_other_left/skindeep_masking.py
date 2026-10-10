from __future__ import annotations

import json
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any, Iterable, Literal, Mapping

from PIL import Image, ImageDraw

MaskPreset = Literal["none", "bottom", "right", "both"]
MaskColor = Literal["neutral_gray", "black", "white"]
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}


@dataclass(frozen=True)
class MaskSpec:
    image_id: str
    filename: str = ""
    manifest_master_filename: str = ""
    mask_preset: MaskPreset = "none"
    right_mask_pct: float = 18.0
    bottom_mask_pct: float = 20.0
    mask_color: MaskColor = "neutral_gray"
    artifact_location: str = ""
    annotation_complete: str = ""


def _normalize_image_id(value: Any) -> str:
    return str(value or "").strip().upper()


def _stem(value: Any) -> str:
    return Path(str(value or "").strip()).stem.casefold()


def _number(value: Any, default: float) -> float:
    try:
        return default if value in (None, "") else float(value)
    except (TypeError, ValueError):
        return default


def _preset(value: Any) -> MaskPreset:
    candidate = str(value or "none").strip().lower()
    return candidate if candidate in {"none", "bottom", "right", "both"} else "none"  # type: ignore[return-value]


def _color(value: Any) -> MaskColor:
    candidate = str(value or "neutral_gray").strip().lower()
    return candidate if candidate in {"neutral_gray", "black", "white"} else "neutral_gray"  # type: ignore[return-value]


def load_mask_specs(path: str | Path) -> dict[str, MaskSpec]:
    """Load the completed masking-annotation JSON without touching source images."""
    with Path(path).open("r", encoding="utf-8") as handle:
        rows = json.load(handle)
    if not isinstance(rows, list):
        raise ValueError("Mask annotations must be a JSON array of objects")

    specs: dict[str, MaskSpec] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        image_id = _normalize_image_id(row.get("image_id"))
        if not image_id:
            continue
        if image_id in specs:
            raise ValueError(f"Duplicate mask annotation for {image_id}")
        specs[image_id] = MaskSpec(
            image_id=image_id,
            filename=str(row.get("filename") or ""),
            manifest_master_filename=str(row.get("manifest_master_filename") or ""),
            mask_preset=_preset(row.get("mask_preset")),
            right_mask_pct=_number(row.get("right_mask_pct"), 18.0),
            bottom_mask_pct=_number(row.get("bottom_mask_pct"), 20.0),
            mask_color=_color(row.get("mask_color")),
            artifact_location=str(row.get("artifact_location") or ""),
            annotation_complete=str(row.get("annotation_complete") or ""),
        )
    return specs


def build_filename_index(specs: Mapping[str, MaskSpec]) -> dict[str, str]:
    index: dict[str, str] = {}
    for image_id, spec in specs.items():
        for candidate in (image_id, spec.filename, spec.manifest_master_filename):
            if candidate:
                index[_stem(candidate)] = image_id
    return index


def infer_image_id(
    image_path: str | Path,
    specs: Mapping[str, MaskSpec],
    filename_index: Mapping[str, str] | None = None,
) -> str | None:
    path = Path(image_path)
    index = filename_index or build_filename_index(specs)
    if path.stem.casefold() in index:
        return index[path.stem.casefold()]
    upper_name = path.name.upper()
    return next((image_id for image_id in specs if image_id in upper_name), None)


def apply_mask(image: Image.Image, spec: MaskSpec) -> Image.Image:
    """Return a masked RGB copy; never mutate or save the source image."""
    output = image.convert("RGB")
    if spec.mask_preset == "none":
        return output

    colors = {"neutral_gray": (128, 128, 128), "black": (0, 0, 0), "white": (255, 255, 255)}
    fill = colors[spec.mask_color]
    width, height = output.size
    right_width = round(width * min(max(spec.right_mask_pct, 0), 100) / 100)
    bottom_height = round(height * min(max(spec.bottom_mask_pct, 0), 100) / 100)
    draw = ImageDraw.Draw(output)

    if spec.mask_preset in {"right", "both"} and right_width:
        draw.rectangle((width - right_width, 0, width, height), fill=fill)
    if spec.mask_preset in {"bottom", "both"} and bottom_height:
        draw.rectangle((0, height - bottom_height, width, height), fill=fill)
    return output


def open_masked_image(
    image_path: str | Path,
    specs: Mapping[str, MaskSpec],
    filename_index: Mapping[str, str] | None = None,
) -> tuple[Image.Image, MaskSpec | None]:
    with Image.open(image_path) as source:
        image_id = infer_image_id(image_path, specs, filename_index)
        if image_id is None:
            return source.convert("RGB"), None
        return apply_mask(source, specs[image_id]), specs[image_id]


def image_to_bytes(image: Image.Image, image_format: Literal["PNG", "JPEG"] = "PNG") -> bytes:
    buffer = BytesIO()
    save_options = {"quality": 95, "subsampling": 0} if image_format == "JPEG" else {}
    image.save(buffer, format=image_format, **save_options)
    return buffer.getvalue()


def iter_images(directory: str | Path) -> Iterable[Path]:
    for path in Path(directory).rglob("*"):
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS:
            yield path
