# Collection provenance

This public-repository edition brings the existing NestForge work together as of November 2, 2026. Maintained source is browsable in the branch; the entire assembled collection is preserved in the [v1.0.0 complete release](https://github.com/thisisformuchfun/nestforge/releases/download/v1.0.0/NestForge-Complete-Collection-v1.0.0.zip).

## Complete archive identity

- Filename: `NestForge-Complete-Collection-v1.0.0.zip`
- Size: **503,982,838 bytes**
- Contents: **1,030 files**, including current models, source, print/CAD packages, all site assets, artwork, saved R1/R2 packages and the October review.
- SHA-256: `e95d1838ec7ddf99900c56ce904a223ac665f8e01ee5dc5261be0aa37c33142b`

`python scripts/fetch-collection.py` restores the release artifacts into a source clone after verifying that checksum. Locations in the table below describe the complete archive and a restored checkout; large binaries and historical packages are not all tracked on the lean branch.

| Material | Source edition | Location |
| --- | --- | --- |
| Current website, current CAD source, print/CAD packs, assets, and review evidence | Published NestForge Site version 8, incorporating R7 geometry and the October 24 editorial integration | `dist/`, `cad-source/`, `scripts/`, `tests/`, `review/` |
| First saved complete collection | NestForge Complete CAD and Prints R1, October 8, 2026; 28 designs | `archive/r1/` |
| Second saved complete collection | NestForge Complete CAD and Prints R2, October 8, 2026; 37 designs | `archive/r2/` |
| Submitted review package | October 23, 2026 overlay, patch, and package metadata | `archive/review-2026-10-23/` |
| Presentation artwork | Earlier NestForge concept images | `docs/artwork/` |
| Website screenshots | Captured from the public NestForge website on November 2, 2026 | `docs/screenshots/` |

The current collection has 47 downloadable designs: 37 without a required purchased camera and 10 backyard camera prototypes. The four new concept studies have no printable CAD. The older Vegas-themed camera source remains in `cad-source/cad/vegas_cameras.py`; it is historical source and is not an additional current downloadable print collection.

## Import decisions

- The current working files were copied from the latest Site source. Hosted-project identity and Git credentials/history are not part of this repository.
- Original R1/R2 complete bundles were unpacked one level so their individually downloadable feeder ZIPs remain intact inside the full release. Their contents are historical snapshots, not the recommended starting point for current prints.
- The current individual print packs, CAD ZIPs, and per-design validation records are retained. These packages are digital prototypes; recorded software checks are not physical test-print results.
- Repository documentation, links, ignore rules, and portable regeneration defaults were added for the GitHub edition. Historical source archives remain unchanged.
- The bundled third-party notices, including the Artec dragon attribution, Three.js, fonts, and nature audio credits, are retained. No new blanket license has been selected for original project content.
- Screenshots show the actual site. Images in `docs/artwork/` are concept artwork; the CAD render images elsewhere are not photographs of completed prints.

## Revision labels

Site version numbers track publication history; CAD revision labels track design revisions. Site version **8** can therefore correctly contain a catalog labeled **R7**. The R1/R2 archives are earlier geometry and should not be mixed with current parts.

## Verification evidence

See `docs/VERIFICATION.md` for checks performed for this repository edition. Historical evidence stays under `review/` and inside the per-design packages. [`docs/full-collection-manifest.sha256`](full-collection-manifest.sha256) preserves the original per-file manifest for the complete collection snapshot. Apply it to that extracted snapshot, not directly to the lean branch, whose README and setup instructions explain release-based delivery. The release archive checksum above verifies the complete download.
