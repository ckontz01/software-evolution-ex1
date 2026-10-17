#!/usr/bin/env python3
"""Package complete raw and computed data without discarding any study evidence."""
from __future__ import annotations
import base64
import hashlib
import json
from pathlib import Path, PurePosixPath
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PART_BYTES = 512 * 1024


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def store_base64(bundle: dict, content: bytes) -> dict:
    """Store the exact logical ZIP as canonical, unwrapped ASCII base64."""
    if len(content) != bundle['bytes'] or hashlib.sha256(content).hexdigest() != bundle['sha256']:
        raise ValueError('Logical ZIP identity differs before base64 storage')
    relative = PurePosixPath(bundle['path'])
    if relative.is_absolute() or '..' in relative.parts or relative.as_posix() != bundle['path'] or relative.parts[0] != 'archives' or relative.suffix != '.zip' or '\\' in bundle['path']:
        raise ValueError(f'Invalid logical ZIP path: {bundle["path"]}')
    physical = ROOT / (bundle['path'] + '.b64')
    physical.parent.mkdir(parents=True, exist_ok=True)
    encoded = base64.b64encode(content)
    encoded_sha = hashlib.sha256(encoded).hexdigest()
    if not physical.exists() or digest(physical) != encoded_sha:
        with tempfile.NamedTemporaryFile(prefix='encoded-stage-', dir=physical.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(encoded)
        try:
            temporary.replace(physical)
        finally:
            temporary.unlink(missing_ok=True)
    record = {key: value for key, value in bundle.items()
              if key not in ('storage', 'part_size_bytes', 'parts', 'encoded_file')}
    record.update(storage='base64', encoded_file={
        'path': physical.relative_to(ROOT).as_posix(), 'bytes': len(encoded),
        'sha256': encoded_sha, 'text_encoding': 'ascii'})
    return record


def pack(name: str, paths: list[Path], *, multipart: bool | None = None) -> dict:
    relative_name = PurePosixPath(name)
    if relative_name.is_absolute() or '..' in relative_name.parts or str(relative_name) != name or '\\' in name:
        raise ValueError(f'Invalid bundle name: {name}')
    target = ROOT / 'archives' / name
    target.parent.mkdir(parents=True, exist_ok=True)
    members = []
    seen = set()
    with tempfile.TemporaryDirectory(prefix='package-stage-', dir=target.parent) as directory:
        stage = Path(directory)
        temporary = stage / 'complete.zip'
        with zipfile.ZipFile(temporary, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
            for path in sorted(paths):
                if not path.is_file() or '__pycache__' in path.parts or path.name.endswith('.part'):
                    continue
                relative = path.relative_to(ROOT).as_posix()
                if not path.resolve().is_relative_to(ROOT.resolve()) or path.is_symlink():
                    raise ValueError(f'Source is not an ordinary repository file: {path}')
                if relative in seen:
                    raise ValueError(f'Duplicate archive member: {relative}')
                seen.add(relative)
                content = path.read_bytes()
                info = zipfile.ZipInfo(relative, date_time=(2026, 10, 17, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                archive.writestr(info, content, compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)
                members.append({'path': relative, 'bytes': len(content), 'sha256': hashlib.sha256(content).hexdigest()})
        record = {'path': target.relative_to(ROOT).as_posix(), 'bytes': temporary.stat().st_size,
                  'sha256': digest(temporary), 'member_count': len(members), 'members': members}
        if multipart is False:
            record['storage'] = 'whole'
            if not target.exists() or digest(target) != record['sha256']:
                temporary.replace(target)
            return record
        if multipart is None:
            return store_base64(record, temporary.read_bytes())
        record.update({'storage': 'multipart', 'part_size_bytes': PART_BYTES, 'parts': []})
        with temporary.open('rb') as stream:
            index = 1
            while content := stream.read(PART_BYTES):
                physical = target.with_name(f'{target.name}.{record["sha256"]}.part{index:04d}')
                staged = stage / physical.name
                staged.write_bytes(content)
                part = {'index': index, 'path': physical.relative_to(ROOT).as_posix(),
                        'bytes': len(content), 'sha256': hashlib.sha256(content).hexdigest()}
                record['parts'].append(part)
                index += 1
        # All parts are complete before publishing any. Hash-qualified paths
        # preserve the previous generation until the new manifest is installed.
        for part in record['parts']:
            physical = ROOT / part['path']
            staged = stage / physical.name
            if not physical.exists() or digest(physical) != part['sha256']:
                staged.replace(physical)
        return record


def obsolete_bundles(expected_names: set[str]) -> list[str]:
    """Catch superseded whole ZIPs, numbered parts, and unfinished old ZIPs."""
    return sorted(p.name for p in (ROOT / 'archives/versions').glob('guava-*.zip*')
                  if p.name.split('.zip', 1)[0] + '.zip' not in expected_names)


def remove_superseded_storage(bundles: list[dict]) -> None:
    """Run only after the replacement manifest has been atomically installed."""
    for bundle in bundles:
        if bundle['storage'] not in ('multipart', 'base64'):
            continue
        logical = ROOT / bundle['path']
        keep = {ROOT / part['path'] for part in bundle.get('parts', [])}
        for old in logical.parent.glob(logical.name + '.*part*'):
            if old.is_file() and old not in keep:
                old.unlink()
        if logical.exists():
            logical.unlink()


def main() -> None:
    manifest = json.loads((ROOT / 'config/versions.json').read_text())
    expected_names = {f"guava-{r['version']}.zip" for r in manifest['versions']}
    obsolete = obsolete_bundles(expected_names)
    if obsolete:
        raise ValueError(f'Archive superseded release bundles before packaging the revised cohort: {obsolete}')
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
    git_archives = sorted((ROOT / 'data/upstream_git').glob('*.zip'))
    if len(git_archives) != 2:
        raise ValueError('Expected the first and last immutable Git source archives')
    bundles.append(pack('upstream_git.zip', git_archives, multipart=False))
    payload = {'schema_version': 3,
               'format': 'Logical standard ZIP/deflate; fixed timestamps; complete original file bytes; version and pilot ZIPs stored as canonical padded RFC4648 base64 ASCII without whitespace in .zip.b64 files',
               'purpose': 'All 90 pinned acquired artifacts and every finalized per-release computed file are preserved, including instructor raw output, unchanged scoped input JARs, supplementary member evidence, algorithm logs and directional MoJoFM details. The pilot bundle includes every k candidate assignment. Unfinished .part files are excluded. Unpack to restore the documented working hierarchy.',
               'version_manifest_sha256': digest(ROOT / 'config/versions.json'),
               'bundles': bundles}
    temporary_manifest = ROOT / 'archives/manifest.json.tmp'
    temporary_manifest.write_text(json.dumps(payload, indent=2) + '\n')
    temporary_manifest.replace(ROOT / 'archives/manifest.json')
    remove_superseded_storage(bundles)


if __name__ == '__main__':
    main()
