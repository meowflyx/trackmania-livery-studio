# Third-party notices and asset provenance

The repository is mixed-license. The root MIT license covers original project code and instructions, **not a relicensing of every bundled file**. Keep this notice and adjacent notices when redistributing plugin or standalone-skill archives.

## Stadium community mesh and derived resources — CC BY 4.0

This work is based on **“trackmania 2020 carsport”** by **amogusstrikesback2**, licensed under **Creative Commons Attribution 4.0 International**:

- Author: https://sketchfab.com/amogusstrikesback2
- Original model: https://sketchfab.com/3d-models/trackmania-2020-carsport-c8b80bfc1ed1427eb37f3eba8d1ecfbf
- License: https://creativecommons.org/licenses/by/4.0/
- Acquisition source: https://github.com/LovelyPotato-ai/TM-LiveSync/tree/104d539b9e3364c1dafcfc3db2a7a41c12019726/assets/car_model

The acquisition source distributes the original model's 756-byte license notice; it is retained as `assets/stadium/model/LICENSE.txt`. The original mesh binary was compared with that exact GitHub revision: Git blob `952370022c1034a04632e4f9f0c163bd35a860a1`, 12,827,508 bytes. Its SHA-256 is recorded in the profile/asset manifest. The Sketchfab page returned HTTP 403 during the release audit, so the live listing was not independently re-read; the distributed license and the acquisition repository's attribution are the recorded basis for inclusion.

Changes: preview materials replaced by neutral definitions; geometry, UVs and node transforms retained. The compact component cache is derived from that mesh. Prepared neutral colour/material maps were created during the preceding local skin work. Details_B/Details_R are derivatives of the community model's original mechanical textures, with project-authored trim/material changes and AI-generated carbon detail. They are **not described as proprietary game textures extracted by this public release**. They and other mixed/derived Stadium texture resources are distributed here under the same CC BY 4.0 terms, with modifications identified. Source PNGs and the protected DDS maps remain available; no Red Bull/Ferrari logos or user reference screenshots are bundled.

The attribution is also copied to generated preview/source outputs. Include it with redistributed renders and modified model/texture derivatives. The model is community-provided, not an official Nadeo template, and the license notice is not a claim of endorsement or a grant of unrelated trademarks.

## Microsoft DirectXTex / texconv — MIT

- Upstream: https://github.com/microsoft/DirectXTex
- Binary release: https://github.com/microsoft/DirectXTex/releases/tag/may2026
- Asset: https://github.com/microsoft/DirectXTex/releases/download/may2026/texconv.exe
- Included Windows x64 executable SHA-256: `dcfdec10244e02cf5037fba089c55fb7e1326b1c8181742d77d15fa5cb5eef06`.

The included hash matches the official GitHub release asset's published SHA-256 digest. Copyright Microsoft Corporation; original MIT license retained adjacent to the executable. No silent executable download or installer is used at runtime.

## Three.js r180 — MIT

- Upstream version: https://github.com/mrdoob/three.js/tree/r180
- Copyright 2010–2025 Three.js authors.
- MIT license retained in the bundled vendor directory.

Only the modules needed by the viewer are included, including DDSLoader, GLTFLoader, OrbitControls and their dependencies. Individual file hashes are pinned in the asset manifest. The external viewer is an approximation, not Trackmania's renderer.

## Original example artwork and project assets

The Ember flat graphic was generated with the native ChatGPT image-generation tool on 2026-10-23 from the included prompt, without a supplied third-party reference. The project icon and exact wing mark were composed programmatically. They are offered with the project under MIT to the extent the publisher holds applicable rights; no representation of exclusivity or universal copyright eligibility is made for AI-generated material. Community-derived geometry/textures visible beneath the artwork retain their attribution above.

No new rights in racing-team logos, car liveries or user-provided references are granted by installing this skill. Future requested branded skins require their own asset provenance. This repository's demo is deliberately unbranded.
