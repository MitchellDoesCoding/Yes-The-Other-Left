# Public benchmark annotations

The repository contains the validated public-release study files:

- `SkinDeep_ground_truth_complete.csv`
- `skindeep_mask_annotations_export.json`

See `ANNOTATION_PROVENANCE.md` for checksums, coverage, public field selection, and validation results. Do not replace either file without rerunning the ID, schema, and checksum audit.

The expected masking fields are:

`image_id`, `filename`, `manifest_master_filename`, `mask_preset`, `right_mask_pct`, `bottom_mask_pct`, `mask_color`, and `annotation_complete`.

Allowed `mask_preset` values are `none`, `bottom`, `right`, and `both`. The standard neutral-gray mask is RGB `(128, 128, 128)`. The historical defaults are 20% of image height for a bottom mask and 18% of image width for a right mask, but each completed annotation controls its own values.
