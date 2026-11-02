# Your first NestForge print

[← README](../README.md) · [All 47 designs](COLLECTION.md) · [Development](DEVELOPMENT.md)

The current collection has 37 camera-free feeders and ten camera prototypes. Every downloadable design is a digital prototype; choose one and review its files before printing the whole assembly.

## Get the complete collection

**[Download the complete release ZIP](https://github.com/thisisformuchfun/nestforge/releases/download/v1.0.0/NestForge-Complete-Collection-v1.0.0.zip)** for all models, print/CAD packs, artwork, website assets and archived revisions. If you cloned the source repository instead, run `python scripts/fetch-collection.py` from its root before using the local site or artifact checks. The helper verifies the pinned archive checksum.

## 1. Pick a design and get the right files

Use the [complete design index](COLLECTION.md) to compare part and plate counts. The [live website](https://nestforge-feeders.stevengineer.chatgpt.site/) adds previews, family filters, search and a plate-budget filter.

| File or folder | Purpose |
|---|---|
| `<design>-X1C.zip` | Complete current print pack, with individual STL parts, arranged native 3MF projects and print metadata |
| `<design>-STEP.zip` | Separate CAD download containing structural solids/assembly; contents differ by design |
| `PRINT-GUIDE.html` | That design’s assembly, print and material notes |
| `design.json` | Part definitions, colors, assembly directions and revision-specific notes |
| `plate-layout.json` / `print-plan.json` | Plate placement, assignments, previews and planning estimates |
| `checks.json` / `assembly-checks.json` | Recorded digital verification results |
| [`cad-source/cad/`](../cad-source/cad/) | Shared editable Python generators and export helpers |

The current website stores 3MF plates inside each full print ZIP and extracts an individual plate on request. Downloading the complete ZIP is also a useful fallback. There is **no ready-to-print G-code** in these packages.

In a GitHub file view, use **Download raw file** for a ZIP. Extract the ZIP locally; GitHub’s source viewer does not run the HTML print guide. Open the extracted guide in a browser, or use the live site’s design information.

## 2. Inspect the Bambu Studio project

The saved plate target is **Bambu Lab X1 Carbon, 0.4 mm nozzle, 256 × 256 mm plate**. Open the native 3MF and check it against your real printer configuration. A different printer or nozzle requires your own arrangement and slicing review; a matching nominal bed size alone is not a compatibility check.

- Use the actual filament profile you intend to print, then review the sliced geometry and supports.
- Verify every flexible snap and release window is free of unwanted support and bridging material.
- Review the part-specific support directions. Some models need localized support; a collection-wide “support free” claim would be wrong.
- Check the purge tower and the printer’s excluded bed area after changing colors or profiles.
- Keep the part names and plate assignments with the files so assembly remains traceable.

Each plate uses at most **four AMS slots**. Three current designs have six colors across the whole build: Monster Mimic Chest, Royal Gatehouse and Stone Fortress. Their plate loads stay within four slots. The ten active R7 camera designs use no more than four colors per complete feeder. Archived revisions can have different palettes.

R7 camera plates use **Generic ASA** in the saved project. Select the actual ASA product/profile and follow your printer and filament manufacturer’s instructions. The older designs have their own saved material assumptions; do not silently replace those settings with a collection-wide prescription.

## 3. Test fit, then build

Read the model’s snap-release and refill instructions before inserting parts. Inspect the sliced preview first and make a small representative fit trial where practical. The historical R6 fit coupon belongs to the R6 camera system; it is not a universal coupon for every design.

Check the actual assembly for latch engagement, removal access, drainage and smooth exposed surfaces. Use the mounting path described for that model. Some feeders hang from an integral eye; others attach to a wall or post. Decorative details are not additional mounting points, and a cord suspends an already assembled feeder rather than replacing its snap joints.

Evaluate a loaded prototype over a suitable low-risk surface before installation. Use the documented seed type and try a small portion to observe bridging or leakage. Make sure the feeding surfaces can be reached for cleaning. No catalog-wide physical test record establishes these behaviors yet.

## 4. If you chose a camera prototype

The [R7 guide](../cad-source/cad/R7-GUIDE.md) explains the intended devices and the modeling limits. Use the particular camera named in your design’s `camera_mount` data. These bays are not universal adapters.

- Purchased cameras are illustrated in previews but excluded from printed-part geometry and counts.
- Published exterior dimensions are fit proxies. Test retention, release access, sensor clearance and focus with the actual device.
- The Wyze Battery Cam Pro designs call for its official close-up lens. The accessory’s physical envelope and practical focus still need checking on the real assembly.
- Birdfy’s illustrated body is a display placeholder within its published overall envelope. It is not a measured housing model.
- Remove electronics before washing or servicing the printed feeder.
- Bottle Bough needs a measured compatible bottle and support bead. It does not provide a universal soda-bottle thread.

## 5. Modify or report your result

Use STEP for solid-model edits and the Python source for parametric changes. Dragon Guard Citadel is a hybrid: its structural STEP omits the scanned dragon surface, which is supplied as a printable mesh and in the 3MF. Preserve [Artec’s attribution and modification notes](../cad-source/cad/COMMUNITY-ASSETS.md).

For a useful build report, record the exact design and revision, printer/nozzle, filament, slicer/profile, changes to supports or scale, photos, and measured results. Separate a successful import or slice from a physical fit test. See [CONTRIBUTING.md](../CONTRIBUTING.md).

## Run the local catalog

From a Git clone, restore the payload and then start the local site. If you extracted the complete release ZIP, skip the first command:

```sh
python scripts/fetch-collection.py
python -m http.server 8000 --bind 127.0.0.1 --directory dist
```

Open **http://127.0.0.1:8000/**. On Windows, `py` may be the available Python launcher. The catalog works without a build step; the animated 3D view needs WebGL. HTML files opened directly with `file://` may be unable to load the catalog and model data.
