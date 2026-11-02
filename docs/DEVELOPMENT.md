# CAD and website development

[← README](../README.md) · [Design index](COLLECTION.md) · [First print](GETTING_STARTED.md)

The branch keeps the maintained website and CAD source, with large generated artifacts distributed in the complete release. Restore those files before running the site, artifact checks or CAD workflows that use the sculpt asset. Current geometry uses the R5 original designs and R7 backyard camera designs. Earlier R1/R2 bundles and the R6 Vegas generators are preserved as historical work; revision numbers refer to different stages of the project, not a promise that all parts interchange.

## Serve the site

The frontend is static HTML, CSS and JavaScript. From a Git clone, run the fetch helper once to restore the pinned collection payload. It verifies SHA-256 before extraction. If you extracted the [complete release ZIP](https://github.com/thisisformuchfun/nestforge/releases/download/v1.0.0/NestForge-Complete-Collection-v1.0.0.zip), skip that step. From the repository root:

```sh
python scripts/fetch-collection.py
python -m http.server 8000 --bind 127.0.0.1 --directory dist
```

Open **http://127.0.0.1:8000/**. No frontend compilation is required after the artifacts have been restored. WebGL is required for the 3D viewer; the catalog and design-detail fallback remain available without it.

| Source | Role |
|---|---|
| [`dist/catalog.json`](../dist/catalog.json) | Authoritative current list of 47 designs, parts and metadata |
| `dist/models/` (restored from the [complete release](https://github.com/thisisformuchfun/nestforge/releases/tag/v1.0.0)) | Per-design browser meshes, packaged print/CAD downloads, guides and validation records |
| [`dist/editorial-data.json`](../dist/editorial-data.json) | Theme groups, detailed build pages, concept studies and dated source notes |
| [`dist/sourcing-data.json`](../dist/sourcing-data.json) | Dated camera, accessory and filament offers |
| [`dist/print-plan-summary.json`](../dist/print-plan-summary.json) | Plate totals and geometric time ranges |
| [`scripts/build-editorial-pages.py`](../scripts/build-editorial-pages.py) | Generates the theme, concept and six detailed build pages |
| [`tests/`](../tests/) | Website regression and static checks |

Keep concepts outside `catalog.json` until actual CAD and print artifacts exist. Their current diagrams and proposed part counts are design studies.

## Validation

After restoring the complete payload with `python scripts/fetch-collection.py`, run the existing checks from the repository root:

```sh
node --test tests/upgrade.test.mjs
python tests/check-site.py
node scripts/check-plate-extraction.mjs
python scripts/verify-r7.py
```

`tests/check-site.py` requires Python’s **lxml** package. The JavaScript checks use Node.js and the checked-in site modules. These commands inspect stored artifacts and behavior; they do not rebuild the CAD or launch Bambu Studio.

| Check | What it establishes |
|---|---|
| `upgrade.test.mjs` | Regression coverage for catalog helpers, source-loading races, sourcing, accessibility state and ZIP behavior |
| `check-site.py` | Local page/assets/anchors, editorial structure, deterministic generation and preserved baseline hashes |
| `check-plate-extraction.mjs` | Extracts all 102 3MF entries using the website’s actual ZIP reader, including CRC validation |
| `verify-r7.py` | Current catalog counts, compressed STL hashes, archive integrity, plate settings and recorded design checks |

The retained baseline hash check is intentionally strict. A legitimate geometry change will require a documented new baseline, rather than quietly overwriting old evidence. The recorded native Bambu Studio roundtrip was performed during artifact generation; rerunning the artifact verifier does not repeat that native-slicer import/export or establish a physical print result.

For editorial changes, run:

```sh
python scripts/build-editorial-pages.py
```

Then run the checks and review the generated diff. Browser QA should include search and reset, camera opt-in, design switching, a full-pack download, an individual-plate download, keyboard focus and narrow layouts. Inspect the no-WebGL fallback separately. The [October integration notes](../review/INTEGRATION-2026-10-24.md) describe earlier browser checks and their limits.

## Work on the CAD

Start with [`cad-source/cad/SOURCE-GUIDE.html`](../cad-source/cad/SOURCE-GUIDE.html), [`R7-GUIDE.md`](../cad-source/cad/R7-GUIDE.md) and the relevant design’s metadata. Dimensions are in millimetres, with Z up.

The shared generators use **CadQuery/OpenCascade**, NumPy, SciPy, trimesh and Pillow. Particular generation/rendering paths also require VTK, numba and lxml. The archived source guide records **CadQuery 2.7.0**; the collection does not supply a fully pinned, platform-independent environment lockfile. The website can be browsed without installing these CAD dependencies.

| CAD modules | Scope |
|---|---|
| `originals.py`, `world.py`, `castles.py`, `sports.py`, `whimsy.py`, `future.py` | Original 37-design families |
| `backyard_traditional.py`, `backyard_organic.py`, `backyard_gravity.py`, `backyard_structural.py` | Active R7 camera feeder architectures |
| `backyard_camera.py`, `audit_backyard_camera.py` | Shared camera proxies, mounting data and checks |
| `common.py`, `sanitize_stl.py`, `audit_assembly.py`, `finalize_step_exports.py` | Geometry export and digital verification helpers |
| `native_bambu.py`, `read_3mf.py`, `package_collection.py` | Native Bambu project conversion, comparison and packaging |
| `community_dragon.py`, `assets/` | Attributed dragon sculpt and its integration |
| `vegas*.py`, `R6-GUIDE.md` | Historical Vegas camera prototypes and their separate fit-coupon workflow |

For an R7 generation example, use an isolated output location and run from the CAD directory. In a POSIX shell:

```sh
cd cad-source/cad
export NESTFORGE_EXPORTS=/absolute/path/to/nestforge-working-exports
python backyard_traditional.py orchard-hopper
```

On Windows, run these CAD regeneration commands inside Linux/WSL. The retained CAD pipeline uses Unix `fcntl` locking; native Windows CAD regeneration has not been validated.

Set `NESTFORGE_EXPORTS` **before** importing `common.py`. Each R7 family module takes the model ID as its positional argument. Inspect a generator’s own entry point before using commands for another revision; the historical R6 command-line interface differs.

### Native Bambu roundtrip

Native project verification needs an actual Bambu Studio executable and its official profiles. [`native_bambu.py`](../cad-source/cad/native_bambu.py) supports:

| Environment variable | Meaning |
|---|---|
| `BAMBUSTUDIO_BIN` | Path to the real Bambu Studio executable |
| `BAMBUSTUDIO_PROFILES` | Path to the official `resources/profiles/BBL` directory |
| `BAMBUSTUDIO_LIB` | Optional command-scoped shared-library search directories |

Use paths for your own Bambu Studio installation; executables and official profiles are not bundled. The public-repository edition accepts the explicit variables above and can discover the executable on `PATH`. The conversion helper imports and exports unsliced projects and compares geometry, colors and placements. It does not send a job to a printer.

### Packaging a change

Use a working copy when running assembly or packaging scripts: several rewrite catalog files, ZIPs and generated directories. Trace the chosen revision’s pipeline before using older `assemble-r5.py` or `assemble-r6.py` scripts against the current site. Preserve each design’s source, metadata, printable meshes, STEP export, guide, plate projects and checks together.

Keep the full Artec license and attribution in any affected Dragon Guard Citadel export. Structural STEP and the sculpt mesh are different deliverables; do not represent the structural STEP as containing the complete scanned dragon.

## Source status and rights

No new project-wide license is asserted here. Existing third-party terms remain with their assets. The [contribution guide](../CONTRIBUTING.md) asks contributors to retain provenance and clearly distinguish digital inspection, native-slicer verification and physical tests.
