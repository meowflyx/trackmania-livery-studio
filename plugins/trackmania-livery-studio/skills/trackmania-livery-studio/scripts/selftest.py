"""Exercise actual DDS/UV/composition behavior in a user-selected fresh directory."""

import argparse
import io
import json
from pathlib import Path
import shutil
import struct
import zipfile

import numpy as np
from PIL import Image, ImageDraw

import studio


def reject(action, message: str) -> None:
    """Require a malformed-input operation to fail with an explicit error."""
    try:
        action()
    except ValueError:
        return
    raise AssertionError(message)


def check(condition: bool, message: str) -> None:
    """Keep checks active under optimized Python execution."""
    if not condition:
        raise AssertionError(message)


def baseline() -> None:
    """Check the neutral input and reject corrupted variants of its stored mip chain."""
    source = studio.ASSETS / 'stadium/neutral.zip'
    value = studio.inspect_zip(source)
    with zipfile.ZipFile(source) as archive:
        original = archive.read('Skin_B.dds')
    for raw in [original[:-1], original + b'extra']:
        reject(lambda: studio.dds_levels(raw), 'Corrupt mip size was accepted')
    bad = bytearray(original)
    struct.pack_into('<I', bad, 28, 1)
    reject(lambda: studio.dds_levels(bad), 'Missing mips were accepted')
    bad[84:88] = b'DX10'
    reject(lambda: studio.dds_levels(bad), 'DX10 header accepted by legacy adapter')
    print(f'BASELINE_OK: neutral CRC; {value["mips_decoded"]} mips decode; truncated/trailing/missing/DX10 rejected')


def modified(work: Path, encoder: Path) -> None:
    """Build from real geometry; test clipping, projection, channels and untouched maps."""
    check(not work.exists(), 'Selftest directory must be fresh')
    studio.init_project(work, 'Studio_Neutral_Test', None)
    fields = studio.uv_fields(work, 'Skin', 512)
    wing = studio.mask_for(fields, {'region': 'wing'}, 'Skin')
    dynamic = studio.mask_for(fields, {'region': 'dynamic_panel'}, 'Skin')
    check(wing.any() and dynamic.any() and not (wing & dynamic).any(), 'Invalid region assignment')
    check(studio.mask_for(fields, {'region': 'wing', 'inset': 2}, 'Skin').sum() < wing.sum(), 'Inset ineffective')
    # Asymmetric artwork exposes orientation flips and duplicated projections.
    art = Image.new('RGBA', (128, 128), '#af4054')
    draw = ImageDraw.Draw(art)
    draw.rectangle((0, 0, 63, 63), fill='#20bd96')
    draw.rectangle((64, 64, 127, 127), fill='#f4df71')
    art.save(work / 'source/asymmetric.png')
    recipe = studio.read_json(studio.ASSETS / 'example-recipe.json')
    recipe['materials']['Skin']['layers'].append({
        'name': 'isolated asymmetric wing stamp', 'type': 'project',
        'image': 'source/asymmetric.png', 'axes': [0, 2],
        'ranges': [[-35, 35], [-151, -136]], 'flip_u': True,
        'mask': {'region': 'wing', 'inset': 2}, 'lod_opacity': [1, 1, .8, .5]})
    studio.write_json(work / 'recipe.json', recipe)
    manifest = studio.compose(work, work / 'recipe.json')
    check(manifest['materials']['Skin']['changed_maps'] == ['Skin_B.dds', 'Skin_R.dds'], 'Wrong changed roles')
    last = manifest['materials']['Skin']['layers'][-1]
    with Image.open(work / last['file']) as layer:
        ink = np.asarray(layer.getchannel('A')) > 0
    check(ink.any() and not ink[~wing].any() and not ink[dynamic].any(), 'Wing stamp escaped mask')
    with Image.open(work / 'source/Skin_R.png') as surface:
        data = np.array(surface)
    check(np.all(data[:, :, 0][wing] == round(.26 * 255)), 'Wrong roughness channel')
    check(np.all(data[:, :, 1][wing] == round(.05 * 255)), 'Wrong metallic channel')
    original_hash = studio.sha(work / 'source/original.zip')
    output = studio.export_project(work, encoder)
    with zipfile.ZipFile(work / 'source/original.zip') as old, zipfile.ZipFile(output) as new:
        changed = [name for name in old.namelist() if old.read(name) != new.read(name)]
    check(set(changed) == {'Skin_B.dds', 'Skin_R.dds'}, 'Untouched functional map was modified')
    check(studio.sha(work / 'source/original.zip') == original_hash, 'Original changed')
    check(studio.sha(output) != original_hash, 'Output not changed')
    with zipfile.ZipFile(work / 'source/Skin_BaseColor.ora') as archive:
        check(archive.testzip() is None, 'ORA CRC mismatch')
        with Image.open(io.BytesIO(archive.read('mergedimage.png'))) as merged:
            first = np.array(merged)
    studio.compose(work, work / 'recipe.json')
    with zipfile.ZipFile(work / 'source/Skin_BaseColor.ora') as archive:
        with Image.open(io.BytesIO(archive.read('mergedimage.png'))) as merged:
            check(np.array_equal(first, np.array(merged)), 'Composition is not idempotent')
    sentinel = Image.new('RGB', (64, 64), (43, 207, 0))
    sentinel_path = work / 'audit/channels.dds'
    log = []
    studio.encode(sentinel, sentinel_path, 'BC5U', encoder, work / 'cache/sentinel', log)
    raw = sentinel_path.read_bytes()
    pixel = studio.decode_level(raw, studio.dds_levels(raw)[0]).getpixel((10, 10))
    check(abs(pixel[0] - 43) <= 2 and abs(pixel[1] - 207) <= 2, f'BC5 channels swapped: {pixel}')
    corners = Image.new('RGB', (64, 64), '#0a1428')
    ImageDraw.Draw(corners).rectangle((0, 0, 31, 31), fill='#f0c020')
    corner_path = work / 'audit/orientation.dds'
    studio.encode(corners, corner_path, 'DXT1', encoder, work / 'cache/sentinel', log)
    raw = corner_path.read_bytes()
    decoded = studio.decode_level(raw, studio.dds_levels(raw)[0])
    check(decoded.getpixel((10, 54))[0] > 220 and decoded.getpixel((10, 10))[0] < 25,
          'Vertical flip not applied exactly once')
    studio.preview(work)
    sources = studio.bundle_sources(work)
    restored = work.parent / f'{work.name}-source-rebuild'
    check(not restored.exists(), 'Source rebuild directory must be fresh')
    restored.mkdir()
    with zipfile.ZipFile(sources) as archive:
        check(all((restored / name).resolve().is_relative_to(restored.resolve())
                  for name in archive.namelist()), 'Unsafe source member')
        archive.extractall(restored)
    (restored / 'cache').mkdir()
    studio.compose(restored, restored / 'source/recipe.json')
    with zipfile.ZipFile(restored / 'source/Skin_BaseColor.ora') as archive:
        with Image.open(io.BytesIO(archive.read('mergedimage.png'))) as merged:
            check(np.array_equal(first, np.array(merged)), 'Portable source rebuild differs')
    report = studio.read_json(work / 'audit/package.json')
    check(report['game'] == 'GAME_PENDING', 'Invented game validation')
    studio.write_json(work / 'audit/selftest.json', {'status': 'MODIFIED_OK',
                      'checks': ['real geometry', 'wing containment', 'dynamic panel preserved',
                                 'roughness/metalness packing', 'BC5 xy sentinel', 'orientation',
                                 'idempotent composition', 'unchanged maps exact', 'source CRC',
                                 'portable canonical recipe rebuild'],
                      'game': 'GAME_PENDING'})
    print('MODIFIED_OK: real UV; wing isolated; RG and flip sentinels; exact untouched maps; idempotent ORA; portable source rebuild; GAME_PENDING')


def rollback(work: Path) -> None:
    """Restore only a duplicate and confirm the changed deliverable remains changed."""
    info = studio.project_info(work)
    output = work / f'deliverables/{info["name"]}.zip'
    trial = work / 'audit/rollback-copy.zip'
    shutil.copy2(output, trial)
    check(studio.sha(trial) != info['original_sha256'], 'Rollback fixture is not modified')
    shutil.copy2(work / 'source/original.zip', trial)
    check(studio.sha(trial) == info['original_sha256'], 'Rollback hash mismatch')
    studio.inspect_zip(trial)
    check(studio.sha(output) != info['original_sha256'], 'Modified deliverable was reverted')
    print('ROLLBACK_OK: duplicate restored byte-exact to neutral; CRC/mips pass; modified ZIP retained')


def main() -> None:
    """Run one named evidence stage in an isolated fresh project."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['baseline', 'modified', 'rollback'])
    parser.add_argument('--work', type=Path)
    parser.add_argument('--texconv')
    args = parser.parse_args()
    if args.stage == 'baseline':
        baseline()
    elif args.stage == 'modified':
        check(args.work is not None, '--work is required')
        modified(args.work.resolve(), studio.texconv_path(args.texconv))
    else:
        check(args.work is not None, '--work is required')
        rollback(args.work.resolve())


if __name__ == '__main__':
    main()
