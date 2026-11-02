# NestForge: camera-free-first review patch

## Useful result

A local-only upgrade is ready for review against **v7 source commit `ccf4a08e11664ffb18de410c1db2289b819fad31`**. It does not publish, push, change access, place orders or contact anyone.

- **37 no-camera designs are now the default**, with camera prototypes behind an explicit opt-in. Existing files remain available.
- **Six detailed build pages** improve the strongest existing themes with genuine CAD previews, measured assembly dimensions, actual plate counts, part-specific supports, cleaning/refill notes, real ZIP downloads and clear prototype caveats.
- **Six theme categories** let buyers browse beyond the creator’s personal favorites.
- **Four original, structurally different concept pages**: Toadstool Terrace, Storybook Nook, Comet Diner and Courtside Canopy. Each is explicitly an unbuilt study with **no CAD or print files**. They are not inserted into the 47-design catalog.
- **24 automated tests pass**, plus extraction/checksum verification of **102 native 3MF plates**, **365 local page references**, and byte-for-byte preservation of **761 original model/CAD/download artifacts**.

The public site remains unchanged at https://nestforge-feeders.stevengineer.chatgpt.site (public, latest version 7 when read).

## Pages to review

Serve `dist/` in an authorized local preview environment, then open:

- `/` — camera-free-first discovery, search, plate budget, sorting, camera opt-in.
- `/themes/` — six audience themes, separated concept cards, evidence/limitations and browser-local shortlist.
- `/designs/scandinavian-cabin/`
- `/designs/fairy-tale-turret/`
- `/designs/garden-clog/`
- `/designs/ufo-snackduction/`
- `/designs/lantern-pavilion/`
- `/designs/helmet/`
- `/concepts/` and its four child routes — explicit unbuilt studies, not purchasable products.

## Concrete defects fixed

1. Camera-first merchandising conflicted with the user’s updated budget/time priority. The original 37 designs are foregrounded without deleting the 10 camera prototypes.
2. Selecting two designs during asynchronous model loading could render the older design’s shopping panel last. Sourcing starts with the selection, and existing generation guards now protect the correct panel.
3. Camera/lens totals and dates were hard-coded. Required-lens prices now come from data; missing prices produce an incomplete estimate instead of a misleading lower total.
4. Snapshot purchasability was presented as “Available.” Every offer now has a per-offer date and a checkout-stock caveat. Full-spool purchase totals are clearly distinguished from per-feeder material consumption.
5. No available ASA match could crash the whole sourcing panel. Missing offers are handled explicitly, and non-1kg/reinforced/invalid-price offers are not silently substituted.
6. Selected-card rerendering lost keyboard focus. Details receive focus; closing restores the originating card (or search fallback). Tabs now use roving tabindex and support Home/End plus arrow navigation.
7. Mobile library cards had a 300px minimum track in a narrower content box. The minimum now respects the available width; long names/actions wrap. Controls have larger targets, and the no-WebGL detail panel no longer reserves a huge fixed viewer gap.
8. The individual-plate ZIP reader checked size but not CRC. Same-length corruption is now rejected before a download is created, with the existing complete-pack fallback retained.
9. Ordinary keyboard or pointer interaction unexpectedly started nature audio. Audio now requires a deliberate Sound action, and stored zero volume is preserved.
10. Singular plate labels, malformed URL hashes, empty search states and unverified price/unsafe-URL edge cases are covered by regression tests.

## Demand evidence — a ranking of tests, not sales claims

| Priority | Direction | Evidence and limitation |
|---|---|---|
| First | Playful garden / cottage & woodland | Etsy’s [Fall/Winter 2026 report](https://www.etsy.com/seller-handbook/article/1521255894814), published Oct 14, reports whimsy-item searches up 110% in its comparison. This is recent adjacent-market evidence, not bird-feeder sales or demand for a mushroom product. |
| Second | Storybook / bookish | Etsy’s [Spring/Summer 2025 report](https://www.etsy.com/seller-handbook/article/1362959156542) describes book-related purchasing and literary styling. This is older, adjacent evidence; use it to choose a test, not forecast sales. |
| Exploratory | Retro space / roadside | The same 2025 report includes cosmic styling. The diner interpretation is original and unproven. |
| Control | Game day / any team | No suitable feeder-specific demand signal was verified. Retain the existing football range and compare a generic court-side concept; do not call it popular. |

The official [Uncommon Goods bird-feeder category](https://www.uncommongoods.com/home-garden/garden/birdhouses-feeders) includes decorative feeders such as Tree Wizard ($34 observed); its mushroom item is a **nester**, not a feeder. The official [Perky-Pet catalog](https://www.perkypet.com/store/bird-feeders) includes decorative/hopper/platform categories and a Country House feeder ($39.99 observed). These corroborate category presence only. Finished-product prices cannot be compared directly with a file download or a full-spool shopping estimate. No competitor imagery or designs were copied.

All original concepts avoid protected characters, logos, book-cover art and recognizable franchise props. No licensed collaboration, bestseller badge, customer review, stock, preorder or finished-product price is invented.

## Purchasing-source refresh

`review/source-checks.json` records the exact official variant checks. On Oct 23:

- Polymaker 1kg ASA variant prices and purchasability were reread from `https://shop.polymaker.com/products/asa.js`; direct variant URLs remain in the page data.
- [Wyze Battery Cam Pro](https://www.wyze.com/products/wyze-battery-cam-pro): $89.98 for the displayed white, one-camera, no-extra-accessory option.
- [Required close-up lens](https://www.wyze.com/products/wyze-cam-close-up-lens): $9.98.
- [Birdfy Cam 2K standalone](https://www.birdfy.com/products/birdfy-cam): $89.99 on the retrieved listing; exact AI-plan option should be checked before buying.
- Other manufacturer/retailer offers retain their Oct 20 dates. No checkout stock, delivery, local inventory or shipping quote was verified. Bambu’s current product-page retrieval failed; its older dated offer was not relabeled as fresh.

Camera work is now secondary. All ten metadata targets lie in their camera’s modeled forward half-space and have service instructions. That check does **not** establish lens position, focus, occlusion, retention, weather sealing or real-device fit. No camera CAD was changed.

## Verification and limits

- `review/unit-tests.txt`: 24 tests, 24 passed, including actual `selectDesign` source in a mocked-DOM race harness. This is not a browser rendering test.
- `review/plate-extraction.txt`: all 102 native 3MF plates extracted using the actual upgraded website code, with CRC verification.
- `review/site-checks.json`: 12 new static pages, 365 local references, 28 images with alt text, no duplicate HTML IDs or missing links, deterministic page generation, 761 unchanged artifacts.
- `review/retained-integrity-tests.json`: original R7 verifier passed; 47 designs, 175 parts, 102 plates, 245.26 MiB static bundle. The verifier rechecks stored artifacts and recorded CAD results; no new physical or native-slicer trial was performed.
- All top-level JavaScript passes `node --check`; `git diff --check` is clean.
- Original CAD renders and four original SVG schematics were visually inspected. The schematics are deliberately labeled “not CAD,” not passed off as realistic physical-product photos.
- Public v7 was inspected in the cloud browser: no-WebGL fallback, catalog, Orchard Hopper detail/print plan and shopping panel were accessible. That observation applies to the **old live site**, not the patch.
- **Rendered browser/mobile QA of the patch is pending.** A normal local server was isolated from the cloud browser. The supported local-server escalation failed with `bwrap: Can't create file at /home/agent/.codex/sessions: Read-only file system`. No permission bypass or further attempt to read that restricted path was made. Mobile changes have static responsive checks only.

The user reports one non-camera print looks good, but its model is unknown. That report was not attributed to an arbitrary product or inflated into catalog-wide validation.

## Reproduce

```sh
python scripts/build-editorial-pages.py
node --test tests/upgrade.test.mjs
python tests/check-site.py
node scripts/check-plate-extraction.mjs
python scripts/verify-r7.py
for f in dist/*.js; do node --check "$f"; done
```

The source stays at `/workspace/shared/nestforge-upgrade`. The review archive is an **overlay plus patch**, not a complete deployable site: it relies on the unchanged v7 models, fonts, audio and vendor files.

## Before any publication or CAD expansion

1. Parent review of this local patch; do not push or deploy it automatically.
2. Browser checks on an authorized preview host at 320/390/768/1440px, keyboard-only and no-WebGL: search/reset, camera opt-in, empty result, direct deep links, tabs/focus, rapid selection, all six build pages, shortlist storage failure, export and a real plate download.
3. Ask which existing model the user printed (a photo or filename is enough). Use that feedback to select the first physical improvement.
4. Clarify whether the next business objective is digital files, finished printed feeders, or both; unit economics differ substantially.
5. For buyer demand, compare equal-quality original concept mockups with actual bird-feeding users. Record first choice, price expectations, maintenance objections, and reasons for rejecting a theme. A small pilot is directional, not a statistically representative sales forecast. No outreach, paid ads or analytics were initiated.
6. Only then engineer one selected concept, audit actual geometry/plates and test refill, cleaning, seed flow and installed load before releasing print files.
