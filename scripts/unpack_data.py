#!/usr/bin/env python3
"""Verify and restore all preserved study data, or one selected release."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', help='Restore only this selected release (all by default)')
    parser.add_argument('--verify-only', action='store_true', help='Check archives and member hashes without writing')
    args = parser.parse_args()
    manifest = json.loads((ROOT / 'archives/manifest.json').read_text())
    bundles = [b for b in manifest['bundles'] if not args.version or b.get('version') == args.version]
    if not bundles:
        parser.error('Version is not in the preserved dataset')
    files = 0
    for bundle in bundles:
        path = ROOT / bundle['path']
        if sha(path.read_bytes()) != bundle['sha256']:
            raise ValueError(f'Archive checksum mismatch: {path}')
        expected = {m['path']: m for m in bundle['members']}
        with zipfile.ZipFile(path) as archive:
            if len(archive.namelist()) != len(expected) or set(archive.namelist()) != set(expected):
                raise ValueError(f'Archive member set mismatch: {path}')
            for name, record in expected.items():
                relative = PurePosixPath(name)
                if relative.is_absolute() or '..' in relative.parts or relative.parts[0] not in ('data', 'results'):
                    raise ValueError(f'Invalid archive path: {name}')
                content = archive.read(name)
                if len(content) != record['bytes'] or sha(content) != record['sha256']:
                    raise ValueError(f'Member checksum mismatch: {name}')
                target = ROOT / relative
                if not args.verify_only:
                    if target.exists() and target.read_bytes() != content:
                        raise ValueError(f'Existing file differs; move it aside before restoring: {target}')
                    target.parent.mkdir(parents=True, exist_ok=True)
                    if not target.exists():
                        target.write_bytes(content)
                files += 1
        print(f'{bundle["path"]}: verified {len(expected)} files', flush=True)
    print(f'Verified {files} files in {len(bundles)} archives' + ('; no files written' if args.verify_only else '; working hierarchy restored'))


if __name__ == '__main__':
    main()
