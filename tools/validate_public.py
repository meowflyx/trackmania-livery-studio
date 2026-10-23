"""Audit publishable files, hashes, manifests and embedded archive boundaries."""

import hashlib
import io
import json
from pathlib import Path
import re
import sys
import zipfile


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / 'plugins/trackmania-livery-studio'
SKILL = PLUGIN / 'skills/trackmania-livery-studio'
EXCLUDED = {'.git', '.work', '.venv', 'dist', '__pycache__'}


def require(condition: bool, message: str) -> None:
    """Keep validation active even under python -O."""
    if not condition:
        raise ValueError(message)


def validate() -> dict:
    """Verify actual bytes and public metadata without printing credentials or paths."""
    files = [p for p in ROOT.rglob('*') if p.is_file()
             and not set(p.relative_to(ROOT).parts) & EXCLUDED]
    private_path = re.compile(r'[A-Z]:[\\/]Users[\\/]|/(?:home|Users)/[^/\s]+/')
    credential = re.compile(r'gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|sk-[A-Za-z0-9]{30,}')
    for path in files:
        require(path.suffix not in {'.log', '.pyc'}, f'Private/generated file in public tree: {path.name}')
        if path.suffix in {'.md', '.json', '.py', '.yml', '.yaml', '.txt', '.cjs', '.html', '.patch'}:
            text = path.read_text(encoding='utf-8')
            require(not private_path.search(text), f'Private absolute path in {path.relative_to(ROOT)}')
            require(not credential.search(text), f'Credential pattern in {path.relative_to(ROOT)}')
            if path.suffix == '.json':
                scan_json(json.loads(text), private_path, credential, path.name)
    metadata = json.loads((PLUGIN / 'plugin.json').read_text(encoding='utf-8'))
    require(metadata['$schema'] == 'https://agent-plugins.org/schemas/1.0.0/plugin.schema.json', 'Wrong manifest schema')
    require(metadata['name'] == 'trackmania-livery-studio', 'Wrong plugin identity')
    require(metadata['extensions']['com.openai']['requires_local_executor'] is True, 'Desktop requirement lost')
    require('made it public simply because' in (ROOT / 'README.md').read_text(encoding='utf-8'), 'Publisher motivation missing')
    require('created with AI' in (ROOT / 'README.md').read_text(encoding='utf-8'), 'AI disclosure missing')
    require('создан с помощью ИИ' in (ROOT / 'README.ru.md').read_text(encoding='utf-8'), 'Russian AI disclosure missing')
    for relative in ['LICENSE', 'THIRD_PARTY.md', 'README.md', 'README.ru.md', 'docs/VALIDATION.md', '.agents/plugins/marketplace.json']:
        require((ROOT / relative).is_file(), f'Missing public file: {relative}')
    manifest = json.loads((SKILL / 'ASSET_MANIFEST.json').read_text(encoding='utf-8'))
    for name, expected in manifest['files'].items():
        path = (SKILL / name).resolve()
        require(path.is_relative_to(SKILL.resolve()), 'Asset path escaped skill')
        require(hashlib.sha256(path.read_bytes()).hexdigest() == expected, f'Pinned asset differs: {name}')
    exe = SKILL / 'assets/vendor/DirectXTex/texconv.exe'
    require(hashlib.sha256(exe.read_bytes()).hexdigest() == 'dcfdec10244e02cf5037fba089c55fb7e1326b1c8181742d77d15fa5cb5eef06', 'Encoder differs from official may2026 digest')
    for path in files:
        if path.suffix == '.zip':
            with zipfile.ZipFile(path) as archive:
                require(archive.testzip() is None, f'ZIP CRC mismatch: {path.name}')
                for name in archive.namelist():
                    require(not Path(name).is_absolute() and '..' not in Path(name).parts,
                            f'Unsafe bundled ZIP path: {name}')
    sys.path.insert(0, str(SKILL / 'scripts'))
    import studio
    report = studio.inspect_zip(SKILL / 'assets/stadium/neutral.zip')
    return {'status': 'PUBLIC_VALIDATION_OK', 'files_checked': len(files),
            'pinned_assets': len(manifest['files']), 'neutral_mips': report['mips_decoded'],
            'checks': ['AI disclosure', 'publisher motivation', 'private paths', 'credential patterns',
                       'asset hashes', 'official encoder digest', 'licenses', 'archive CRC/mips'],
            'game': 'GAME_PENDING'}


def scan_json(value, private_path: re.Pattern, credential: re.Pattern, label: str) -> None:
    """Scan decoded JSON values so backslash escaping cannot hide a private root."""
    if isinstance(value, str):
        require(not private_path.search(value), f'Private path in JSON: {label}')
        require(not credential.search(value), f'Credential pattern in JSON: {label}')
    elif isinstance(value, list):
        for item in value:
            scan_json(item, private_path, credential, label)
    elif isinstance(value, dict):
        for item in value.values():
            scan_json(item, private_path, credential, label)


def scan_archives(folder: Path) -> int:
    """Reopen release archives and recursively inspect nested text/JSON members."""
    private_path = re.compile(r'[A-Z]:[\\/]Users[\\/]|/(?:home|Users)/[^/\s]+/')
    credential = re.compile(r'gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|sk-[A-Za-z0-9]{30,}')

    def inspect(raw: bytes, label: str, depth: int = 0) -> None:
        """Inspect known generated ZIP/ORA containers without extracting paths."""
        require(depth <= 5, 'Unexpected nested archive depth')
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            require(archive.testzip() is None, f'Bad CRC: {label}')
            for name in archive.namelist():
                require(not name.startswith(('/', '\\')) and '..' not in Path(name).parts,
                        f'Unsafe release archive member: {label}')
                data = archive.read(name)
                suffix = Path(name).suffix
                if suffix in {'.zip', '.ora'}:
                    inspect(data, f'{label}/{name}', depth + 1)
                elif suffix in {'.json', '.md', '.txt', '.py', '.html', '.yaml', '.yml', '.cjs'}:
                    text = data.decode('utf-8')
                    require(not private_path.search(text), f'Private text path in archive: {label}/{name}')
                    require(not credential.search(text), f'Credential pattern in archive: {label}/{name}')
                    if suffix == '.json':
                        scan_json(json.loads(text), private_path, credential, f'{label}/{name}')
    paths = list(folder.glob('*.zip'))
    for path in paths:
        inspect(path.read_bytes(), path.name)
    return len(paths)


if __name__ == '__main__':
    result = validate()
    if '--archives' in sys.argv:
        result['release_archives_scanned'] = scan_archives(ROOT / 'dist')
    print(json.dumps(result, ensure_ascii=False))
