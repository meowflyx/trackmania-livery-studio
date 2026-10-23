"""Build audited Trackmania Stadium texture packages without inventing UVs.

The CLI separates creative composition, deterministic DDS export and validation.
It never installs a skin, publishes an upload or modifies game configuration.
"""

import argparse
import hashlib
import io
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile

import numpy as np
from PIL import Image, ImageColor, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'assets'
PROFILE_PATH = ASSETS / 'stadium/profile.json'
BLOCKS = {b'DXT1': 8, b'DXT5': 16, b'ATI1': 8, b'BC4U': 8,
          b'ATI2': 16, b'BC5U': 16}
EXTRA_FORMATS = {'Skin_CoatR.dds': 'BC4U', 'Details_I.dds': 'DXT5',
                 'Details_N.dds': 'BC5U', 'Glass_D.dds': 'DXT1',
                 'Glass_I.dds': 'BC5U'}


def sha(path: Path) -> str:
    """Return the SHA-256 of the reopened file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict:
    """Read UTF-8 metadata, including Windows UTF-8 BOM if present."""
    return json.loads(path.read_text(encoding='utf-8-sig'))


def write_json(path: Path, value: object) -> None:
    """Save human-readable, reproducible metadata."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def require(condition: bool, message: str) -> None:
    """Reject a failed invariant even when Python optimization is enabled."""
    if not condition:
        raise ValueError(message)


def profile() -> dict:
    """Load only the profile coupled to the shipped geometry hashes."""
    value = read_json(PROFILE_PATH)
    model = PROFILE_PATH.parent / 'model'
    require(sha(model / 'scene.bin') == value['model_bin_sha256'], 'Geometry hash mismatch')
    require(sha(model / 'scene.gltf') == value['gltf_sha256'], 'GLTF profile hash mismatch')
    require(sha(PROFILE_PATH.parent / 'geometry/Skin.npz') == value['skin_geometry_cache_sha256'],
            'Component geometry cache hash mismatch')
    return value


def dds_levels(raw: bytes) -> list[dict]:
    """Bounds-check every stored legacy block-compressed level through 1x1.

    DX10, cubemap, volume and array textures are intentionally rejected rather
    than interpreted as the supplied ordinary car-texture profile.
    """
    require(len(raw) >= 128 and raw[:4] == b'DDS ', 'Missing DDS magic/header')
    require(struct.unpack_from('<I', raw, 4)[0] == 124, 'Invalid DDS header size')
    require(struct.unpack_from('<I', raw, 76)[0] == 32, 'Invalid pixel format size')
    require(struct.unpack_from('<I', raw, 80)[0] & 4 != 0, 'Missing DDS FourCC flag')
    fourcc = bytes(raw[84:88])
    require(fourcc in BLOCKS, f'Unsupported legacy FourCC: {fourcc!r}')
    height, width = struct.unpack_from('<II', raw, 12)
    depth = struct.unpack_from('<I', raw, 24)[0]
    require(width > 0 and height > 0 and depth in (0, 1), 'Invalid DDS dimensions/depth')
    require(width <= 16384 and height <= 16384, 'DDS dimensions exceed audit bound')
    require(width & (width - 1) == 0 and height & (height - 1) == 0,
            'DDS dimensions must be powers of two in this profile')
    require(struct.unpack_from('<I', raw, 112)[0] == 0, 'Cubemap/volume not supported')
    count = struct.unpack_from('<I', raw, 28)[0]
    require(count == max(width, height).bit_length(), 'Missing or excessive mip levels')
    offset = 128
    result = []
    for index in range(count):
        w, h = max(1, width >> index), max(1, height >> index)
        length = max(1, (w + 3) // 4) * max(1, (h + 3) // 4) * BLOCKS[fourcc]
        require(offset + length <= len(raw), f'Truncated DDS mip {index}')
        result.append({'mip': index, 'width': w, 'height': h,
                       'offset': offset, 'bytes': length})
        offset += length
    require(offset == len(raw), 'Unexpected bytes after final DDS mip')
    return result


def decode_level(raw: bytes, level: dict) -> Image.Image:
    """Decode one actual stored payload, never a regenerated image-library mip."""
    header = bytearray(raw[:128])
    flags = struct.unpack_from('<I', header, 8)[0] & ~0x20000
    struct.pack_into('<I', header, 8, flags)
    struct.pack_into('<II', header, 12, level['height'], level['width'])
    struct.pack_into('<I', header, 20, level['bytes'])
    struct.pack_into('<I', header, 28, 1)
    struct.pack_into('<I', header, 108, 0x1000)
    offset = level['offset']
    with Image.open(io.BytesIO(bytes(header) + raw[offset:offset + level['bytes']])) as image:
        return image.convert('RGBA')


def inspect_zip(path: Path, output: Path | None = None) -> dict:
    """Validate archive paths, file roles and every independently decoded mip."""
    spec = profile()
    rows = {}
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        require(len(names) == len(set(names)), 'Duplicate ZIP member')
        require(all('/' not in n and '\\' not in n and n not in ('', '.', '..')
                    and ':' not in n for n in names), 'Car ZIP must contain flat filenames')
        require(set(spec['required']) <= set(names), 'Missing required car texture or Icon.tga')
        require(sum(i.file_size for i in archive.infolist()) < 512 * 1024 * 1024,
                'ZIP exceeds audit decompression bound')
        require(archive.testzip() is None, 'ZIP CRC mismatch')
        for name in names:
            data = archive.read(name)
            if name == 'Icon.tga':
                with Image.open(io.BytesIO(data)) as icon:
                    require(icon.format == 'TGA' and icon.size == (256, 256), 'Icon must be 256x256 TGA')
                continue
            require(name.endswith('.dds'), f'Unexpected skin member: {name}')
            expected = spec['formats'].get(Path(name).stem, EXTRA_FORMATS.get(name))
            require(expected is not None, f'Unprofiled texture role: {name}; audit before adding support')
            require(data[84:88].decode('ascii') == expected, f'Wrong FourCC for {name}')
            levels = dds_levels(data)
            for level in levels:
                image = decode_level(data, level)
                require(image.size == (level['width'], level['height']), 'Decoded dimensions differ')
                if data[84:88] == b'DXT1':
                    require(image.getchannel('A').getextrema() == (255, 255),
                            f'Unexpected BC1 transparency: {name} mip {level["mip"]}')
            rows[name] = {'fourcc': expected, 'levels': levels,
                          'sha256': hashlib.sha256(data).hexdigest()}
    report = {'status': 'FILES_VERIFIED', 'game': 'GAME_PENDING',
              'zip_sha256': sha(path), 'textures': rows,
              'mips_decoded': sum(len(row['levels']) for row in rows.values())}
    if output:
        write_json(output, report)
    return report


def texconv_path(override: str | None) -> Path:
    """Resolve an explicit encoder, otherwise the bundled Windows binary."""
    path = Path(override).expanduser().resolve() if override else ASSETS / 'vendor/DirectXTex/texconv.exe'
    require(path.is_file(), f'Missing texconv: {path}')
    return path


def run_command(args: list, log: list) -> None:
    """Run a deterministic subprocess without shell interpolation and retain evidence."""
    values = [str(value) for value in args]
    executable = None
    if sys.platform == 'win32' and len(values[0]) >= 260:
        executable = '\\\\?\\' + str(Path(values[0]).resolve())
    result = subprocess.run(values, executable=executable, capture_output=True, text=True, check=False)
    log.append({'argv': values, 'stdout': result.stdout, 'stderr': result.stderr,
                'exit_status': result.returncode})
    if result.returncode:
        raise RuntimeError(f'Encoder failed ({result.returncode}): {result.stdout}\n{result.stderr}')


def linear_resize(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    """Filter sRGB colour in linear light, not gamma-encoded RGB bytes."""
    channels = []
    for component in image.convert('RGB').split():
        srgb = np.asarray(component, dtype=np.float32) / 255
        linear = np.where(srgb <= .04045, srgb / 12.92, ((srgb + .055) / 1.055) ** 2.4)
        small = np.asarray(Image.fromarray(linear).resize(size, Image.Resampling.BOX))
        encoded = np.where(small <= .0031308, small * 12.92, 1.055 * small ** (1 / 2.4) - .055)
        channels.append(Image.fromarray(np.rint(np.clip(encoded, 0, 1) * 255).astype(np.uint8)))
    return Image.merge('RGB', channels)


def encode(image: Image.Image, target: Path, fourcc: str, encoder: Path,
           temporary: Path, log: list, mip_images: list[Image.Image] | None = None) -> None:
    """Encode a full legacy chain; apply the tested xy BC5 header adapter once."""
    temporary.mkdir(parents=True, exist_ok=True)
    source = temporary / f'{target.stem}.png'
    image.transpose(Image.Transpose.FLIP_TOP_BOTTOM).save(source)
    arguments = [encoder, '-nologo', '-y', '-dx9', '-f',
                 'BC1_UNORM' if fourcc == 'DXT1' else 'BC5_UNORM', '-m', '0']
    if fourcc == 'DXT1':
        arguments += ['-srgb', '-bc', 'u']
    run_command(arguments + ['-o', temporary, source], log)
    raw = bytearray(source.with_suffix('.dds').read_bytes())
    if fourcc == 'BC5U':
        require(raw[84:88] in (b'ATI2', b'BC5U'), 'Unexpected BC5 encoder header')
        raw[84:88] = b'BC5U'
    if mip_images is not None:
        require(fourcc == 'DXT1', 'Custom colour mips require BC1')
        for level, authored in zip(dds_levels(raw), mip_images, strict=True):
            mip_source = temporary / f'{target.stem}_m{level["mip"]:02d}.png'
            authored.transpose(Image.Transpose.FLIP_TOP_BOTTOM).save(mip_source)
            run_command([encoder, '-nologo', '-y', '-dx9', '-f', 'BC1_UNORM',
                         '-bc', 'u', '-m', '1', '-srgb', '-o', temporary, mip_source], log)
            encoded = mip_source.with_suffix('.dds').read_bytes()
            require(len(encoded) == 128 + level['bytes'], 'Encoded custom mip size mismatch')
            raw[level['offset']:level['offset'] + level['bytes']] = encoded[128:]
    dds_levels(raw)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(raw)


def neutral_base(encoder: Path) -> Path:
    """Create a neutral starting ZIP once from unbranded source maps."""
    target = ASSETS / 'stadium/neutral.zip'
    require(not target.exists(), 'Neutral base already exists; do not overwrite packaged resources')
    work = ASSETS / 'stadium/neutral_build'
    work.mkdir(exist_ok=True)
    log = []
    entries = {p.name: p.read_bytes() for p in (ASSETS / 'stadium/protected').glob('*.dds')}
    for name in ['Skin_B', 'Skin_R', 'Wheels_B', 'Wheels_R']:
        with Image.open(ASSETS / f'stadium/neutral_png/{name}.png') as image:
            path = work / f'{name}.dds'
            encode(image.convert('RGB'), path, 'DXT1' if name.endswith('_B') else 'BC5U',
                   encoder, work / 'encoding', log)
            entries[path.name] = path.read_bytes()
    icon = Image.new('RGB', (256, 256), '#22313e')
    ImageDraw.Draw(icon).rounded_rectangle((38, 75, 218, 190), radius=20, fill='#9faab1')
    buffer = io.BytesIO()
    icon.save(buffer, 'TGA')
    entries['Icon.tga'] = buffer.getvalue()
    save_zip(target, entries)
    inspect_zip(target)
    write_json(ASSETS / 'stadium/neutral-export-log.json', log)
    return target


def save_zip(path: Path, entries: dict[str, bytes]) -> None:
    """Write a flat deterministic ZIP with stable member timestamps."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in sorted(entries):
            item = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            item.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(item, entries[name], compresslevel=9)


def init_project(path: Path, name: str, base: Path | None) -> dict:
    """Start a new editable project and retain an immutable original ZIP copy."""
    require(not (path / 'project.json').exists(), 'Project already initialized; choose a new directory')
    require(name and all(c.isalnum() or c in '_-' for c in name), 'Use a simple skin name, no path characters')
    base = (base or ASSETS / 'stadium/neutral.zip').resolve()
    report = inspect_zip(base)
    for child in ['source/base', 'source/layers', 'cache', 'build', 'audit', 'deliverables']:
        (path / child).mkdir(parents=True, exist_ok=True)
    shutil.copy2(base, path / 'source/original.zip')
    with zipfile.ZipFile(base) as archive:
        for material in ['Skin', 'Wheels', 'Details']:
            for suffix in ['B', 'R']:
                raw = archive.read(f'{material}_{suffix}.dds')
                image = decode_level(raw, dds_levels(raw)[0])
                image.transpose(Image.Transpose.FLIP_TOP_BOTTOM).convert('RGB').save(
                    path / f'source/base/{material}_{suffix}.png')
    value = {'name': name, 'profile': profile()['id'], 'original_sha256': report['zip_sha256'],
             'original_name': base.name, 'changed_maps': [], 'game': 'GAME_PENDING'}
    write_json(path / 'project.json', value)
    return value


def project_info(path: Path) -> dict:
    """Verify the original backup every time the project is reopened."""
    value = read_json(path / 'project.json')
    require(value['profile'] == profile()['id'], 'Wrong project profile')
    require(sha(path / 'source/original.zip') == value['original_sha256'], 'Original backup was modified')
    return value


def geometry(material: str) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Read real accessors, with stride support, and stable UV components."""
    spec = profile()
    document = read_json(ASSETS / 'stadium/model/scene.gltf')
    binary = (ASSETS / 'stadium/model/scene.bin').read_bytes()

    def accessor(index: int) -> np.ndarray:
        """Read one tightly packed or strided numeric accessor."""
        item = document['accessors'][index]
        require('sparse' not in item, 'Sparse accessor requires a different mesh adapter')
        view = document['bufferViews'][item['bufferView']]
        dtype = np.dtype({5126: '<f4', 5125: '<u4', 5123: '<u2', 5121: 'u1'}[item['componentType']])
        width = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[item['type']]
        return np.ndarray((item['count'], width), dtype=dtype, buffer=binary,
                          offset=view.get('byteOffset', 0) + item.get('byteOffset', 0),
                          strides=(view.get('byteStride', width * dtype.itemsize), dtype.itemsize))

    positions, normals, uvs, triangles = [], [], [], []
    offset = 0
    for mesh in document['meshes']:
        for primitive in mesh['primitives']:
            if primitive['material'] != spec['materials'][material]:
                continue
            attrs = primitive['attributes']
            pos = accessor(attrs['POSITION'])
            positions.append(pos)
            normals.append(accessor(attrs['NORMAL']))
            uvs.append(accessor(attrs['TEXCOORD_0']))
            triangles.append(accessor(primitive['indices']).reshape(-1, 3) + offset)
            offset += len(pos)
    position, normal, uv, triangle = map(np.concatenate, (positions, normals, uvs, triangles))
    if material == 'Skin':
        with np.load(ASSETS / 'stadium/geometry/Skin.npz', allow_pickle=False) as known:
            require(np.array_equal(position, known['position']) and np.array_equal(uv, known['uv'])
                    and np.array_equal(triangle, known['triangles']), 'Skin cache geometry mismatch')
            ids = known['vertex_islands'].copy()
    else:
        _, inverse = np.unique(np.rint(uv * 100000).astype(np.int32), axis=0, return_inverse=True)
        parent = np.arange(int(inverse.max()) + 1)

        def find(index: int) -> int:
            """Compress a UV connectivity root."""
            while parent[index] != index:
                parent[index] = parent[parent[index]]
                index = parent[index]
            return int(index)

        for a, b, c in inverse[triangle]:
            root = find(a)
            parent[find(b)] = root
            parent[find(c)] = root
        roots = np.array([find(i) for i in inverse])
        unique, counts = np.unique(roots, return_counts=True)
        ordered = sorted(zip(unique.tolist(), counts.tolist()), key=lambda x: (-x[1], x[0]))
        mapping = {root: i for i, (root, _) in enumerate(ordered)}
        ids = np.array([mapping[int(root)] for root in roots])
    return position, normal, uv, triangle, ids


def uv_fields(path: Path, material: str, size: int) -> dict:
    """Rasterize immutable UV triangles into physical-coordinate painting fields."""
    require(64 <= size <= 4096 and size & (size - 1) == 0, 'UV size must be power-of-two 64..4096')
    cache = path / f'cache/{material}_{size}.npz'
    if cache.exists():
        with np.load(cache, allow_pickle=False) as stored:
            return {key: stored[key] for key in stored.files}
    points, normals, uv, triangles, ids = geometry(material)
    position = np.zeros((size, size, 3), np.float32)
    normal = np.zeros_like(position)
    island = np.full((size, size), -1, np.int32)
    coverage = np.zeros((size, size), np.uint16)
    wire = Image.new('RGB', (size, size), '#111f2b')
    draw = ImageDraw.Draw(wire)
    for triangle in triangles:
        vertices = uv[triangle] * size
        left, top = np.maximum(np.floor(vertices.min(0)).astype(int), 0)
        right, bottom = np.minimum(np.ceil(vertices.max(0)).astype(int), size - 1)
        if left > right or top > bottom:
            continue
        a, b, c = vertices
        determinant = (b[1]-c[1])*(a[0]-c[0]) + (c[0]-b[0])*(a[1]-c[1])
        if abs(determinant) < 1e-7:
            continue
        px, py = np.meshgrid(np.arange(left, right + 1) + .5, np.arange(top, bottom + 1) + .5)
        wa = ((b[1]-c[1])*(px-c[0]) + (c[0]-b[0])*(py-c[1])) / determinant
        wb = ((c[1]-a[1])*(px-c[0]) + (a[0]-c[0])*(py-c[1])) / determinant
        wc = 1 - wa - wb
        inside = (wa >= -1e-5) & (wb >= -1e-5) & (wc >= -1e-5)
        weights = np.stack((wa, wb, wc), axis=-1)
        position[top:bottom + 1, left:right + 1][inside] = (weights @ points[triangle])[inside]
        normal[top:bottom + 1, left:right + 1][inside] = (weights @ normals[triangle])[inside]
        island[top:bottom + 1, left:right + 1][inside] = ids[triangle[0]]
        coverage[top:bottom + 1, left:right + 1][inside] += 1
        draw.line([tuple(v) for v in vertices] + [tuple(a)], fill='#67a6be', width=1)
    normal /= np.maximum(np.linalg.norm(normal, axis=-1, keepdims=True), 1e-8)
    result = {'position': position, 'normal': normal, 'island': island, 'mask': island >= 0}
    cache.parent.mkdir(exist_ok=True)
    np.savez_compressed(cache, **result)
    wire.save(path / f'audit/{material}_{size}_UV.png')
    colour = np.zeros((size, size, 3), np.uint8)
    for index in np.unique(island[island >= 0]):
        colour[island == index] = ((int(index) * 47 + 61) % 200 + 40,
                                  (int(index) * 91 + 33) % 200 + 40,
                                  (int(index) * 29 + 17) % 200 + 40)
    Image.fromarray(colour).save(path / f'audit/{material}_{size}_islands.png')
    components = []
    for index in np.unique(ids):
        selected = ids == index
        components.append({'id': int(index), 'uv_min': uv[selected].min(0).tolist(),
                           'uv_max': uv[selected].max(0).tolist(),
                           'position_min': points[selected].min(0).tolist(),
                           'position_max': points[selected].max(0).tolist()})
    write_json(path / f'audit/{material}_{size}_geometry.json', {
        'model_bin_sha256': profile()['model_bin_sha256'], 'triangles': len(triangles),
        'covered_pixels': int((island >= 0).sum()), 'overlap_pixels': int((coverage > 1).sum()),
        'components': components})
    return result


def mask_for(fields: dict, options: dict, material: str) -> np.ndarray:
    """Intersect named/component/physical/normal constraints, rejecting unknown keys."""
    require(set(options) <= {'region', 'islands', 'position', 'normal', 'inset'}, 'Unknown mask key')
    selected = fields['mask'].copy()
    if 'region' in options:
        require(material == 'Skin', 'Named regions only apply to the hashed Skin material')
        selected &= np.isin(fields['island'], profile()['regions'][options['region']])
    if 'islands' in options:
        selected &= np.isin(fields['island'], options['islands'])
    for key in ['position', 'normal']:
        for axis, bounds in options.get(key, {}).items():
            require(axis in 'xyz' and len(axis) == 1, 'Axis must be x/y/z')
            require(len(bounds) == 2 and bounds[0] <= bounds[1], 'Invalid mask interval')
            coordinate = fields[key][:, :, 'xyz'.index(axis)]
            selected &= (coordinate >= bounds[0]) & (coordinate <= bounds[1])
    inset = options.get('inset', 0)
    require(isinstance(inset, int) and 0 <= inset <= 64, 'Inset must be 0..64 pixels')
    if inset:
        padded = np.pad(selected.astype(np.uint8) * 255, inset)
        eroded = Image.fromarray(padded).filter(ImageFilter.MinFilter(inset * 2 + 1))
        selected = np.asarray(eroded)[inset:-inset, inset:-inset] > 0
    return selected


def projected(image: Image.Image, fields: dict, layer: dict) -> Image.Image:
    """Bilinearly sample RGBA artwork in physical space with premultiplied alpha."""
    axes, ranges = layer['axes'], layer['ranges']
    require(len(axes) == 2 and len(set(axes)) == 2 and all(i in (0, 1, 2) for i in axes),
            'Projection needs two distinct coordinate axes')
    require(len(ranges) == 2 and all(len(r) == 2 and r[0] != r[1] for r in ranges), 'Bad projection ranges')
    position = fields['position']
    u = (position[:, :, axes[0]] - ranges[0][0]) / (ranges[0][1] - ranges[0][0])
    v = (position[:, :, axes[1]] - ranges[1][0]) / (ranges[1][1] - ranges[1][0])
    if layer.get('flip_u'):
        u = 1 - u
    if layer.get('flip_v'):
        v = 1 - v
    keep = fields['mask'].copy()
    if layer.get('repeat'):
        u, v = u % 1, v % 1
    else:
        keep &= (u >= 0) & (u <= 1) & (v >= 0) & (v <= 1)
    samples = np.asarray(image.convert('RGBA'), dtype=np.float32) / 255
    samples[:, :, :3] *= samples[:, :, 3:4]
    x = np.clip(u, 0, 1) * (image.width - 1)
    y = np.clip(v, 0, 1) * (image.height - 1)
    x0, y0 = x.astype(int), y.astype(int)
    x1, y1 = np.minimum(x0 + 1, image.width - 1), np.minimum(y0 + 1, image.height - 1)
    fx, fy = (x - x0)[:, :, None], (y - y0)[:, :, None]
    top = samples[y0, x0] * (1 - fx) + samples[y0, x1] * fx
    bottom = samples[y1, x0] * (1 - fx) + samples[y1, x1] * fx
    result = top * (1 - fy) + bottom * fy
    result[:, :, :3] /= np.maximum(result[:, :, 3:4], 1e-8)
    result[~keep] = 0
    return Image.fromarray(np.rint(np.clip(result, 0, 1) * 255).astype(np.uint8))


def padding(image: Image.Image, occupied: np.ndarray, count: int = 12) -> Image.Image:
    """Extend colours into empty pixels without repainting another occupied island."""
    pixels = np.array(image.convert('RGB'))
    active = occupied.copy()
    for _ in range(count):
        expanded = active.copy()
        for dy, dx in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            moved = np.roll(active, (dy, dx), (0, 1))
            if dy:
                moved[0 if dy > 0 else -1] = False
            if dx:
                moved[:, 0 if dx > 0 else -1] = False
            fill = moved & ~expanded
            pixels[fill] = np.roll(pixels, (dy, dx), (0, 1))[fill]
            expanded |= fill
        active = expanded
    return Image.fromarray(pixels)


def png_bytes(image: Image.Image) -> bytes:
    """Encode an image to lossless PNG in memory."""
    stream = io.BytesIO()
    image.save(stream, 'PNG')
    return stream.getvalue()


def save_ora(path: Path, layers: list[tuple[str, Image.Image]], merged: Image.Image) -> None:
    """Write editable bottom-to-top layer sources to a standard OpenRaster archive."""
    root = ET.Element('image', w=str(merged.width), h=str(merged.height), version='0.0.3')
    stack = ET.SubElement(root, 'stack')
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('mimetype', 'image/openraster', compress_type=zipfile.ZIP_STORED)
        for index, (name, image) in enumerate(reversed(layers)):
            source = f'data/layer{index:03d}.png'
            ET.SubElement(stack, 'layer', name=name, src=source, opacity='1.0', visibility='visible',
                          x='0', y='0', **{'composite-op': 'svg:src-over'})
            archive.writestr(source, png_bytes(image))
        archive.writestr('stack.xml', ET.tostring(root, encoding='utf-8'))
        archive.writestr('mergedimage.png', png_bytes(merged))
        thumb = merged.copy()
        thumb.thumbnail((256, 256))
        archive.writestr('Thumbnails/thumbnail.png', png_bytes(thumb))


def compose(path: Path, recipe_path: Path) -> dict:
    """Build editable materials with explicit physical projection and clipping."""
    info = project_info(path)
    recipe = read_json(recipe_path)
    portable_recipe = json.loads(json.dumps(recipe))
    size = recipe.get('source_size', 2048)
    require(64 <= size <= 4096 and size & (size - 1) == 0, 'Invalid source_size')
    manifest = {'materials': {}, 'source_size': size, 'recipe': recipe_path.name}
    for material, definition in recipe['materials'].items():
        require(material in ('Skin', 'Wheels'), 'Functional Details maps are protected; audit a separate adapter before editing')
        fields = uv_fields(path, material, size)
        with Image.open(path / f'source/base/{material}_B.png') as original:
            base = original.convert('RGBA').resize((size, size), Image.Resampling.LANCZOS)
        layers = [('Original base', base)]
        layer_manifest = []
        for index, description in enumerate(definition.get('layers', [])):
            kind = description['type']
            if kind == 'fill':
                layer = Image.new('RGBA', (size, size), ImageColor.getrgb(description['color']) + (255,))
            elif kind in ('project', 'atlas'):
                source = (recipe_path.parent / description['image']).resolve()
                inputs = path / 'source/inputs'
                inputs.mkdir(exist_ok=True)
                saved_input = inputs / f'{material}_{index:03d}{source.suffix.lower()}'
                if source != saved_input.resolve():
                    shutil.copy2(source, saved_input)
                portable_recipe['materials'][material]['layers'][index]['image'] = (
                    saved_input.relative_to(path / 'source').as_posix())
                with Image.open(source) as image:
                    if kind == 'project':
                        layer = projected(image, fields, description)
                    else:
                        require(image.size == (size, size), 'Atlas asset dimensions differ from source_size')
                        layer = image.convert('RGBA')
            else:
                raise ValueError(f'Unknown layer type: {kind}')
            selected = mask_for(fields, description.get('mask', {}), material)
            opacity = description.get('opacity', 1)
            require(0 <= opacity <= 1, 'Opacity must be 0..1')
            alpha = np.asarray(layer.getchannel('A'), dtype=np.float32) * selected * opacity
            layer.putalpha(Image.fromarray(np.rint(alpha).astype(np.uint8)))
            require(np.asarray(layer.getchannel('A')).any(), f'Layer has no ink: {description["name"]}')
            saved = f'source/layers/{material}_{index:03d}.png'
            layer.save(path / saved)
            layer_manifest.append({'name': description['name'], 'file': saved,
                                   'lod_opacity': description.get('lod_opacity', [1])})
            require(all(0 <= value <= 1 for value in layer_manifest[-1]['lod_opacity'])
                    and layer_manifest[-1]['lod_opacity'], 'Invalid lod_opacity')
            layers.append((description['name'], layer))
        merged = base.copy()
        for _, image in layers[1:]:
            merged.alpha_composite(image)
        padding(merged, fields['mask']).save(path / f'source/{material}_B.png')
        save_ora(path / f'source/{material}_BaseColor.ora', layers, merged)
        with Image.open(path / f'source/base/{material}_R.png') as original:
            surface = np.array(original.convert('RGB').resize((size, size), Image.Resampling.BILINEAR))
        for change in definition.get('surface', []):
            selected = mask_for(fields, change.get('mask', {}), material)
            for key, channel in [('roughness', 0), ('metalness', 1)]:
                if key in change:
                    require(0 <= change[key] <= 1, f'{key} must be 0..1')
                    surface[:, :, channel][selected] = round(change[key] * 255)
        changed = [f'{material}_B.dds']
        if definition.get('surface'):
            Image.fromarray(surface).save(path / f'source/{material}_R.png')
            changed.append(f'{material}_R.dds')
        manifest['materials'][material] = {'layers': layer_manifest, 'changed_maps': changed}
    info['changed_maps'] = sorted(n for d in manifest['materials'].values() for n in d['changed_maps'])
    write_json(path / 'source/composition.json', manifest)
    write_json(path / 'source/recipe.original.json', recipe)
    write_json(path / 'source/recipe.json', portable_recipe)
    write_json(path / 'project.json', info)
    return manifest


def export_project(path: Path, encoder: Path) -> Path:
    """Replace only composed maps, leaving the original package independently intact."""
    info = project_info(path)
    manifest = read_json(path / 'source/composition.json')
    log = []
    with zipfile.ZipFile(path / 'source/original.zip') as archive:
        entries = {n: archive.read(n) for n in archive.namelist()}
    for material, definition in manifest['materials'].items():
        size = manifest['source_size']
        fields = uv_fields(path, material, size)
        with Image.open(path / f'source/base/{material}_B.png') as image:
            base = image.convert('RGBA').resize((size, size), Image.Resampling.LANCZOS)
        name = f'{material}_B.dds'
        original_levels = dds_levels(entries[name])
        authored_mips = []
        for level in original_levels:
            canvas = base.copy()
            for layer in definition['layers']:
                with Image.open(path / layer['file']) as image:
                    ink = image.convert('RGBA')
                values = layer['lod_opacity']
                scale = values[min(level['mip'], len(values) - 1)]
                if scale != 1:
                    ink.putalpha(ink.getchannel('A').point(lambda a: round(a * scale)))
                canvas.alpha_composite(ink)
            authored_mips.append(linear_resize(padding(canvas, fields['mask']),
                                               (level['width'], level['height'])))
        output = path / 'build' / name
        encode(authored_mips[0], output, 'DXT1', encoder, path / 'cache/encoding', log, authored_mips)
        entries[name] = output.read_bytes()
        if f'{material}_R.dds' in definition['changed_maps']:
            name = f'{material}_R.dds'
            level = dds_levels(entries[name])[0]
            with Image.open(path / f'source/{material}_R.png') as image:
                data = image.convert('RGB').resize((level['width'], level['height']), Image.Resampling.BOX)
            output = path / 'build' / name
            encode(data, output, 'BC5U', encoder, path / 'cache/encoding', log)
            entries[name] = output.read_bytes()
    icon = path / 'source/Icon.tga'
    if icon.exists():
        entries['Icon.tga'] = icon.read_bytes()
        if 'Icon.tga' not in info['changed_maps']:
            info['changed_maps'].append('Icon.tga')
    target = path / f'deliverables/{info["name"]}.zip'
    save_zip(target, entries)
    report = inspect_zip(target, path / 'audit/package.json')
    with zipfile.ZipFile(path / 'source/original.zip') as old:
        actual_changes = sorted(n for n, data in entries.items() if old.read(n) != data)
    require(set(actual_changes) <= set(info['changed_maps']), 'Unrequested map changed')
    report.update(changed_entries=actual_changes, original_sha256=info['original_sha256'],
                  encoder_sha256=sha(encoder), preview='NOT_INSPECTED')
    write_json(path / 'audit/package.json', report)
    write_json(path / 'audit/export_commands.json', log)
    write_json(path / 'project.json', info)
    return target


def preview(path: Path) -> Path:
    """Prepare a self-contained static viewer of the real compressed colour mips."""
    info = project_info(path)
    target = path / f'deliverables/{info["name"]}.zip'
    inspect_zip(target)
    view = path / 'preview'
    view.mkdir(exist_ok=True)
    shutil.copytree(ASSETS / 'stadium/model', view / 'model', dirs_exist_ok=True)
    shutil.copytree(ASSETS / 'vendor/three', view / 'vendor/three', dirs_exist_ok=True)
    shutil.copy2(ASSETS / 'viewer.html', view / 'viewer.html')
    (view / 'dds').mkdir(exist_ok=True)
    (view / 'decoded').mkdir(exist_ok=True)
    with zipfile.ZipFile(target) as archive:
        for material in ['Skin', 'Wheels', 'Details']:
            raw = archive.read(f'{material}_B.dds')
            (view / f'dds/{material}_B.dds').write_bytes(raw)
            levels = dds_levels(raw)
            sheet = Image.new('RGB', (768, 512), '#e0e4e9')
            draw = ImageDraw.Draw(sheet)
            for index, level in enumerate(levels[:6]):
                stored = decode_level(raw, level)
                stored.transpose(Image.Transpose.FLIP_TOP_BOTTOM).save(
                    path / f'audit/{material}_stored_m{index}.png')
                thumbnail = stored.transpose(Image.Transpose.FLIP_TOP_BOTTOM).convert('RGB')
                thumbnail = thumbnail.resize((256, 230), Image.Resampling.NEAREST)
                x, y = index % 3 * 256, index // 3 * 256
                sheet.paste(thumbnail, (x, y + 26))
                draw.text((x + 5, y + 5), f'M{index} {level["width"]}x{level["height"]}', fill='#132335')
            sheet.save(path / f'audit/{material}_STORED_MIPS.png')
            data = archive.read(f'{material}_R.dds')
            channels = decode_level(data, dds_levels(data)[0]).convert('RGB').split()
            Image.merge('RGB', (Image.new('L', channels[0].size, 255), channels[0], channels[1])).save(
                view / f'decoded/{material}_PBR.png')
        normal = archive.read('Wheels_N.dds')
        encoded = np.array(decode_level(normal, dds_levels(normal)[0]).convert('RGB'))
        xy = encoded[:, :, :2].astype(np.float32) / 127.5 - 1
        encoded[:, :, 2] = np.rint((np.sqrt(np.maximum(0, 1 - (xy * xy).sum(-1))) + 1) * 127.5).astype(np.uint8)
        Image.fromarray(encoded).save(view / 'decoded/Wheels_N.png')
    shutil.copy2(ASSETS / 'stadium/model/LICENSE.txt', path / 'source/MODEL_LICENSE.txt')
    return view / 'viewer.html'


def bundle_sources(path: Path) -> Path:
    """Package editable source and provenance, excluding generated geometry caches."""
    info = project_info(path)
    target = path / f'deliverables/{info["name"]}_sources.zip'
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as archive:
        for folder in ['source', 'audit']:
            for item in sorted((path / folder).rglob('*')):
                if item.is_file():
                    archive.write(item, item.relative_to(path).as_posix())
        archive.write(path / 'project.json', 'project.json')
    with zipfile.ZipFile(target) as archive:
        require(archive.testzip() is None, 'Source ZIP CRC mismatch')
    return target


def main() -> None:
    """Dispatch explicit project operations; failures exit nonzero with a concrete reason."""
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    doctor = commands.add_parser('doctor', help='Inspect dependencies, geometry and encoder')
    doctor.add_argument('--texconv')
    neutral = commands.add_parser('make-neutral', help=argparse.SUPPRESS)
    neutral.add_argument('--texconv')
    init = commands.add_parser('init', help='Copy and audit a base ZIP, create editable project')
    init.add_argument('--project', type=Path, required=True)
    init.add_argument('--name', required=True)
    init.add_argument('--base', type=Path)
    uv = commands.add_parser('uv', help='Rasterize actual UV geometry and physical fields')
    uv.add_argument('--project', type=Path, required=True)
    uv.add_argument('--material', choices=['Skin', 'Wheels', 'Details'], required=True)
    uv.add_argument('--size', type=int, default=2048)
    compose_cmd = commands.add_parser('compose', help='Compose a layered physical-placement recipe')
    compose_cmd.add_argument('--project', type=Path, required=True)
    compose_cmd.add_argument('--recipe', type=Path, required=True)
    export = commands.add_parser('export', help='Export a compatible ZIP with all stored mips audited')
    export.add_argument('--project', type=Path, required=True)
    export.add_argument('--texconv')
    inspect = commands.add_parser('inspect', help='Inspect an actual import ZIP and every mip')
    inspect.add_argument('--zip', type=Path, required=True)
    inspect.add_argument('--report', type=Path)
    for name, help_text in [('preview', 'Prepare a native DDS viewer and decoded mip sheets'),
                            ('bundle-sources', 'Package editable sources and audit evidence')]:
        command = commands.add_parser(name, help=help_text)
        command.add_argument('--project', type=Path, required=True)
    args = parser.parse_args()
    if hasattr(args, 'project'):
        args.project = args.project.resolve()
    if args.command == 'doctor':
        import PIL
        encoder = texconv_path(args.texconv)
        profile()
        if not args.texconv and (ROOT / 'ASSET_MANIFEST.json').exists():
            manifest = read_json(ROOT / 'ASSET_MANIFEST.json')
            require(sha(encoder) == manifest['files']['assets/vendor/DirectXTex/texconv.exe'],
                    'Bundled encoder hash differs from pinned manifest')
        log = []
        run_command([encoder, '--help'], log)
        print(json.dumps({'status': 'DOCTOR_OK', 'python': sys.version.split()[0],
                          'pillow': PIL.__version__, 'numpy': np.__version__,
                          'encoder': str(encoder), 'encoder_sha256': sha(encoder),
                          'profile': profile()['id']}, ensure_ascii=False))
    elif args.command == 'make-neutral':
        print(f'NEUTRAL_OK: {neutral_base(texconv_path(args.texconv))}')
    elif args.command == 'init':
        value = init_project(args.project, args.name, args.base)
        print(f'INIT_OK: original_sha256={value["original_sha256"]}')
    elif args.command == 'uv':
        project_info(args.project)
        fields = uv_fields(args.project, args.material, args.size)
        print(f'UV_OK: {args.material} {args.size}x{args.size}; covered={fields["mask"].sum()}')
    elif args.command == 'compose':
        result = compose(args.project, args.recipe.resolve())
        print(f'COMPOSE_OK: {len(result["materials"])} materials; editable ORA and layers saved')
    elif args.command == 'export':
        print(f'EXPORT_OK: {export_project(args.project, texconv_path(args.texconv))}; GAME_PENDING')
    elif args.command == 'inspect':
        report = inspect_zip(args.zip, args.report)
        print(f'FILES_VERIFIED: {len(report["textures"])} textures; {report["mips_decoded"]} stored mips decoded; CRC OK; GAME_PENDING')
    elif args.command == 'preview':
        print(f'PREVIEW_READY: {preview(args.project)}; serve project directory on loopback; visual inspection pending')
    elif args.command == 'bundle-sources':
        print(f'SOURCES_OK: {bundle_sources(args.project)}')


if __name__ == '__main__':
    main()
