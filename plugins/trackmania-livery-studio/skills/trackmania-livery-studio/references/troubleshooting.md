# Skin-specific troubleshooting

Start with the original ZIP and full-resolution game/editor screenshots. Record their camera distance, car screen width, lighting and which installed file/hash was selected. Small attachments alone do not identify a stored mip or prove the game recompressed the file.

1. Audit package headers, dimensions, all stored mips, colour opacity and colour/data formats. A normal 2048 source does not establish the ZIP's resolution or compression quality.
2. Decode exact mip0..5 into a sheet; compare thin outlines, microtexture and small logos. Compare the native compressed viewer with source PNG at matching car screen size. If defects already exist in stored low mips, fix their artwork/compression. Recompressing a screenshot is not a useful test.
3. Confirm viewer transforms, original UVs and material channel order. Double flips and ATI2/BC5U interpretations can make a renderer disagree with the actual game. Do not tune art to compensate for a wrong preview.
4. If still unresolved, make a separate diagnostic skin with distinct solid colours/labels for stored mips, then ask for one controlled game comparison. Preserve normal skin. This isolates mip choice without blanket cache deletion or driver changes.
5. If file mipmaps are correct but runtime still differs, inspect active game texture quality/filtering/render scale only with the user's agreement. Do not blame settings merely because the package parser passed. Check whether the exact new version was selected and cached under a reused name.

Registration code C-AA-00-03 is an observed symptom, not a proven DDS diagnosis. Distinguish archive structure, account/club permissions, upload/name/cache and service conditions; consult current official support when needed. Do not invent an undocumented required ZIP field.

Wheels that look static need a controlled motion test to distinguish stationary mapping from repeated-spoke aliasing. Do not change their design without evidence; respect the user's choice to defer it.
