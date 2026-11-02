# Historical collection archives

The [complete v1.0.0 download](https://github.com/thisisformuchfun/nestforge/releases/download/v1.0.0/NestForge-Complete-Collection-v1.0.0.zip) preserves all saved historical collection files alongside the current designs.

| Folder inside the complete download | Contents |
| --- | --- |
| `archive/r1/` | First saved 28-design collection, source, individual print packs, and guide |
| `archive/r2/` | Saved 37-design collection, 155 parts, 84 print plates, source, and verification records |
| `archive/review-2026-10-23/` | Original review overlay, patch, and package metadata |

These are historical snapshots. Use the current `dist/models/` collection for current parts; revisions are not interchangeable.

From a cloned source repository, run `python scripts/fetch-collection.py` to restore these folders and the current print assets. An already-downloaded complete ZIP can be reused with `python scripts/fetch-collection.py --archive /path/to/NestForge-Complete-Collection-v1.0.0.zip`.

The large exports live in the release asset. The repository keeps the maintained source and documentation convenient to browse.
