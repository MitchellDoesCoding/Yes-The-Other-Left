# SkinDeep-542 report specification

## Cohort

- 542 unique source images.
- Patient-centered ground truth.
- LEFT and RIGHT are unilateral/determinable cases.
- Bilateral, midline, not-applicable, and unable-to-determine cases are scored as UTD controls.
- Original and horizontal-mirror views are retained as paired observations, not treated as unrelated source images.

## Required model metrics

1. API completion and parse-validity rates.
2. Overall three-class accuracy.
3. Unilateral accuracy, with UTD counted as incorrect.
4. Unilateral coverage: fraction answered LEFT or RIGHT.
5. Accuracy among committed LEFT/RIGHT predictions.
6. Wrong-side rate on unilateral cases.
7. Correct abstention on controls.
8. False lateralization on controls.
9. Original and mirrored results separately.
10. Both-correct pair accuracy.
11. Mirror reversal among pairs with two committed answers.
12. Prompt-level, body-region-level, and image-level results.
13. Confusion counts and row-normalized confusion rates.
14. Failures and missing trials, never silently converted to UTD.

## Uncertainty

For inferential comparisons, resample source images as clusters so original/mirror views, prompts, and repeated trials for the same source image remain together. State the bootstrap seed and number of resamples. Trial-level binomial intervals may be shown only as descriptive intervals and must not substitute for image-clustered uncertainty.

## Data-release boundary

Public reports may contain code, prompts, DLB identifiers, aggregate tables, and filename-only permission manifests if authorized. They must not contain source image bytes, masked image bytes, local file paths, credentials, or example images lacking explicit publication permission.
