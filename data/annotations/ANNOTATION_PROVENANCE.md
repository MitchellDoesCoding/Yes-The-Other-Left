# Annotation provenance

## Ground truth

- File: `SkinDeep_ground_truth_complete.csv`
- Rows: 542
- Public-release SHA-256: `6d94eb0d7c3eba5ef589c67b851d19bcaad516e954e970cd93bdfae2f4e2a84e`
- Public fields: image ID, original filename, master filename, anatomical and laterality labels, confidence, UTD reason, multiplicity, target clarity, and review flag.
- Annotator identity, internal source/batch fields, timestamps, paths, and free-text notes are excluded from the public release.
- Required manual corrections verified:
  - `DLB_00011934 = left`
  - `DLB_00012224 = right`

## Inference-time masking annotations

- File: `skindeep_mask_annotations_export.json`
- Supplied by the study team on 2026-10-07.
- Rows and unique image IDs: 542.
- Public-release SHA-256: `bf20a841440c315b9d7ee8be736c182f58d3a9d3e221fbec00a680f939ad6158`
- Every ground-truth image ID has exactly one annotation.
- All 542 annotations are marked complete.
- Mask presets: 328 bottom, 213 right, and 1 none.
- Mask color: neutral gray for all 542 images.
- No duplicate IDs, extra IDs, missing IDs, invalid percentages, invalid presets, or invalid colors were found.

The public mask export contains only the fields required to reproduce standardized inference-time masking. Scoring uses the separately versioned ground-truth CSV.
