"""Native recovery state machine; disposable fixture releases, no model calls.

Run with the other tests: python3 -m unittest discover -s tests -v
Claude Code v2.1.269+ is optional. No Git checkout or external marketplace is
needed: the update and rollback operate on a temporary local marketplace.
"""

import json
from pathlib import Path
import shutil
import subprocess
import sys
import unittest

from test_create_preset import PresetFixture, ROOT


@unittest.skipUnless(shutil.which('claude'), 'Claude Code CLI is not installed')
class NativeRecoveryTests(PresetFixture, unittest.TestCase):
    def command(self, *args, stdin=None, expected=0):
        completed = subprocess.run(
            args, input=stdin, env=self.isolated_env(), cwd=self.project,
            capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(completed.returncode, expected, completed.stderr)
        return completed

    def catalog(self):
        result = json.loads(self.command(
            'claude', '--print', '--no-session-persistence', '--output-format', 'json',
            '/output-style', '--strict-mcp-config', '--mcp-config',
            '{"mcpServers":{}}', '--tools', '',
        ).stdout)
        self.assertFalse(result['is_error'], result)
        for key in ('num_turns', 'duration_api_ms', 'total_cost_usd'):
            self.assertEqual(result[key], 0, result)
        for key in ('input_tokens', 'output_tokens'):
            self.assertEqual(result['usage'][key], 0, result)
        # Hosts may annotate the selected catalog entry with '(current)'.
        return '\n'.join(line.replace(' (current):', ':')
                         for line in result['result'].split('\n'))

    def installed_version(self, expected):
        plugins = json.loads(self.command('claude', 'plugin', 'list', '--json').stdout)
        self.assertTrue(any(p['id'] == 'lej-output-fixer@lej' and p['version'] == expected
                            for p in plugins), plugins)

    def test_delayed_retry_and_deleted_selection_survive_update_and_rollback(self):
        self.project = self.home / 'project'
        self.project.mkdir()
        (self.project / '.git').mkdir()
        market = self.home / 'market'
        market.mkdir()
        for directory in ('.claude-plugin', 'skills', 'output-styles'):
            shutil.copytree(ROOT / directory, market / directory,
                            ignore=shutil.ignore_patterns('__pycache__'))
        manifest = market / '.claude-plugin/plugin.json'
        original_manifest = manifest.read_bytes()
        original_version = json.loads(original_manifest)['version']
        # Two fixture releases of this source exercise the real plugin manager
        # without embedding a stale historical implementation in the test suite.
        next_manifest = json.loads(original_manifest)
        major, minor, patch = map(int, original_version.split('.'))
        next_manifest['version'] = f'{major}.{minor}.{patch + 1}'
        self.command('claude', 'plugin', 'marketplace', 'add', str(market), '--json')
        self.command('claude', 'plugin', 'install', 'lej-output-fixer@lej', '--json')
        self.installed_version(original_version)

        user = self.config / 'settings.json'
        shared = self.project / '.claude/settings.json'
        local = self.project / '.claude/settings.local.json'
        shared.parent.mkdir(exist_ok=True)
        for path, style in ((user, 'Learning'), (shared, 'Explanatory'), (local, 'Owned Brief')):
            value = json.loads(path.read_text()) if path.exists() else {}
            value.update(outputStyle=style, env={'RECOVERY_SENTINEL': path.name})
            path.write_text(json.dumps(value))
        decoy = self.home / '.claude/settings.json'
        decoy.parent.mkdir()
        decoy.write_text('{"outputStyle":"Concise","env":{"DECOY":"untouched"}}')

        payload = {**self.data, 'name': 'Owned Brief', 'description': 'Original approved body'}
        saver = market / 'skills/style/scripts/create_preset.py'
        def save(data, expected=0):
            return self.command(sys.executable, str(saver), stdin=json.dumps(data), expected=expected)
        original = Path(json.loads(save(payload).stdout)['path'])
        renamed = original.with_name('renamed-owned.md')
        original.rename(renamed)
        renamed_bytes = renamed.read_bytes()
        self.assertIn('\n- Owned Brief: Original approved body\n', self.catalog())

        # A later save owns the vacated filename. An old delayed retry must
        # neither overwrite that successor nor alter the renamed original.
        successor = {**payload, 'name': 'Owned/Brief', 'description': 'New approved body',
                     'instructions': 'Keep the newer instructions.'}
        self.assertEqual(Path(json.loads(save(successor).stdout)['path']), original)
        successor_bytes = original.read_bytes()
        failure = save(payload, expected=1)
        self.assertEqual(failure.stdout, '')
        self.assertIn('error', json.loads(failure.stderr))
        self.assertEqual(original.read_bytes(), successor_bytes)
        self.assertEqual(renamed.read_bytes(), renamed_bytes)

        # Deleting a selected style leaves a stale preference. A later edit to
        # another settings key is newer user data, not a snapshot to roll back.
        renamed.unlink()
        value = json.loads(user.read_text())
        value['env']['ADDED_AFTER_DELETE'] = 'preserve this edit'
        user.write_text(json.dumps(value))
        expected_settings = {p: json.loads(p.read_text()) for p in (user, shared, local, decoy)}
        def assert_state():
            for path, expected in expected_settings.items():
                self.assertEqual(json.loads(path.read_text()), expected)
            self.assertFalse(renamed.exists())
            self.assertEqual(original.read_bytes(), successor_bytes)
            text = self.catalog()
            self.assertIn('Output style: Owned Brief', text)
            self.assertNotIn('\n- Owned Brief:', text)
            self.assertIn('\n- Owned/Brief: New approved body\n', text)
            self.assertIn('\n- lej-output-fixer:Scannable:', text)
            # Discovery itself must also preserve every setting.
            for path, expected in expected_settings.items():
                self.assertEqual(json.loads(path.read_text()), expected)
        assert_state()
        manifest.write_text(json.dumps(next_manifest))
        self.command('claude', 'plugin', 'update', 'lej-output-fixer@lej', '--json')
        self.installed_version(next_manifest['version'])
        assert_state()
        # Repeating the update is an idempotent successful control.
        self.command('claude', 'plugin', 'update', 'lej-output-fixer@lej', '--json')
        self.installed_version(next_manifest['version'])
        assert_state()
        self.command('claude', 'plugin', 'uninstall', 'lej-output-fixer@lej', '--json')
        manifest.write_bytes(original_manifest)
        self.command('claude', 'plugin', 'install', 'lej-output-fixer@lej', '--json')
        self.installed_version(original_version)
        assert_state()

        # Only explicit fixture deletion frees the successor's filename for a
        # retry. Restoring it uses the frontmatter reference, not its old name.
        original.unlink()
        restored = Path(json.loads(save(payload).stdout)['path'])
        self.assertEqual(restored.read_bytes(), renamed_bytes)
        self.assertIn('\n- Owned Brief: Original approved body\n', self.catalog())
        for path, expected in expected_settings.items():
            self.assertEqual(json.loads(path.read_text()), expected)


if __name__ == '__main__':
    unittest.main()
