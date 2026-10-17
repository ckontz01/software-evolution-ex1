#!/usr/bin/env python3
"""Verify and restore all preserved study data, or one selected release."""
from __future__ import annotations
import argparse
import base64
import binascii
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import stat
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PART_BYTES = 512 * 1024


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_path(name: str, allowed_roots: tuple[str, ...]) -> Path:
    """Reject traversal, alternate separators, and filesystem symlink escapes."""
    if not isinstance(name, str) or not name or '\\' in name or '\0' in name:
        raise ValueError(f'Invalid archive path: {name!r}')
    relative = PurePosixPath(name)
    if relative.is_absolute() or '..' in relative.parts or relative.as_posix() != name or len(relative.parts) < 2 or relative.parts[0] not in allowed_roots:
        raise ValueError(f'Invalid archive path: {name}')
    target = ROOT
    for piece in relative.parts:
        target /= piece
        if target.is_symlink():
            raise ValueError(f'Symlink in archive path: {name}')
    if not target.resolve().is_relative_to(ROOT.resolve()):
        raise ValueError(f'Archive path escapes repository: {name}')
    return target


def logical_zip_bytes(bundle: dict) -> bytes:
    logical = safe_path(bundle['path'], ('archives',))
    if logical.suffix != '.zip' or not re.fullmatch(r'[0-9a-f]{64}', bundle['sha256']):
        raise ValueError(f'Invalid logical ZIP record: {bundle["path"]}')
    storage = bundle.get('storage', 'whole')
    if storage == 'whole':
        if bundle.get('parts') or bundle.get('encoded_file'):
            raise ValueError('Whole ZIP record cannot also declare another physical storage')
        content = logical.read_bytes()
    elif storage == 'base64':
        encoded_file = bundle.get('encoded_file')
        if not isinstance(encoded_file, dict) or bundle.get('parts') or bundle.get('part_size_bytes'):
            raise ValueError('Base64 ZIP requires a single encoded file record')
        physical = safe_path(encoded_file['path'], ('archives',))
        expected_size = 4 * ((bundle['bytes'] + 2) // 3)
        if encoded_file['path'] != bundle['path'] + '.b64' or encoded_file.get('text_encoding') != 'ascii' or not re.fullmatch(r'[0-9a-f]{64}', encoded_file['sha256']):
            raise ValueError('Invalid encoded ZIP path or encoding record')
        encoded = physical.read_bytes()
        if encoded_file['bytes'] != expected_size or len(encoded) != expected_size or sha(encoded) != encoded_file['sha256']:
            raise ValueError(f'Encoded ZIP checksum/size mismatch: {encoded_file["path"]}')
        try:
            content = base64.b64decode(encoded, validate=True)
        except (ValueError, binascii.Error) as error:
            raise ValueError('Invalid strict base64 ZIP content') from error
        if base64.b64encode(content) != encoded:
            raise ValueError('Base64 ZIP content is not canonical padded RFC4648')
    elif storage == 'multipart':
        if bundle.get('encoded_file'):
            raise ValueError('Multipart ZIP cannot also declare an encoded file')
        if bundle.get('part_size_bytes') != PART_BYTES or not bundle.get('parts'):
            raise ValueError('Multipart ZIP requires ordered 512KiB parts')
        expected_count = (bundle['bytes'] + PART_BYTES - 1) // PART_BYTES
        if len(bundle['parts']) != expected_count:
            raise ValueError('Physical part count does not match logical ZIP size')
        pieces = []
        for index, part in enumerate(bundle['parts'], 1):
            physical = safe_path(part['path'], ('archives',))
            expected_path = f'{bundle["path"]}.{bundle["sha256"]}.part{index:04d}'
            if part['index'] != index or part['path'] != expected_path:
                raise ValueError(f'Physical part order/path mismatch: {part["path"]}')
            expected_bytes = min(PART_BYTES, bundle['bytes'] - (index - 1) * PART_BYTES)
            piece = physical.read_bytes()
            if part['bytes'] != expected_bytes or len(piece) != expected_bytes or sha(piece) != part['sha256']:
                raise ValueError(f'Physical part checksum/size mismatch: {part["path"]}')
            pieces.append(piece)
        content = b''.join(pieces)
    else:
        raise ValueError(f'Unknown archive storage: {storage}')
    if len(content) != bundle['bytes'] or sha(content) != bundle['sha256']:
        raise ValueError(f'Logical ZIP checksum/size mismatch: {bundle["path"]}')
    return content


def checked_members(bundle: dict):
    """Validate the complete ZIP inventory; yield verified file bytes only."""
    expected = {member['path']: member for member in bundle['members']}
    if len(expected) != len(bundle['members']) or bundle['member_count'] != len(expected):
        raise ValueError(f'Duplicate/mismatched manifest members: {bundle["path"]}')
    for name in expected:
        safe_path(name, ('data', 'results'))
    with zipfile.ZipFile(io.BytesIO(logical_zip_bytes(bundle))) as archive:
        if len(archive.namelist()) != len(expected) or set(archive.namelist()) != set(expected):
            raise ValueError(f'Archive member set mismatch: {bundle["path"]}')
        for name, record in expected.items():
            info = archive.getinfo(name)
            if info.is_dir() or stat.S_ISLNK(info.external_attr >> 16):
                raise ValueError(f'Archive member is not a regular file: {name}')
            content = archive.read(name)
            if len(content) != record['bytes'] or sha(content) != record['sha256']:
                raise ValueError(f'Member checksum mismatch: {name}')
            yield name, content


def restore_bundles(bundles: list[dict], *, verify_only: bool = False) -> int:
    """Preflight every selected bundle and destination before restoring anything."""
    if len({bundle['path'] for bundle in bundles}) != len(bundles):
        raise ValueError('Duplicate logical archive paths')
    seen = set()
    for bundle in bundles:
        for name, content in checked_members(bundle):
            if name in seen:
                raise ValueError(f'Member occurs in multiple bundles: {name}')
            seen.add(name)
            target = safe_path(name, ('data', 'results'))
            if not verify_only and target.exists() and (not target.is_file() or target.read_bytes() != content):
                raise ValueError(f'Existing file differs; move it aside before restoring: {target}')
    if not verify_only:
        for bundle in bundles:
            for name, content in checked_members(bundle):
                target = safe_path(name, ('data', 'results'))
                if target.exists():
                    if not target.is_file() or target.read_bytes() != content:
                        raise ValueError(f'Existing file differs; move it aside before restoring: {target}')
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                # Exclusive creation preserves local files even if another
                # process creates one after the preflight check.
                with target.open('xb') as stream:
                    stream.write(content)
    return len(seen)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', help='Restore only this selected release (all by default)')
    parser.add_argument('--verify-only', action='store_true', help='Check archives and member hashes without writing')
    args = parser.parse_args()
    manifest = json.loads((ROOT / 'archives/manifest.json').read_text())
    if manifest.get('schema_version', 1) not in (1, 2, 3):
        raise ValueError('Unsupported archive manifest schema')
    if manifest.get('schema_version') == 2 and manifest.get('physical_part_size_bytes') != PART_BYTES:
        raise ValueError('Unexpected multipart archive size policy')
    bundles = [b for b in manifest['bundles'] if not args.version or b.get('version') == args.version]
    if not bundles:
        parser.error('Version is not in the preserved dataset')
    files = restore_bundles(bundles, verify_only=args.verify_only)
    for bundle in bundles:
        print(f'{bundle["path"]}: verified {bundle["member_count"]} files', flush=True)
    print(f'Verified {files} files in {len(bundles)} archives' + ('; no files written' if args.verify_only else '; working hierarchy restored'))


if __name__ == '__main__':
    main()
