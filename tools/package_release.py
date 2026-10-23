"""Build public plugin/marketplace/skill ZIPs from one inspected source tree."""

import hashlib
import json
from pathlib import Path
import zipfile

from validate_public import PLUGIN, ROOT, SKILL, validate


def package(target: Path, files: list[tuple[Path, str]]) -> None:
    """Write deterministic paths/timestamps and reopen the finished archive."""
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path, name in sorted(files, key=lambda item: item[1]):
            entry = zipfile.ZipInfo(name, (2026, 10, 23, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = (0o755 if path.suffix == '.sh' else 0o644) << 16
            archive.writestr(entry, path.read_bytes(), compresslevel=9)
    with zipfile.ZipFile(target) as archive:
        if archive.testzip() is not None:
            raise ValueError(f'Archive CRC failed: {target.name}')


def main() -> None:
    """Produce three independently installable archive formats and their hashes."""
    validate()
    destination = ROOT / 'dist'
    destination.mkdir(exist_ok=True)
    version = json.loads((PLUGIN / 'plugin.json').read_text(encoding='utf-8'))['version']
    plugin_files = [(p, p.relative_to(PLUGIN).as_posix()) for p in PLUGIN.rglob('*')
                    if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc']
    package(destination / f'trackmania-livery-studio-plugin-{version}.zip', plugin_files)
    market_files = [(p, 'plugins/trackmania-livery-studio/' + name) for p, name in plugin_files]
    for relative in ['.agents/plugins/marketplace.json', 'README.md', 'README.ru.md', 'LICENSE', 'THIRD_PARTY.md']:
        market_files.append((ROOT / relative, relative))
    for folder in ['docs', 'examples']:
        for path in (ROOT / folder).rglob('*'):
            if path.is_file() and '__pycache__' not in path.parts and path.suffix != '.pyc':
                market_files.append((path, path.relative_to(ROOT).as_posix()))
    package(destination / f'trackmania-livery-studio-marketplace-{version}.zip', market_files)
    skill_files = [(p, 'trackmania-livery-studio/' + p.relative_to(SKILL).as_posix())
                   for p in SKILL.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc']
    package(destination / f'trackmania-livery-studio-skill-{version}.zip', skill_files)
    lines = [f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}'
             for p in sorted(destination.iterdir()) if p.is_file() and p.name != 'SHA256SUMS.txt']
    (destination / 'SHA256SUMS.txt').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f'PACKAGE_OK: 3 reopened archives; version={version}; SHA256SUMS.txt')


if __name__ == '__main__':
    main()
