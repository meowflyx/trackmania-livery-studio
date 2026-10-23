---
name: trackmania-livery-studio
description: Create or revise real Trackmania 2020 Stadium car skins from a design idea, racing livery reference or existing skin ZIP. Produce editable UV textures, compatible DDS mipmaps and an importable ZIP; diagnose skin-specific seams or compression artifacts. Not for general Formula 1 news or Trackmania driving advice.
---

# Trackmania Livery Studio

Deliver a usable skin, not a picture of a car. Default to Trackmania 2020 Stadium/CarSport and make a new version, preserving the user's original. Respond in the user's language.

## Start from the request

- A concrete one-line request is enough to begin. Infer secondary choices from the reference; do not force a questionnaire or stop at concept approval unless the user requests that gate.
- For a team, year and Grand Prix, research the **specific livery** using team/F1/event primary sources and reference photos. Record URLs and dates in the project. Distinguish a documented race-specific livery from a normal season livery or an inspired adaptation. Do not invent a future/unannounced special edition. If unavailable, say so briefly and use the nearest verified season design, labelled as an interpretation, unless exact replication is essential to the user.
- Preserve actual design choices: palette, finish, sponsor density, tyre compound and wear. Red Bull, glossy paint, red tyre rings and our previous design are examples, not defaults for every request.
- For an existing ZIP, inspect files, dimensions, stored mipmaps and hashes before changing it. Read [troubleshooting.md](references/troubleshooting.md) for pixelation/import complaints. Do not apply a preselected “fix” from a screenshot alone.

## Tool and project setup

Use built-in browsing and image generation where available; no remote service, API key or MCP server is required by this package. The bundled encoder is Windows x64. Instructions and Python helpers are portable, but other hosts need a compatible native `texconv` supplied via `--texconv`. Run the host's available Python with Pillow and NumPy; install dependencies only through its permitted workflow. A skill does not grant tools or filesystem access.

Read [pipeline.md](references/pipeline.md) before the first build. Resolve `STUDIO` to this skill's absolute directory, choose a separate writable `PROJECT`, then run:

```text
python STUDIO/scripts/studio.py doctor
python STUDIO/scripts/studio.py init --project PROJECT --name Skin_Name
python STUDIO/scripts/studio.py uv --project PROJECT --material Skin --size 2048
```

For revisions add `--base ORIGINAL.zip` to `init`. Do not silently replace a different car's geometry with the bundled community mesh. The bundled profile's region IDs, orientation and BC5 adapter apply only to its hashed geometry. Inspect another model first.

## Create the design

Read [art-direction.md](references/art-direction.md) for imagegen prompts and reference handling. Generate **flat, unlit artwork/material assets** rather than asking a generator to invent a UV atlas or showing a generated car as proof. Keep original generations, references, exact logos and separate paint/pattern/sponsor layers. Use exact vectors/high-resolution assets or faithful text for sponsor marks, not hallucinated imagegen typography.

Project artwork onto actual geometry with the helper's recipe, or write a bounded project-specific compositor. Use one shared surface/world-space definition for connected graphic paths. Do not hand-align unrelated UV-island endpoints and assume they join. Add padding around occupied islands without moving the UVs. Keep moving wing graphics in their own region, with margins and no unintended connection to the stationary body. Leave dynamic number/name and instrument surfaces functional.

The helper supports named masks, physical-axis projection, repeatable material patterns, fills, material roughness/metalness changes, editable OpenRaster and per-layer distance opacity. See [recipe.md](references/recipe.md) and the runnable `assets/example-recipe.json`. Adapt its geometry and colours; it is a neutral smoke fixture, not a finished artistic template.

```text
python STUDIO/scripts/studio.py compose --project PROJECT --recipe PROJECT/recipe.json
python STUDIO/scripts/studio.py export --project PROJECT
python STUDIO/scripts/studio.py inspect --zip PROJECT/deliverables/Skin_Name.zip
python STUDIO/scripts/studio.py preview --project PROJECT
```

## Verify before delivery

1. Reopen the actual ZIP and validate CRC, flat paths, required files, exact formats, dimensions and **every stored mip level**. Check BC1 opacity and the BC5 RG channel/orientation adapter. Preserve unedited functional maps byte-for-byte.
2. Inspect model views from front, rear, both sides, top, diagonals and wheel close-ups. Check sponsor cropping, mirrored text, continuity, panel boundaries and wing separation. Read [quality.md](references/quality.md).
3. Use the generated local viewer with **native compressed DDS colour mip chains**, not mip0 decoded to PNG with regenerated browser mipmaps. Inspect placement unlit and approximate materials lit. Inspect chase-camera scale: the car may occupy only 300–400 pixels in a 1920-pixel screenshot. The viewer does not reproduce Trackmania's shaders, nameplate, speedometer or wing animation.
4. Inspect stored small mips and consider explicit per-layer LOD simplification only when the detail warrants it. Do not automatically blur all artwork, upscale the ZIP, remove mipmaps or change game settings. Thin high-contrast multicolour strokes can break within BC1 blocks even when mip0 is sharp.
5. Test any requested deployment or rollback on a duplicate first. Do not overwrite another skin, clear caches, change drivers or publish to a club merely because you are making a ZIP.

Iterate on observed defects. Re-render after changes and inspect images, not merely test logs. Actual in-game import/appearance remains a separate validation state until observed; do not claim it from an external render. The automated scripts validate the known texture-package profile, not a guarantee of all future game versions.

## Deliver

Return clickable paths/links to the **skin ZIP**, editable sources (ORA/layers/recipe/original generations), preview contact sheet and verification report. Keep export logs, original SHA-256 and a tested restoration path. State file checks, preview checks and in-game checks separately, briefly. A concept alone is not completion; if a required tool is missing, retain the project and identify the concrete missing execution step rather than labelling a mockup “importable”.

For host installation and portability see [hosts.md](references/hosts.md). The package's current sources and provenance are in [sources.md](references/sources.md).
