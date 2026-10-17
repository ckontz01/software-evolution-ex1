#!/usr/bin/env python3
"""Package complete raw and computed data without discarding any study evidence."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pack(name: str, paths: list[Path]) -> dict:
    target = ROOT / 'archives' / name
    target.parent.mkdir(parents=True, exist_ok=True)
    members = []
    with zipfile.ZipFile(target, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in sorted(paths):
            if not path.is_file() or '__pycache__' in path.parts:
                continue
            relative = path.relative_to(ROOT).as_posix()
            info = zipfile.ZipInfo(relative, date_time=(2026, 10, 17, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)
            members.append({'path': relative, 'bytes': path.stat().st_size, 'sha256': digest(path)})
    return {'path': target.relative_to(ROOT).as_posix(), 'bytes': target.stat().st_size,
            'sha256': digest(target), 'member_count': len(members), 'members': members}


def main() -> None:
    manifest = json.loads((ROOT / 'config/versions.json').read_text())
    bundles = []
    for release in manifest['versions']:
        version = release['version']
        paths = []
        for prefix in ('data/raw', 'data/graphs', 'results/versions'):
            directory = ROOT / prefix / version
            if not directory.is_dir():
                raise FileNotFoundError(directory)
            paths.extend(directory.rglob('*'))
        record = pack(f'versions/guava-{version}.zip', paths)
        record['version'] = version
        bundles.append(record)
        print(version, record['member_count'], record['bytes'], flush=True)
    bundles.append(pack('pilot.zip', list((ROOT / 'results/pilot').rglob('*'))))
    payload = {'format': 'ZIP/deflate; fixed timestamps; complete original file bytes',
               'purpose': 'All 90 acquired artifacts and every per-release computed file, including raw algorithm logs, are preserved. Unpack to restore the documented working hierarchy.',
               'version_manifest_sha256': digest(ROOT / 'config/versions.json'),
               'bundles': bundles}
    (ROOT / 'archives/manifest.json').write_text(json.dumps(payload, indent=2) + '\n')


if __name__ == '__main__':
    main()
