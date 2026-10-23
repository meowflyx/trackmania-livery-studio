# Validation status — public alpha

Version: **1.1.0-alpha.1**. Release preparation date: **2026-10-23**.

This file reports tests, not an implied guarantee that all models, accounts, hosts or future Trackmania builds work identically.

| Check | Meaning |
|---|---|
| Original regression fixture | The preceding private release decoded 79 stored mip levels, checked BC5 RG channels and one vertical flip, isolated a wing emblem, preserved unedited maps and restored a duplicate. |
| Independent cold-start fixture | A second agent, without conversation history, followed the packaged skill and rebuilt all eight skin entries from extracted sources byte-for-byte. |
| Public clean-install regression | **PASS**: extracted public plugin ZIP, fresh venv with Python 3.12.14, Pillow 13.0.0 and NumPy 2.5.4; all 79 mip levels decoded, BC5/flip sentinels, editable-source replay and duplicate rollback. CI repeats these deterministic checks. |
| Image-generation demonstration | **PASS for files/external preview**: Ember uses a newly generated flat artwork file and actual UV/DDS/export pipeline, with 21 captured and inspected views. The privacy-sanitized downloadable source archive independently rebuilt all eight skin entries byte-for-byte using the fresh environment. Prompt, source image, recipe and build helper are published. |
| External viewer | Native compressed colour mip chains, not mip0-only PNGs with regenerated mips. Approximately lit and unlit views; this is not the game's shader. |
| Live Trackmania import and driving | **PENDING for this exact public release/demo**. Earlier user gameplay images are development history, not a new public-release test. |
| Dynamic displays, wing deployment, multiplayer/club upload | **PENDING** in the actual game. Static viewer screenshots do not exercise them. |
| Claude, cloud Linux/macOS, arbitrary custom car profiles | **NOT VALIDATED**. The bundled encoder is Windows x64; the geometry adapter is Stadium-specific. |

## Reproduce deterministic checks

The first hosted Windows CI run exposed automatic LF/CRLF conversion of a pinned JSON asset. The fix is repository-level `* -text` in `.gitattributes`, preserving resource bytes rather than weakening the hash check. A deliberately deep local marketplace-install test also exposed Git for Windows' path limit; a per-process `core.longpaths=true` override is documented, with no global Git change.

That deep installation additionally exposed Windows process creation failing when texconv's executable path reached 276 characters. The shared encoder runner now passes an explicit extended-length executable path on Windows when necessary. The selftest copies the pinned executable into a 270+ character path and actually launches it, so this is a regression-tested fix, not a skipped check.

In a fresh directory with Python/Pillow/NumPy available:

```powershell
python tools/validate_public.py
$s='plugins/trackmania-livery-studio/skills/trackmania-livery-studio/scripts'
python "$s/studio.py" doctor
python "$s/selftest.py" baseline
python "$s/selftest.py" modified --work .work/regression
python "$s/selftest.py" rollback --work .work/regression
python tools/package_release.py
```

The selftest's `modified` stage requires a new work directory; use another name for a repeated run rather than overwriting a previous test. It builds a real import-format ZIP with DDS, not a pretend successful test object. The archive parser checks every stored mip through 1x1. The executable rollback helper restores a disposable copy, not the active project.

## Remaining game check

Use the exact release demo ZIP and record its SHA-256. Keep the current skin selected/preserved, copy the new version into the appropriate local `Skins/Models/CarSport` directory, select it via the game's supported UI and verify import/appearance. Compare at matched car screen size and actual game settings. Inspect the wing in both positions, race number/name, display surfaces, wheel/tyre appearance and small logos. Record whether club registration/network visibility was actually tested. Do not mark this row complete merely because a file was copied or a preview loaded.

## Honest limitations

The skill is an agent workflow, not an autonomous hosted rendering service. Image-generation quality and exact sponsor placement still require visual judgement and iteration. The model contains overlapping/mirrored UV reuse; its hash-bound region adapter and actual views must be consulted. Thin multicolour details may compress poorly in BC1 even at 2048. Do not diagnose every game/editor difference as a DDS bug, and do not claim arbitrary future branded liveries are confirmed references.
