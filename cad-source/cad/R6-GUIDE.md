# NestForge Vegas camera hotels - R6

Twelve original hotel-inspired digital prototypes: Bellagio, Venetian, Caesars,
Paris, Excalibur, New York-New York, Luxor, Flamingo, Wynn, legacy Mirage, Strat
and Circus Circus. No hotel affiliation or licensed architectural reproduction.

Each default build has three printed ASA pieces on two native, unsliced X1C
plates: the one-piece twin reservoir/terrace, integral architectural snap roof,
and Wyze Battery Cam Pro cradle. Body color is kept on its own full-bed plate;
the roof and cradle share a second plate. At most four colors per build/plate.

## Camera choices

- Wyze Battery Cam Pro: default bay, published 63.5 x 45.7 x 88.9 mm envelope.
  Buy its official close-up lens. Withdraw the cradle, release the camera, then
  open the bottom battery compartment to swap or USB-C charge the removable pack.
- Birdfy Cam 2K: extended rear cradle puts the complete camera behind the roof,
  with no overhead body/antenna constraint. Published overall height is 230 mm;
  body height is not published. The 90 mm body in the website is illustrative.
  Withdraw the camera for USB-C charging. Supplied solar hardware remains optional.
- Blink Outdoor 4: conditional mechanical cradle. Replace its nonrechargeable
  lithium AA batteries through the rear cover after removal. A Sync Module is
  required. Suitable close-focus optics have not been verified; it is not a
  validated close-up camera recommendation.

One camera, one matching cradle. The two-plate hotel pack includes Wyze only.
Other cradle files are one-plate replacements. Camera hardware in the website
is illustrative, bought separately, and absent from STL/STEP/3MF print geometry.
No mirror is supplied: direct optics leave lens/PIR/IR paths clear. A mirror
cannot eliminate minimum focus distance and would need separate optical testing.

## Prototype sequence

1. Print the small roof-snap coupon first; it preserves production beam and slot
   geometry. Tune ASA shrinkage, extrusion and release force before the full body.
2. Print one camera cradle and test retention against the actual purchased unit.
   Published dimensions do not establish measured housing contours or sensor data.
3. Check focus and PIR triggering at the actual landing position. Numerical close
   focus ranges were not published for the checked Birdfy/Wyze kits. No physical
   fit, optical, fatigue, hanging load, feed flow or weather tests have been done.
4. Slice the full plates with the actual ASA brand profile and support settings.
   The cradle's hook protrudes 2.2 mm below its plate: support is required beneath
   the raised plate, not just the hook. Keep flexure slots and grip arms clear.
5. Load-test over a soft surface; the suspension eye and four roof catches carry
   the assembled feeder. Remove camera electronics before washing or charging.

## Regeneration

Use CadQuery/OpenCascade, NumPy, SciPy, trimesh, Pillow, VTK and numba. The real
Bambu Studio executable and official profiles are required for native project
roundtrip verification; see native_bambu.py environment overrides.

    export NESTFORGE_EXPORTS=/absolute/output/exports
    python vegas.py --only luxor

Run sanitize_stl.run(folder), audit_assembly.audit(design_json), then
package_collection.package_design(design_json). Digital checks require closed
single-body meshes, exact nonoverlapping material regions, STEP readback,
zero significant BREP interference, X1C limits/exclusion/tower clearance and
native Bambu geometry/color/placement roundtrip. Never bypass a failed check.

The source uses common.py, vegas.py, vegas_arch_a.py, vegas_arch_b.py and
vegas_cameras.py. vegas_fit_coupon.py regenerates the small fit check. Architecture
is original code; no downloaded Birdfy CAD geometry is redistributed.

The website stores each native plate inside its complete ZIP and extracts the
unchanged individual 3MF in the browser to avoid duplicated download storage.
Print times are unsliced geometric planning ranges; support time is excluded.
Price snapshots were checked October 20, 2026 UTC; Amazon prices were unverified.
Direct retailer and ASA manufacturer links accompany the current online list.
