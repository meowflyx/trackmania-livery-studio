# Ember — original unbranded demonstration

The flat `artwork.png` was generated with the native image-generation tool. It is not a picture of a car and not a completed UV atlas. `prompt.txt` records the generation prompt. No existing team, sponsor logo or supplied photo was used as a reference.

Run from the repository root with the documented Python dependencies:

```text
python examples/ember/build_demo.py --project .work/ember
```

The helper uses the shipped real geometry and the standard CLI pipeline. It writes a genuine DDS skin ZIP, editable ORA/layers and a portable recipe into the chosen project. It adds a separate exact wing mark, paints soft-compound tyre rings in physical coordinates and retains functional mechanical/normal maps. The script is a reproducible demonstration recipe, not the whole agent skill or a special rule for every livery.

To inspect the result, run the generated preview in a loopback server:

```text
python -m http.server 8882 --bind 127.0.0.1 --directory .work/ember
```

Then open `http://127.0.0.1:8882/preview/viewer.html` in an available browser. Optional `scripts/capture.cjs` automates the required views when Playwright is already installed. Stop the server when finished. These are external renders, not game captures. The release demo remains GAME_PENDING until actual import/driving evidence is recorded.
