# Working pipeline

`studio.py --help` lists commands. All project paths are explicit. The skill directory is discovered from the script, not a user account path. Dependencies: Python 3.10+, Pillow >=10, NumPy >=1.24; Windows x64 for bundled texconv. There are no runtime downloads. Use `doctor` to inspect versions, executable hash and assets.

## Geometry and UV

The licensed preview mesh is community work by amogusstrikesback2, CC BY 4.0, not an official Nadeo UV template. Its binary, topology, UVs and node transforms are preserved. Only imported preview materials were replaced with neutral definitions. Attribution travels with previews and sources. `assets/stadium/profile.json` binds region IDs to geometry hashes. Never reuse those IDs on a different mesh.

Material index 3 = Skin, 0 = Wheels, 2 = Details. POSITION values are centimetres, x sideways, y up, z forward. Model nodes convert to metres. `uv` rasterizes existing triangles at texel centres, emits position/normal/component fields, wireframe, island map and physical bounds. Skin has compact pre-audited component assignments; other material connectivity is derived. Raster overlap is reported, not silently declared harmless; mirrored reuse requires visual inspection. Uncovered regions remain untouched.

Default authored/export colour resolution is 2048 square for the supplied neutral profile. This is a tested choice, not a universal maximum or a proof of sharpness. `compose` can use a larger source with `source_size`, but export resolution changes must be deliberate, recorded and checked against the live game's requirements. Keep per-map dimensions independent; Wheels_N is smaller in this profile.

## Export rules of this profile

- Flat ZIP: Skin_B/R, Wheels_B/R/N, Details_B/R and Icon.tga. Extra specialized maps in a revision are retained, not guessed or removed.
- Base colour: BC1/DXT1, legacy D3D9 DDS, opaque, complete mip chain. Colour resized in linear light and compressed with uniform RGB weights. Roughness/metalness and normals are linear data.
- R maps: R = roughness, G = metalness. Not glTF's G/B layout. For preview only, build `[255, roughness, metalness]` from decoded DDS.
- BC5: in this tested exporter/game path, texconv's **ATI2 xy payload is relabelled BC5U without payload swapping**. The historic car pipeline interprets ATI2 as yx. The local channel-sentinel test verifies the adapter. Do not generalize this header adapter to arbitrary DDS writers.
- Author PNG orientation follows GLTF UVs. Export flips vertically **once**. The native compressed preview corrects via texture transform; it does not regenerate mips. Decoded preview PNGs also need orientation correction.
- Preserve Details/instrument/emission and specialized alpha conventions. Never blanket-fill all maps or bake lighting/AO into base colour. Optional CoatR is BC4; read actual source documentation before introducing a new functional texture.

`init --base` backs up the original ZIP and decodes only editable colour/R maps into source PNGs. It accepts only the supplied material profile and rejects unexpected formats rather than “repairing” by guesswork. Build a separate profile to support a genuinely different car. `export` begins from backup entries and replaces only maps listed by the composition manifest plus Icon.tga if explicitly supplied. Other map payloads stay byte-identical.

`inspect` reads each legacy header, computes per-level block sizes, verifies the complete chain ends at 1x1, rejects truncation/trailing bytes, decodes every stored level, validates opaque BC1 alpha, checks allowed map conventions and flat ZIP paths. This does not contact game servers or prove club-registration success.
