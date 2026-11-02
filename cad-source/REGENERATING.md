# Working with the editable CAD

The ready-made print and STEP downloads are under `dist/models/`. Regeneration
is optional. Use the checked-out `cad-source/cad/` scripts for the current path
handling; source copies embedded in the preserved ZIP downloads are snapshots
from the revision that produced those files.

## Environment

The CAD tooling was written for a Unix-like Python environment and uses `fcntl`
file locking. Linux or WSL is the appropriate starting point. The website itself
does not require these tools: serve `dist/` with any static HTTP server.

The archived dependency baseline names CadQuery 2.7.0, trimesh, NumPy, SciPy,
Pillow, VTK and numba. `manifold3d` is also needed for the adapted dragon sculpt;
`lxml` is needed for the static website checks. For example, in a dedicated
Python environment:

```sh
python3 -m pip install cadquery==2.7.0 trimesh numpy scipy Pillow vtk numba manifold3d lxml
```

This publication verified the existing exports and website checks. It did not
rerun the full CAD build or establish a new dependency lockfile. Keep dependency
and Bambu Studio versions with any new regeneration report.

## Output directories

Run commands below from the repository root. Dimensions are millimetres, Z up.

| Setting | Meaning | Default |
|---|---|---|
| `NESTFORGE_EXPORTS` | Generator, audit and packaging output | `cad-source/exports/` |
| `NESTFORGE_R7` | R7 packaging/installer input override | `NESTFORGE_EXPORTS`, then `cad-source/exports/` |
| `NESTFORGE_BLOCKOUTS` | Traditional/organic silhouette studies | `blockouts/` beside the selected export directory |
| `NESTFORGE_R6` | Historical R6 staging root containing `exports/`, `adapters/` and `coupons/` | `cad-source/r6/` |

For an explicit local output directory:

```sh
export NESTFORGE_EXPORTS="$PWD/cad-source/exports"
python3 cad-source/cad/backyard_traditional.py orchard-hopper
```

Generate one model per process. Do not run competing writers against the same
model directory. The checked-in design brief retains historical planning
context; its old machine-specific paths are not setup requirements.

## Camera model generators

| Module | Model IDs |
|---|---|
| `backyard_traditional.py` | `orchard-hopper`, `meadow-lantern`, `ridge-aframe` |
| `backyard_organic.py` | `fern-wall-pocket`, `pebble-pod`, `drift-platform` |
| `backyard_gravity.py` | `bottle-bough`, `acorn-column` |
| `backyard_structural.py` | `woven-arch`, `willow-screen` |

Pass one model ID as the positional argument. The existing 37-design families
are in `originals.py`, `world.py`, `castles.py`, `sports.py`, `whimsy.py` and
`future.py`; their selectors differ, so read their entry points before running.
`vegas*.py` and the R6 guide preserve the earlier hotel study and are not the
active camera catalog.

Dragon Guard Citadel uses `community_dragon.py` and the credited Artec asset in
`cad/assets/`. The detailed dragon remains a sculpt mesh; the structural STEP
does not contain that sculpt. Preserve `COMMUNITY-ASSETS.md`, `ATTRIBUTION.txt`
and the supplied Artec license with derivatives.

## Auditing and native plate packaging

The saved 3MF files are native, unsliced Bambu Studio projects. For a new native
roundtrip, install Bambu Studio separately and point the helper at the real
executable and its official BBL profiles:

```sh
export BAMBUSTUDIO_BIN=/absolute/path/to/bambu-studio
export BAMBUSTUDIO_PROFILES=/absolute/path/to/resources/profiles/BBL
```

The executable can alternatively be found on `PATH` as `bambu-studio` or
`BambuStudio`. The profiles directory must still be set. `BAMBUSTUDIO_LIB` is an
optional command-scoped shared-library path; without it, the inherited library
path is preserved. No helper sends a print job.

After generating a selected R7 model, the existing stages are:

```sh
python3 cad-source/cad/audit_assembly.py --only orchard-hopper
python3 cad-source/cad/audit_backyard_camera.py --only orchard-hopper
python3 scripts/package-r7.py --only orchard-hopper
```

The R7 packager requires current camera-audit hashes and a successful native
Bambu roundtrip. Do not treat a generated mesh alone as an approved replacement
for a packaged design. The CAD camera audit uses published envelopes and stated
optical assumptions; real camera fit, focus, snap life, feed flow and installed
load still require physical trials.

`scripts/assemble-r7.py` installs all ten packaged camera models and rewrites
the website catalog, downloads and source ZIP. It is a collection-maintenance
operation, expects all ten export directories, and should be run in a staging
checkout. `assemble-r5.py` and `assemble-r6.py` are retained revision installers.

The plate-preview renderer also uses a C compiler (`cc`) and the DejaVu Sans
font path documented in `scripts/render-print-plans.py`. Native CAD regeneration,
slicer execution and browser WebGL rendering are separate from the preserved
artifact checks under `tests/` and `scripts/verify-r7.py`.
