# Quality gates

## Files

Reopen archive; inspect every stored mip. Verify expected legacy FourCC and RG packing, no accidental transparent BC1 blocks, complete dimensions, CRC, flat paths and source hashes. Check the exporter did not resize all maps to one size. Skin ZIP and source ZIP are distinct. A PNG renamed .dds is invalid. Preserve existing specialized maps and test orientation with a labelled asymmetric sentinel.

## Geometry and artwork

Inspect unlit views front/rear/left/right/top and diagonals, then approximate-lit views and wheels. Check line tangent continuity, no unrelated island bleed, no split sponsors, no mirrored typography, enough contrast in gameplay lighting. A moving wing must have its own artwork boundary. The bundled viewer is static: use actual game evidence to judge wing deployment. Race number/name area and dashboard surfaces are not blank livery panels.

Compare at equal screen-space car size. A 1920 screenshot with a 350-pixel car does not show a 1920-pixel car texture. Thin white edging mixed with red/dark blue in BC1's 4x4 blocks can acquire coloured staircase artifacts; more texture resolution alone is not a diagnosis. Inspect exact DDS mip1..5, not only the 4K authoring PNG. Keep the full compressed chain in the browser (`generateMipmaps=false`); decoded PNG plus generated GPU mips is a different product.

Serve only the project directory on loopback using the host's permitted local-server workflow, then open `preview/viewer.html`. If Node and Playwright/Chromium already exist, optional `node STUDIO/scripts/capture.cjs LOOPBACK_VIEWER_URL OUTPUT_DIRECTORY` captures 12 unlit angles and nine lit inspection views. `STUDIO_PLAYWRIGHT` may point to the host's Playwright module. This is an optional automation adapter, not a reason to install an entire browser stack without need. Inspect the captured images using image-view tools and make a contact sheet; a `CAPTURE_OK` log proves loading/capture, not artistic judgment.

## Evidence tiers

For an already installed Edge or Chrome, set `STUDIO_BROWSER_CHANNEL=msedge` or `chrome` before running capture. This avoids requiring Playwright's separate Chromium download. No browser install is performed by the helper.

- FILES_VERIFIED: actual archive parser/decoders passed; list changed map names and original SHA.
- PREVIEW_INSPECTED: actual rendered images visually inspected; record angles, car pixel size, native colour mip use, approximate lighting, unresolved visual findings.
- GAME_PENDING / GAME_OBSERVED: only change the latter after actual import and matching game evidence. A successful local file copy is not registration, gameplay, club upload or network visibility.

For delivery, generate a contact sheet, sources ZIP and JSON/text report. Judge the result as a race-camera skin, not a studio poster. If a viewed defect remains, fix and inspect again before saying the artistic work is finished. State remaining game verification concisely; never fabricate a live-game test to close the workflow.
