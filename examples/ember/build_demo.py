"""Map original AI artwork through the actual Stadium UVs and export a demo ZIP."""

import argparse
import importlib.util
import json
from pathlib import Path
import shutil

import numpy as np
from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / 'plugins/trackmania-livery-studio/skills/trackmania-livery-studio'
SPEC = importlib.util.spec_from_file_location('studio', SKILL / 'scripts/studio.py')
studio = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(studio)


def save_json(path: Path, value: object) -> None:
    """Save an editable recipe or record."""
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main() -> None:
    """Build a new project without modifying packaged assets or the current game skin."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--texconv')
    args = parser.parse_args()
    project = args.project.resolve()
    studio.init_project(project, 'Ember_Studio_Demo', None)
    source = project / 'source'
    shutil.copy2(Path(__file__).parent / 'artwork.png', source / 'artwork.png')
    shutil.copy2(Path(__file__).parent / 'prompt.txt', source / 'generation-prompt.txt')
    size = 2048
    fields = studio.uv_fields(project, 'Skin', size)
    tire = studio.uv_fields(project, 'Wheels', size)
    positions = tire['position']
    x, y, z = np.moveaxis(positions, -1, 0)
    center_z = np.where(z > 25, 178.30, -120.166)
    radius = np.hypot(y - 35.253, z - center_z)
    sidewall = (np.abs(tire['normal'][:, :, 0]) > .4) & tire['mask']
    ring = sidewall & (radius > 29.2) & (radius < 31.2)
    tyre_layer = np.zeros((size, size, 4), np.uint8)
    tyre_layer[ring] = (218, 43, 37, 255)
    Image.fromarray(tyre_layer).save(source / 'soft-rings.png')
    mark = Image.new('RGBA', (768, 192))
    draw = ImageDraw.Draw(mark)
    draw.polygon([(70, 60), (260, 60), (325, 96), (260, 132), (70, 132), (130, 96)], fill='#d94b26')
    draw.ellipse((358, 64, 422, 128), fill='#17202b')
    draw.rectangle((468, 76, 680, 116), fill='#17202b')
    mark.save(source / 'wing-mark.png')
    recipe = {
        'source_size': size,
        'materials': {
            'Skin': {
                'layers': [
                    {'name': 'Quiet dark body paint', 'type': 'fill', 'color': '#15171c', 'mask': {'region': 'body'}},
                    {'name': 'Generated Ember pigment, common physical mapping', 'type': 'project',
                     'image': 'artwork.png', 'axes': [0, 2], 'ranges': [[-82, 82], [-161, 209]],
                     'mask': {'region': 'body_static'}, 'lod_opacity': [1, 1, .96, .85, .7, .6]},
                    {'name': 'Dynamic panel quiet backing', 'type': 'fill', 'color': '#181a20', 'mask': {'region': 'dynamic_panel'}},
                    {'name': 'Independent wing warm ivory', 'type': 'fill', 'color': '#eadac1', 'mask': {'region': 'wing'}},
                    {'name': 'Contained exact wing mark', 'type': 'project', 'image': 'wing-mark.png',
                     'axes': [0, 2], 'ranges': [[-32, 32], [-150, -137]], 'flip_u': True,
                     'mask': {'region': 'wing', 'normal': {'y': [.65, 1]}, 'inset': 8}}
                ],
                'surface': [{'roughness': .24, 'metalness': .04, 'mask': {'region': 'body'}},
                            {'roughness': .31, 'metalness': .12, 'mask': {'region': 'rims'}}]
            },
            'Wheels': {'layers': [{'name': 'Physical soft compound rings', 'type': 'atlas',
                                    'image': 'soft-rings.png'}]}
        }
    }
    save_json(source / 'recipe.json', recipe)
    studio.compose(project, source / 'recipe.json')
    output = studio.export_project(project, studio.texconv_path(args.texconv))
    studio.preview(project)
    save_json(source / 'generation.json', {
        'tool': 'native ChatGPT image generation', 'date': '2026-10-23',
        'asset': 'artwork.png', 'references': [], 'brand': 'original unbranded demo',
        'ai_disclosure': 'Artwork and most project code/instructions were created with AI.',
        'game': 'GAME_PENDING'})
    studio.bundle_sources(project)
    print(f'DEMO_OK: {output.name}; original AI artwork projected through real UV; DDS audited; GAME_PENDING')


if __name__ == '__main__':
    main()
