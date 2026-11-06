"""Run: python3 -m unittest discover -s tests -v

Standard-library tests need Python 3.9+. Native loader tests additionally use
Claude Code v2.1.269+ on PATH, isolated configuration and a closed loopback API endpoint.
They make zero model requests and never use the operator's settings or auth.
"""

from concurrent.futures import ThreadPoolExecutor
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'skills/style/scripts/create_preset.py'
spec = importlib.util.spec_from_file_location('create_preset', SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class PresetFixture:
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='output-fixer-tests-')
        self.addCleanup(self.temporary.cleanup)
        self.home = Path(self.temporary.name)
        self.config = self.home / 'custom config'
        self.data = {
            'name': 'My Brief',
            'description': 'Answer first',
            'instructions': '- Keep paragraphs short.\n- Explain unfamiliar terms.\n',
        }

    def create(self, **changes):
        return module.create_preset({**self.data, **changes}, self.config)

    def isolated_env(self):
        return {
            'PATH': os.environ.get('PATH', os.defpath),
            'HOME': str(self.home),
            'CLAUDE_CONFIG_DIR': str(self.config),
            'XDG_CONFIG_HOME': str(self.home / 'xdg'),
            'CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC': '1',
            'CLAUDECODE': '1',
            'ANTHROPIC_BASE_URL': 'http://127.0.0.1:1',
            'ANTHROPIC_API_KEY': 'test-placeholder',
        }


class PresetTests(PresetFixture, unittest.TestCase):
    def test_writes_only_new_preset_and_preserves_settings(self):
        self.config.mkdir()
        settings = self.config / 'settings.json'
        settings.write_bytes(b'{"permissions":{"deny":["Bash(*)"]},"outputStyle":"Learning"}\n')
        before = settings.read_bytes()
        result = self.create()
        path = Path(result['path'])
        self.assertEqual(path, self.config / 'output-styles/my-brief.md')
        self.assertEqual(result['reference'], 'My Brief')
        self.assertEqual(settings.read_bytes(), before)
        self.assertTrue(path.read_text().endswith(self.data['instructions']))
        self.assertIn('\nkeep-coding-instructions: true\n', path.read_text())
        self.assertEqual(sorted(p.relative_to(self.config).as_posix() for p in self.config.rglob('*') if p.is_file()), ['output-styles/my-brief.md', 'settings.json'])

    def test_metadata_preserves_literal_quotes_punctuation_and_unicode(self):
        name = '"Résumé: # Brief"'
        description = 'Use "one answer": # no filler; C:\\notes'
        path = Path(self.create(name=name, description=description)['path'])
        lines = path.read_text().splitlines()
        self.assertEqual(json.loads(lines[1].split(': ', 1)[1]), name)
        self.assertEqual(json.loads(lines[2].split(': ', 1)[1]), description)

    def test_replacing_coding_instructions_requires_boolean_false(self):
        path = Path(self.create(keep_coding_instructions=False)['path'])
        self.assertIn('\nkeep-coding-instructions: false\n', path.read_text())
        with self.assertRaises(ValueError):
            self.create(name='Other', keep_coding_instructions='false')

    def test_existing_file_survives_same_slug(self):
        path = Path(self.create()['path'])
        before = path.read_bytes()
        with self.assertRaises(FileExistsError):
            self.create(name='My/Brief', instructions='Replacement must not be written.')
        self.assertEqual(path.read_bytes(), before)

    def test_symlink_collision_does_not_touch_target(self):
        directory = self.config / 'output-styles'
        directory.mkdir(parents=True)
        target = self.home / 'existing.md'
        target.write_text('Existing user content\n')
        (directory / 'my-brief.md').symlink_to(target)
        with self.assertRaises(FileExistsError):
            self.create()
        self.assertEqual(target.read_text(), 'Existing user content\n')

    def test_two_simultaneous_saves_have_one_winner(self):
        def attempt(index):
            try:
                return self.create(instructions=f'- Writer {index}.\n')
            except FileExistsError:
                return None
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(attempt, range(2)))
        winners = [i for i, result in enumerate(results) if result is not None]
        self.assertEqual(len(winners), 1)
        content = Path(results[winners[0]]['path']).read_text()
        self.assertTrue(content.endswith(f'- Writer {winners[0]}.\n'))

    def test_invalid_input_does_not_create_any_files(self):
        invalid = [None, [], {}, {**self.data, 'name': ''},
                   {**self.data, 'name': 'Name\nforce-for-plugin: true'},
                   {**self.data, 'description': 'First\rSecond'},
                   {**self.data, 'instructions': '   '},
                   {**self.data, 'keep_coding_instructions': 1}]
        for data in invalid:
            with self.subTest(data=data), self.assertRaises(ValueError):
                module.create_preset(data, self.config)
        self.assertFalse(self.config.exists())

    def test_user_name_cannot_escape_directory_or_exceed_filename_limit(self):
        for name in ['../../outside', '💬', '語' * 100]:
            with self.subTest(name=name):
                path = Path(self.create(name=name)['path'])
                self.assertEqual(path.parent, self.config / 'output-styles')
                self.assertLessEqual(len(path.name.encode('utf-8')), 244)
                self.assertTrue(path.is_file())

    def test_cli_honors_custom_config_directory_without_activating_style(self):
        completed = subprocess.run([sys.executable, str(SCRIPT)],
                                   input=json.dumps(self.data), text=True,
                                   capture_output=True, env=self.isolated_env(), timeout=10)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        result = json.loads(completed.stdout)
        self.assertEqual(Path(result['path']).parent, self.config / 'output-styles')
        self.assertEqual(result['reference'], self.data['name'])
        self.assertFalse((self.config / 'settings.json').exists())
        self.assertFalse((self.home / '.claude').exists())

    def test_cli_reports_invalid_json_without_writing(self):
        completed = subprocess.run([sys.executable, str(SCRIPT)], input='{broken',
                                   text=True, capture_output=True, env=self.isolated_env(), timeout=10)
        self.assertEqual(completed.returncode, 1)
        self.assertIn('error', json.loads(completed.stderr))
        self.assertEqual(completed.stdout, '')
        self.assertFalse(self.config.exists())

    def test_cli_uses_user_home_without_config_override(self):
        env = self.isolated_env()
        del env['CLAUDE_CONFIG_DIR']
        completed = subprocess.run([sys.executable, str(SCRIPT)],
                                   input=json.dumps(self.data), text=True,
                                   capture_output=True, env=env, timeout=10)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        path = Path(json.loads(completed.stdout)['path'])
        self.assertEqual(path.parent, self.home / '.claude/output-styles')
        self.assertFalse(self.config.exists())


@unittest.skipUnless(shutil.which('claude'), 'Claude Code CLI is not installed')
class NativeLoaderTests(PresetFixture, unittest.TestCase):
    def test_generated_metadata_is_loaded_with_exact_names_and_descriptions(self):
        cases = [
            ('"Quoted Brief"', 'Preserve "quotes" and C:\\notes'),
            ('Research: Deep Dive', 'Answer: explain # tradeoffs'),
            ('true', 'null'),
            ('Résumé 短い', 'Plain language — fewer words'),
        ]
        for name, description in cases:
            self.create(name=name, description=description)
        project = self.home / 'project'
        project.mkdir()
        (project / '.git').mkdir()
        self.config.mkdir(exist_ok=True)
        settings = self.config / 'settings.json'
        settings.write_text('{"outputStyle":"Learning","permissions":{"deny":["Bash(*)"]}}\n')
        before = settings.read_bytes()
        completed = subprocess.run([
            'claude', '--print', '--no-session-persistence', '--output-format', 'json',
            '--plugin-dir', str(ROOT), '/output-style', '--strict-mcp-config',
            '--mcp-config', '{"mcpServers":{}}', '--tools', '',
        ], env=self.isolated_env(), cwd=project, capture_output=True, text=True, timeout=30)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        result = json.loads(completed.stdout)
        self.assertFalse(result['is_error'], result)
        self.assertEqual(result['local_command'], 'output_style')
        for name, description in cases:
            self.assertIn(f'\n- {name}: {description}\n', result['result'])
        self.assertEqual(result['num_turns'], 0)
        self.assertEqual(result['duration_api_ms'], 0)
        self.assertEqual(result['total_cost_usd'], 0)
        self.assertEqual(result['usage']['input_tokens'], 0)
        self.assertEqual(result['usage']['output_tokens'], 0)
        self.assertEqual(settings.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
