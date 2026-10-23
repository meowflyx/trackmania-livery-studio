# Composition recipe

Paths to artwork are relative to the recipe file. Work inside the project. `assets/example-recipe.json` is an executable neutral example; no proprietary team art is bundled.

```json
{
  "source_size": 2048,
  "materials": {
    "Skin": {
      "layers": [
        {"name": "base paint", "type": "fill", "color": "#173f4f", "mask": {"region": "body_static"}},
        {"name": "independent wing", "type": "fill", "color": "#111820", "mask": {"region": "wing"}},
        {"name": "shared generated artwork", "type": "project", "image": "source/artwork.png", "axes": [0, 2], "ranges": [[-80, 80], [-160, 200]], "mask": {"region": "body_static"}, "opacity": 0.8, "lod_opacity": [1, 0.8, 0.5, 0.25, 0]}
      ],
      "surface": [{"roughness": 0.22, "metalness": 0.0, "mask": {"region": "body"}}]
    }
  }
}
```

Arrays `layers` are bottom-to-top; base PNG comes from original ZIP. The helper writes each layer PNG and a native OpenRaster stack, the merged master and a material R map. Source files remain editable. Re-run composition from the **preserved init sources**, not its previous merged output, to avoid duplicate decals. Put manual edits into distinct input assets/layers or update the recipe; `compose` deliberately rebuilds its generated masters.

Composition also saves the original JSON and a portable `source/recipe.json`, with every artwork input copied into `source/inputs/` and references rewritten relative to that canonical recipe. Recompose an extracted source bundle with `--recipe PROJECT/source/recipe.json`; it needs no original absolute artwork paths. Root project recipes may remain as working copies, but the canonical portable one is included in the source ZIP.

Mask keys are intersections:
- `region`: one of profile's named Skin regions. Refused for other materials.
- `islands`: explicit UV component IDs for the selected material.
- `position`: object x/y/z to `[min,max]` physical ranges.
- `normal`: x/y/z intervals; use to restrict a planar projection to appropriate-facing surfaces. Normals are normalized in raster cache.
- `inset`: nonnegative pixels eroded from the selected UV mask, useful for wing sponsor margins. Inspect physical margins too.

Layer types:
- `fill`: `color` in hex, optional opacity.
- `project`: RGBA image, `axes` two distinct POSITION axes 0/1/2, two nonzero `ranges`; optional `flip_u`, `flip_v`, `repeat`. Non-repeating pixels outside rectangle are transparent. Transparent samples are bilinear in premultiplied colour to avoid dark fringes. Use named region/inset for a sponsor rather than a broad full-body projection. Avoid parallel surfaces receiving duplicated ink by setting normal/position masks.
- `atlas`: RGBA asset already aligned to this exact UV atlas. This is for verified authoring/edits, not generator-guessed UVs.

`lod_opacity` is optional, one scale per exported mip, last value persists. Leave it out by default. It is for gradual reduction of genuinely unresolvable microtexture, not hiding a defective high-resolution master. Export recomposites these known layers before linear-light downsampling. If absent, every mip derives from the same artwork.

`surface` allows region-limited roughness/metalness [0,1]. It preserves the original data outside its mask. No Skin_N/emission map is fabricated. Padding grows colour into empty UV pixels only, never neighbouring occupied islands.

The helper is intentionally not an automatic artistic layout solver. The agent researches, generates assets, chooses physical placement and inspects every view; scripts handle the fragile repeatable mechanics. For radial sidewall compound bands or a continuous curved stripe, derive one physical scalar field from the emitted position/normal cache in a project-specific compositor, save a separate RGBA layer, and pass it as an audited atlas layer. Do not replace all tyre/rim geometry with a flat circle.
