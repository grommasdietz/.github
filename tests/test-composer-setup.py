"""Check that compatibility setup selects the actual runtime dependency scope."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / 'actions/setup/install-composer.sh'


class ComposerSetupTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        (self.root / 'playground').mkdir()
        self.manifest('.', {'require-dev': {'getkirby/cms': '^5.6'}})
        self.manifest('playground', {'require': {'getkirby/cms': '^5.6'}})
        binary = self.root / 'bin'
        binary.mkdir()
        composer = binary / 'composer'
        composer.write_text('#!' + shutil.which('python3') + '\n' + '''import json, pathlib, sys
args = sys.argv[1:]
directory = pathlib.Path(args.pop(0).split('=', 1)[1])
manifest = json.loads((directory / 'composer.json').read_text())
operation = args.pop(0)
if operation == 'config': sys.exit(0)
if operation == 'require':
    requirement = next(arg.split(':', 1)[1] for arg in args if arg.startswith('getkirby/cms:'))
    expected = 'require-dev' if '--dev' in args else 'require'
    assert 'getkirby/cms' in manifest.get(expected, {})
elif operation == 'install':
    requirement = manifest.get('require', {}).get('getkirby/cms', manifest.get('require-dev', {}).get('getkirby/cms', 'none'))
else: raise AssertionError(operation)
(directory / 'installed-kirby').write_text(requirement)
''')
        composer.chmod(0o700)
        self.environment = dict(os.environ, PATH=str(binary) + os.pathsep + os.environ['PATH'],
                                GITHUB_ENV=str(self.root / 'environment'), KIRBY='6.0.0-rc.3')

    def manifest(self, directory, value):
        (self.root / directory / 'composer.json').write_text(json.dumps(value))

    def run_setup(self, scope='all', version='6.0.0-rc.3'):
        return subprocess.run(['bash', str(SCRIPT)], cwd=str(self.root),
                              env=dict(self.environment, SCOPE=scope, KIRBY=version),
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

    def test_requested_version_reaches_both_existing_runtime_scopes(self):
        result = self.run_setup()
        self.assertEqual(result.returncode, 0, result.stderr)
        for directory in ['.', 'playground']:
            self.assertEqual((self.root / directory / 'installed-kirby').read_text(), '6.0.0-rc.3')
        self.assertEqual((self.root / 'environment').read_text(), 'KIRBY_TEST_MAJOR=6\n')

    def test_playground_scope_changes_the_runtime_without_installing_root_tools(self):
        self.assertEqual(self.run_setup('playground').returncode, 0)
        self.assertEqual((self.root / 'playground/installed-kirby').read_text(), '6.0.0-rc.3')
        self.assertFalse((self.root / 'installed-kirby').exists())

    def test_no_override_keeps_the_locked_manifest_constraints(self):
        self.assertEqual(self.run_setup(version='').returncode, 0)
        self.assertEqual((self.root / 'playground/installed-kirby').read_text(), '^5.6')
        self.assertFalse((self.root / 'environment').exists())

    def test_root_without_cms_does_not_acquire_an_unused_second_core(self):
        self.manifest('.', {'require-dev': {'phpunit/phpunit': '^12'}})
        self.assertEqual(self.run_setup().returncode, 0)
        self.assertEqual((self.root / 'installed-kirby').read_text(), 'none')
        self.assertEqual((self.root / 'playground/installed-kirby').read_text(), '6.0.0-rc.3')


if __name__ == '__main__':
    unittest.main()
