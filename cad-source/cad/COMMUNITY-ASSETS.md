# Community sculpt

Dragon Guard Citadel uses **Dragon (Fantasy Dragon)**, a 3D scan published by **Artec Group inc. / Artec 3D**:
https://www.artec3d.com/3d-models/fantasy-dragon

The downloaded STL archive includes the CC BY 3.0 Unported license; that original file is preserved as `assets/ARTEC-LICENSE.txt`. The source page additionally links CC BY 4.0. This package follows the attribution terms of the supplied CC BY 3.0 license: https://creativecommons.org/licenses/by/3.0/

Adaptations: uniformly scaled to 24.5% of scan size; 0.30 mm voxel remeshing, one-voxel outward thickening and smoothing to stabilize thin scan surfaces; reduced triangle count; connected to a removable snap crown. No endorsement by Artec is implied.

`assets/artec-dragon-printable.stl` is the adapted standalone sculpt. Run `community_dragon.py` to integrate it with the parameterized castle. This is **hybrid CAD**: editable structural STEP, plus a sculpt mesh. Full printable shape is supplied as STL and native Bambu 3MF; the STEP intentionally contains only the mechanical structure. Wings and jaw need reviewed support placement. Physical printing, snap fit, hanger load and seed-flow tests remain required.

All other R5 surface details are authored in the accompanying CadQuery scripts. No other downloaded community sculptures are incorporated in this release.
