import hashlib
import io
import json
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import prepare_pr1061
import check_pr1061


class PreparationTests(unittest.TestCase):
    def test_clean_setup_recreates_records_from_cached_archive(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            cache = folder / 'cache'
            cache.mkdir()
            archive = cache / 'core.tar.gz'
            with tarfile.open(archive, 'w:gz') as packed:
                member = tarfile.TarInfo('source/reviewed.py')
                member.size = 6
                packed.addfile(member, io.BytesIO(b'pinned'))
            digest = hashlib.sha256(archive.read_bytes()).hexdigest()
            with mock.patch.dict(prepare_pr1061.SOURCES, {'core': ('owner/repo', 'revision', digest)}, clear=True):
                build = folder / 'build'
                records = prepare_pr1061.prepare(build, cache)
                self.assertEqual((build / 'core/reviewed.py').read_bytes(), b'pinned')
                self.assertEqual(json.loads((build / 'core-source.json').read_text()), records['core_archive'])
                (build / 'core-source.json').unlink()
                prepare_pr1061.prepare(build)
                self.assertTrue((build / 'core-source.json').exists())
                (build / 'core/reviewed.py').write_bytes(b'changed')
                with self.assertRaisesRegex(ValueError, 'Modified source'):
                    prepare_pr1061.prepare(build)

    def test_corrupt_archive_fails_before_extraction(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            (folder / 'core.tar.gz').write_bytes(b'corrupt')
            with self.assertRaisesRegex(ValueError, 'archive hash mismatch'):
                prepare_pr1061.prepare(folder)
            self.assertFalse((folder / 'core').exists())

    def test_unsafe_members_are_rejected(self):
        for name, kind in [('source/../../escape', tarfile.REGTYPE),
                           ('source/link', tarfile.SYMTYPE),
                           ('source/C:/escape', tarfile.REGTYPE)]:
            with self.subTest(name=name), io.BytesIO() as stream:
                with tarfile.open(fileobj=stream, mode='w') as archive:
                    member = tarfile.TarInfo(name)
                    member.type = kind
                    archive.addfile(member)
                stream.seek(0)
                with tarfile.open(fileobj=stream) as archive, self.assertRaises(ValueError):
                    prepare_pr1061.verified_members(archive)


class FeatureProbeTests(unittest.TestCase):
    def test_probe_is_executed_and_logs_replaced(self):
        data = dict.fromkeys(('prepare', 'init', 'operators', 'properties'), True)
        result = mock.Mock(returncode=0, stdout=json.dumps(data), stderr='')
        with tempfile.TemporaryDirectory() as temp, mock.patch.object(check_pr1061.subprocess, 'run', return_value=result) as run:
            output = Path(temp)
            (output / 'metaclass-probe.stdout.txt').write_text('stale')
            actual, command = check_pr1061.probe_features(Path(sys.executable), output)
            self.assertEqual(actual, data)
            self.assertEqual(json.loads((output / 'metaclass-probe.stdout.txt').read_text()), data)
            self.assertIn(check_pr1061.FEATURE_PROBE, command)
            run.assert_called_once()

    def test_false_missing_and_non_boolean_features_fail(self):
        for data in [{}, {'prepare': True},
                     dict.fromkeys(('prepare', 'init', 'operators', 'properties'), 1),
                     dict.fromkeys(('prepare', 'init', 'operators', 'properties'), False)]:
            with self.subTest(data=data), tempfile.TemporaryDirectory() as temp:
                result = mock.Mock(returncode=0, stdout=json.dumps(data), stderr='')
                with mock.patch.object(check_pr1061.subprocess, 'run', return_value=result):
                    with self.assertRaisesRegex(ValueError, 'four proposed metaclass'):
                        check_pr1061.probe_features(Path(sys.executable), Path(temp))


if __name__ == '__main__':
    unittest.main()
