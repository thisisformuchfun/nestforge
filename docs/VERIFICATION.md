# Repository verification — November 2, 2026

These results apply to the **complete 1,030-file collection** assembled and checked before release packaging. Its [release ZIP](https://github.com/thisisformuchfun/nestforge/releases/download/v1.0.0/NestForge-Complete-Collection-v1.0.0.zip) preserves the models, native projects, artwork and historical files. The browsable branch contains maintained source and selected documentation images; restore the full payload with `python scripts/fetch-collection.py` before repeating artifact or website checks.

## Results

| Check | Result |
| --- | --- |
| Current catalog and packaged-artifact verifier | 47 designs, 175 printed parts, 102 native X1C plates |
| Camera subset | 10 designs, 20 printed parts, 18 plates |
| Website ZIP-reader extraction | All 102 native 3MF entries extracted successfully |
| Static site and editorial checks | 365 local references, 12 editorial pages, 28 images with alt text |
| Preserved baseline artifacts | All 761 recorded artifacts retained unchanged |
| Catalog integrity | Exact recorded SHA-256 match |
| Python syntax | 38 maintained source files passed |
| JavaScript regression command | Passed; the runner reports one passing test file containing 24 declared cases |
| Editorial regeneration | Deterministic; no generated-page byte changes |
| Bounded credential-pattern check | No common credential-pattern hits in 482 text files and 2,408 text entries inside project ZIPs |
| Historical R2 archives | 37 feeder ZIPs and 84 contained 3MF ZIP containers passed CRC checks; referenced parts/regions/plates were present |

Environment for these command checks: Python 3.12.14, Node.js 24.22.1, and lxml for HTML inspection.

## Commands

From a source clone, restore the complete payload first. If you extracted the complete release ZIP, skip the fetch command:

```sh
python scripts/fetch-collection.py
node --test tests/upgrade.test.mjs
python tests/check-site.py
node scripts/check-plate-extraction.mjs
python scripts/verify-r7.py
```

The static checker retains the original 761-artifact manifest and adds an explicit catalog baseline in `review/publication-integrity.json`. It no longer depends on a private hosted-project identity. Its extra Git check runs only when this directory is the actual repository root, so downloaded source ZIPs remain usable.

## Browser inspection

The public website was inspected while producing the README screenshots. Theme navigation, existing-design detail pages, the family filter, and the camera-prototype opt-in were exercised. The browser displayed the existing no-WebGL fallback; the interactive 3D rendering path was not exercised in this session. Screenshots are in `docs/screenshots/`.

## Scope

These checks inspect the delivered files and stored digital evidence. No new CAD regeneration, native slicer execution, physical printing, load test, snap-cycle test, camera fit/focus check, seed-flow test, or weather trial was performed. Earlier recorded native Bambu Studio and geometry checks remain as historical evidence; rechecking their files does not repeat those experiments.

The prototype status, physical-test flags, camera fit limitations, and split mesh/STEP attribution are retained in the catalog and documentation. Site version 8 contains R7 design revisions; these are different versioning systems.

## Source-checkout restoration check

An isolated copy of the maintained source tree was restored using `scripts/fetch-collection.py --archive` with the exact release ZIP. The checksum matched; 915 payload files were restored and 4 identical files retained. The restored checkout passed the static, regression, 102-plate extraction, and 47-design artifact checks. This checked the local-archive path; the public GitHub download is verified separately at publication.
