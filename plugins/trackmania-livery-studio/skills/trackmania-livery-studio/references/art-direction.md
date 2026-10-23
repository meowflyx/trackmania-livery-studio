# Art direction and references

Translate the reference into a design language: dominant/secondary/accent colours, distribution, signature geometry, logo hierarchy, finish, wheel details and empty space. Adapt to Stadium proportions rather than placing an F1 side photograph across the atlas. More sponsors do not necessarily mean more quality. Use coherent families of detail and readable spacing; remove decoration that competes with the focal mark.

For exact team/year/race requests, keep `reference_sources.json` with URL, publisher, date, what it supports, and whether the claimed special livery was actually confirmed. Team launch/race galleries and official F1 images outrank reposts. Distinguish reference collection from downloadable logo licensing/provenance. Retain user-supplied assets unchanged in `source/originals`.

## Image generation

Prefer the host's native image generator for original paint motifs, textile/geometric patterns, rubber wear and carbon variations. Follow its current editing workflow: inspect existing local images, supply references and preserve masks/dimensions during edits. Do not name an assumed model/version in the skill.

Reusable prompt pattern:

```text
Create a flat, unlit material/artwork asset for an actual racing-car UV workflow.
Reference design language: [verified team/season/event and attached references].
Palette: [colours]. Motif scale and contrast: [specific]. Finish will be supplied
by a separate roughness map, not painted highlights. View: orthographic flat
surface, no car, no perspective, no shadows, no bevel, no vignette, no baked light.
Keep [edges] repeatable if tiling is requested. No logos, lettering, sponsor text,
numberplate or fake panel geometry. Output [dimensions/aspect/background].
```

For worn tyres: mild circumferential scuff variation, rubber pickup restrained and low contrast; no hard directional lighting, muddy damage, artificial tread on an explicitly slick tyre or fake geometry. Mask the generated rubber into tread, preserve sidewall marks/compound rings separately, vary roughness with the material rather than replacing functional normals blindly.

Generator output is an asset, not UV truth. Map it through the actual profile. Use a shared world-space mapping for artwork spanning stationary body panels; use separate projections/masks for wing, sides and mirrored surfaces. Keep exact sponsor logos as separate high-resolution layers. Inspect both left and right for flipped writing. Request a generator correction when its artwork is poor, not to compensate for a broken UV transform.
