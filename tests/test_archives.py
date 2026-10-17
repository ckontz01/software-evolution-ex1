"""Round trips and failure boundaries for encoded and legacy evidence archives."""
import base64
from copy import deepcopy
import hashlib
import importlib.util
import io
from pathlib import Path
import random
import shutil
import tempfile
import unittest
from unittest.mock import patch
import zipfile


REPOSITORY = Path(__file__).resolve().parents[1]


def script(name):
    spec = importlib.util.spec_from_file_location(name, REPOSITORY / 'scripts' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


packager = script('package_data')
unpacker = script('unpack_data')


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.patches = [patch.object(module, 'ROOT', self.root) for module in (packager, unpacker)]
        for context in self.patches:
            context.start()
            self.addCleanup(context.stop)
        self.contents = {
            'data/raw/demo/a.bin': random.Random(484).randbytes(packager.PART_BYTES * 2 + 137),
            'results/versions/demo/b.txt': b'Complete evidence; preserved newlines.\r\n',
        }
        for name, content in self.contents.items():
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)

    def bundle(self, multipart=True):
        return packager.pack('versions/guava-10.0.zip', [self.root / n for n in self.contents], multipart=multipart)

    def clear_sources(self):
        for name in ('data', 'results'):
            if (self.root / name).exists():
                shutil.rmtree(self.root / name)

    def assert_no_restoration(self):
        self.assertFalse((self.root / 'data').exists())
        self.assertFalse((self.root / 'results').exists())

    def test_deterministic_multipart_round_trip_and_standard_zip_bytes(self):
        bundle = self.bundle()
        self.assertEqual(bundle, self.bundle())
        self.assertGreaterEqual(len(bundle['parts']), 3)
        self.assertTrue(all(p['bytes'] == 512 * 1024 for p in bundle['parts'][:-1]))
        self.assertFalse((self.root / bundle['path']).exists())
        content = unpacker.logical_zip_bytes(bundle)
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            self.assertEqual({n: archive.read(n) for n in archive.namelist()}, self.contents)
        self.clear_sources()
        self.assertEqual(unpacker.restore_bundles([bundle]), 2)

        self.assertEqual({n: (self.root / n).read_bytes() for n in self.contents}, self.contents)
        self.assertEqual(unpacker.restore_bundles([bundle]), 2)

    def test_default_base64_round_trip_preserves_exact_standard_zip(self):
        bundle = self.bundle(multipart=None)
        self.assertEqual(bundle['storage'], 'base64')
        self.assertEqual(bundle, self.bundle(multipart=None))
        encoded = bundle['encoded_file']
        stored = (self.root / encoded['path']).read_bytes()
        self.assertEqual(encoded['path'], bundle['path'] + '.b64')
        self.assertEqual(encoded['text_encoding'], 'ascii')
        self.assertEqual(stored.decode('ascii').encode('utf-8'), stored)
        self.assertEqual(hashlib.sha256(stored).hexdigest(), encoded['sha256'])
        self.assertEqual(encoded['bytes'], 4 * ((bundle['bytes'] + 2) // 3))
        legacy = self.bundle(multipart=True)
        content = unpacker.logical_zip_bytes(bundle)
        self.assertEqual(base64.b64decode(stored, validate=True), content)
        self.assertEqual(content, unpacker.logical_zip_bytes(legacy))
        self.assertFalse((self.root / bundle['path']).exists())
        self.clear_sources()
        self.assertEqual(unpacker.restore_bundles([bundle]), 2)
        self.assertEqual({n: (self.root / n).read_bytes() for n in self.contents}, self.contents)
        self.assertEqual(unpacker.restore_bundles([bundle]), 2)

    def test_missing_encoded_file_does_not_restore_any_member(self):
        bundle = self.bundle(multipart=None)
        (self.root / bundle['encoded_file']['path']).unlink()
        self.clear_sources()
        with self.assertRaises(FileNotFoundError):
            unpacker.restore_bundles([bundle])
        self.assert_no_restoration()

    def test_encoded_checksum_detects_corrupted_text_before_restoration(self):
        bundle = self.bundle(multipart=None)
        physical = self.root / bundle['encoded_file']['path']
        encoded = bytearray(physical.read_bytes())
        encoded[0] = ord('A') if encoded[0] != ord('A') else ord('B')
        physical.write_bytes(encoded)
        self.clear_sources()
        with self.assertRaisesRegex(ValueError, 'Encoded ZIP checksum'):
            unpacker.restore_bundles([bundle])
        self.assert_no_restoration()

    def test_decoded_zip_hash_is_checked_when_encoded_hash_matches(self):
        bundle = self.bundle(multipart=None)
        physical = self.root / bundle['encoded_file']['path']
        content = bytearray(unpacker.logical_zip_bytes(bundle))
        content[-1] ^= 1
        encoded = base64.b64encode(content)
        physical.write_bytes(encoded)
        bundle['encoded_file']['sha256'] = hashlib.sha256(encoded).hexdigest()
        self.clear_sources()
        with self.assertRaisesRegex(ValueError, 'Logical ZIP checksum'):
            unpacker.restore_bundles([bundle])
        self.assert_no_restoration()

    def test_strict_base64_rejects_whitespace_and_noncanonical_padding(self):
        original = packager.pack('versions/guava-empty.zip', [])
        physical = self.root / original['encoded_file']['path']
        original_encoded = physical.read_bytes()
        self.assertTrue(original_encoded.endswith(b'=='))
        self.clear_sources()
        alphabet = b'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
        for mutation, message in [('whitespace', 'strict base64'), ('padding_bits', 'not canonical')]:
            with self.subTest(mutation=mutation):
                bundle = deepcopy(original)
                encoded = bytearray(original_encoded)
                if mutation == 'whitespace':
                    encoded[0] = ord(' ')
                else:
                    encoded[-3] = alphabet[alphabet.index(encoded[-3]) + 1]
                physical.write_bytes(encoded)
                bundle['encoded_file']['sha256'] = hashlib.sha256(encoded).hexdigest()
                with self.assertRaisesRegex(ValueError, message):
                    unpacker.restore_bundles([bundle])
                self.assert_no_restoration()

    def test_unsafe_encoded_file_paths_and_symlinks_are_rejected(self):
        original = self.bundle(multipart=None)
        self.clear_sources()
        for name in ('archives/../outside.b64', '/tmp/outside.b64', 'archives/wrong.zip.b64'):
            with self.subTest(path=name):
                bundle = deepcopy(original)
                bundle['encoded_file']['path'] = name
                with self.assertRaises(ValueError):
                    unpacker.restore_bundles([bundle])
                self.assert_no_restoration()
        physical = self.root / original['encoded_file']['path']
        elsewhere = self.root / 'elsewhere.b64'
        physical.replace(elsewhere)
        physical.symlink_to(elsewhere)
        with self.assertRaisesRegex(ValueError, 'Symlink'):
            unpacker.restore_bundles([original])
        self.assert_no_restoration()

    def test_base64_cleanup_preserves_new_storage_and_removes_old_parts(self):
        old = self.bundle(multipart=True)
        new = self.bundle(multipart=None)
        self.assertEqual(old['sha256'], new['sha256'])
        self.assertEqual(unpacker.logical_zip_bytes(old), unpacker.logical_zip_bytes(new))
        packager.remove_superseded_storage([new])
        self.assertTrue((self.root / new['encoded_file']['path']).is_file())
        self.assertTrue(all(not (self.root / p['path']).exists() for p in old['parts']))
        self.assertEqual(unpacker.restore_bundles([new], verify_only=True), 2)

    def test_legacy_whole_zip_and_unchanged_whole_file(self):
        bundle = self.bundle(multipart=False)
        original = (self.root / bundle['path']).stat().st_mtime_ns
        self.assertEqual(bundle, self.bundle(multipart=False))
        self.assertEqual((self.root / bundle['path']).stat().st_mtime_ns, original)
        del bundle['storage']
        self.clear_sources()
        self.assertEqual(unpacker.restore_bundles([bundle]), 2)
        self.assertEqual((self.root / next(iter(self.contents))).read_bytes(), next(iter(self.contents.values())))

    def test_missing_part_does_not_restore_any_file(self):
        bundle = self.bundle()
        (self.root / bundle['parts'][-1]['path']).unlink()
        self.clear_sources()
        with self.assertRaises(FileNotFoundError):
            unpacker.restore_bundles([bundle])
        self.assert_no_restoration()

    def test_corrupted_part_does_not_restore_any_file(self):
        bundle = self.bundle()
        path = self.root / bundle['parts'][-1]['path']
        content = bytearray(path.read_bytes())
        content[-1] ^= 1
        path.write_bytes(content)
        self.clear_sources()
        with self.assertRaisesRegex(ValueError, 'Physical part checksum'):
            unpacker.restore_bundles([bundle])
        self.assert_no_restoration()

    def test_reordered_parts_and_incorrect_declared_size_are_rejected(self):
        original = self.bundle()
        self.clear_sources()
        for mutation in ('order', 'size'):
            with self.subTest(mutation=mutation):
                bundle = deepcopy(original)
                if mutation == 'order':
                    bundle['parts'].reverse()
                else:
                    bundle['parts'][0]['bytes'] -= 1
                with self.assertRaises(ValueError):
                    unpacker.restore_bundles([bundle])
                self.assert_no_restoration()

    def test_whole_zip_hash_is_checked_even_when_part_hashes_match(self):
        bundle = self.bundle()
        part = bundle['parts'][-1]
        path = self.root / part['path']
        content = bytearray(path.read_bytes())
        content[-1] ^= 1
        path.write_bytes(content)
        part['sha256'] = hashlib.sha256(content).hexdigest()
        self.clear_sources()
        with self.assertRaisesRegex(ValueError, 'Logical ZIP checksum'):
            unpacker.restore_bundles([bundle])
        self.assert_no_restoration()

    def test_late_member_corruption_is_detected_before_earlier_member_write(self):
        bundle = self.bundle()
        bundle['members'][-1]['sha256'] = '0' * 64
        self.clear_sources()
        with self.assertRaisesRegex(ValueError, 'Member checksum'):
            unpacker.restore_bundles([bundle])
        self.assert_no_restoration()

    def test_differing_local_file_blocks_all_restoration(self):
        bundle = self.bundle()
        self.clear_sources()
        conflict = self.root / 'results/versions/demo/b.txt'
        conflict.parent.mkdir(parents=True)
        conflict.write_bytes(b'My local changes')
        with self.assertRaisesRegex(ValueError, 'Existing file differs'):
            unpacker.restore_bundles([bundle])
        self.assertFalse((self.root / 'data').exists())
        self.assertEqual(conflict.read_bytes(), b'My local changes')

    def test_verify_only_writes_nothing(self):
        bundle = self.bundle()
        self.clear_sources()
        self.assertEqual(unpacker.restore_bundles([bundle], verify_only=True), 2)
        self.assert_no_restoration()

    def test_unsafe_logical_part_and_member_paths_are_rejected(self):
        original = self.bundle()
        self.clear_sources()
        for kind, value in [('logical', 'archives/../outside.zip'),
                            ('part', '/tmp/outside.part'),
                            ('member', 'data/../../outside'),
                            ('member', 'data\\outside'),
                            ('member', 'data//outside'),
                            ('member', 'data')]:
            with self.subTest(kind=kind, value=value):
                bundle = deepcopy(original)
                if kind == 'logical':
                    bundle['path'] = value
                elif kind == 'part':
                    bundle['parts'][0]['path'] = value
                else:
                    bundle['members'][0]['path'] = value
                with self.assertRaises(ValueError):
                    unpacker.restore_bundles([bundle])
                self.assert_no_restoration()

    def test_symlink_destination_is_rejected(self):
        bundle = self.bundle()
        self.clear_sources()
        (self.root / 'elsewhere').mkdir()
        (self.root / 'data').symlink_to(self.root / 'elsewhere', target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'Symlink'):
            unpacker.restore_bundles([bundle])
        self.assertEqual(list((self.root / 'elsewhere').iterdir()), [])

    def test_obsolete_detection_includes_numbered_parts(self):
        self.bundle()
        obsolete = self.root / ('archives/versions/guava-9.0.zip.' + 'a' * 64 + '.part0001')
        obsolete.write_bytes(b'old generation')
        encoded = self.root / 'archives/versions/guava-9.1.zip.b64'
        encoded.write_bytes(b'old encoded release')
        self.assertEqual(packager.obsolete_bundles({'guava-10.0.zip'}), sorted([obsolete.name, encoded.name]))

    def test_old_generation_survives_until_manifest_switch(self):
        old = self.bundle()
        first = self.root / next(iter(self.contents))
        first.write_bytes(b'New evidence')
        new = self.bundle()
        self.assertNotEqual(old['sha256'], new['sha256'])
        self.assertEqual(unpacker.restore_bundles([old], verify_only=True), 2)
        packager.remove_superseded_storage([new])
        self.assertTrue(all((self.root / p['path']).is_file() for p in new['parts']))
        self.assertTrue(all(not (self.root / p['path']).exists() for p in old['parts']))


if __name__ == '__main__':
    unittest.main()
