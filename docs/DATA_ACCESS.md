# Obtaining and handling DFTB Skin Deep images

The repository does **not** download, scrape, or redistribute Skin Deep images. Researchers must obtain written authorization from the DFTB Skin Deep rights holder and download the approved files through the route DFTB provides.

## Required process

1. Review the current DFTB privacy, consent, copyright, and image-use terms.
2. Send DFTB the completed request in `PERMISSION_REQUEST_TEMPLATE.md` and attach `data/manifests/skindeep_permission_request_filenames.csv`.
3. Describe the exact research purpose, storage controls, masking procedure, expected publications, collaborators with access, retention period, and whether example images will appear in posters or manuscripts.
4. Obtain written confirmation before downloading or processing any image. Record the permission date, sender, scope, expiration, attribution language, and publication restrictions in your institution's secure records—not in this public repository.
5. If your school or institution requires ethics/IRB review, data-protection review, parental approval, or a data-use agreement, complete that process separately. DFTB authorization does not replace institutional approval.
6. Use only the approved download mechanism. Do not automate scraping unless DFTB explicitly authorizes it.
7. Place the authorized files in `data/raw/skindeep/`. This directory is gitignored.
8. Validate the download locally with `prepare_skindeep.py`. Resolve every missing or duplicate filename before inference.
9. Keep both source and masked derivatives private. The standard pipeline masks only in memory.

DFTB's privacy notice states that identifiable image contributors—or a parent, guardian, or attorney when applicable—must consent through the Skin Deep consent process. That describes DFTB's collection process; downstream researchers should still request separate authorization for the proposed research use and publication context.

Useful current contacts and pages:

- DFTB privacy policy: https://dontforgetthebubbles.com/privacy-policy/
- Skin Deep consent process referenced by DFTB: https://dftbskindeep.com/consent-process/
- General Skin Deep data-protection contact listed by DFTB: hello@dftbskindeep.com

Website terms can change. Reconfirm them at the time of access and preserve the written authorization with the study records.
