import io
import json
import tempfile
import tomllib
import unittest
from pathlib import Path
from unittest.mock import patch

from proxy_ai import codex_cli
from proxy_ai.client import ProxyError, normalize_base_url


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        check = patch.object(codex_cli, 'check_cli', return_value='codex-cli 0.166.0')
        check.start()
        self.addCleanup(check.stop)

    def test_local_docker_url(self):
        self.assertEqual(normalize_base_url('http://127.0.0.1:8080/v1'), 'http://127.0.0.1:8080')
        for url in ('http://192.168.1.2:8080', 'http://127.0.0.1:0', 'http://localhost:8080'):
            with self.assertRaises(ProxyError):
                normalize_base_url(url)

    def test_merge_preserves_original_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'config.toml'
            original = b'# original\r\nmodel = "gpt-6-astra"\r\nmodel_provider = "openai"\r\n[mcp_servers.example]\r\ncommand="existing"\r\n'
            path.write_bytes(original)
            backup = codex_cli.install_config(path, 'http://127.0.0.1:8080')
            self.assertEqual(backup.read_bytes(), original)
            self.assertTrue(path.read_bytes().startswith(original))
            config = tomllib.loads(path.read_text(encoding='utf-8'))
            self.assertEqual(config['model_provider'], 'openai')
            self.assertEqual(config['mcp_servers']['example']['command'], 'existing')
            profile = tomllib.loads((path.parent / 'vf_code.config.toml').read_text())
            self.assertEqual(profile['model'], 'gpt-6.1-sol')
            profile = tomllib.loads((path.parent / 'vf_critical.config.toml').read_text())
            self.assertEqual(profile['model'], 'gpt-6-astra')
            profile = tomllib.loads((path.parent / 'vf_ultra.config.toml').read_text())
            self.assertEqual(profile['model'], 'gpt-6-astra')
            self.assertEqual(profile['model_reasoning_effort'], 'ultra')
            self.assertEqual(profile['service_tier'], 'default')
            self.assertNotIn('profiles', config)
            self.assertEqual(config['model_providers']['videoforge_proxy']['request_max_retries'], 0)
            before = path.read_bytes()
            self.assertIsNone(codex_cli.install_config(path, 'http://127.0.0.1:8080'))
            self.assertEqual(path.read_bytes(), before)

    def test_collision_refuses_to_change_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'config.toml'
            original = b'[profiles.vf_code]\nmodel="custom"\n'
            path.write_bytes(original)
            with self.assertRaises(ProxyError):
                codex_cli.install_config(path, 'https://proxy.example.com')
            self.assertEqual(path.read_bytes(), original)

    def test_existing_v2_profile_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'config.toml'
            path.write_text('# original\n')
            profile = path.parent / 'vf_code.config.toml'
            profile.write_text('model="custom"\n')
            with self.assertRaises(ProxyError):
                codex_cli.install_config(path, 'https://proxy.example.com')
            self.assertEqual(path.read_text(), '# original\n')
            self.assertEqual(profile.read_text(), 'model="custom"\n')

    def test_launch_requires_execute_before_network_or_docker(self):
        with patch.object(codex_cli, 'load_client', side_effect=AssertionError('network')):
            with patch('sys.stdout', new_callable=io.StringIO):
                self.assertEqual(codex_cli.main(['run']), 0)

    def test_plan_has_no_secret_and_uses_cli_overrides(self):
        args = codex_cli.launch_args('code', 'http://127.0.0.1:8080')
        joined = ' '.join(args)
        self.assertIn('model_provider="videoforge_proxy"', joined)
        self.assertIn('model="gpt-6.1-sol"', joined)
        self.assertIn('supports_websockets=false', joined)
        self.assertIn('request_max_retries=0', joined)
        self.assertNotIn('Bearer', joined)

    def test_fallback_only_before_launch_and_opt_in(self):
        with patch.object(codex_cli, 'load_client', side_effect=ProxyError('offline')):
            with patch.object(codex_cli.subprocess, 'call', return_value=7) as run:
                with patch('sys.stderr', new_callable=io.StringIO):
                    self.assertEqual(codex_cli.main(['run', '--execute']), 2)
                    run.assert_not_called()
                    self.assertEqual(codex_cli.main(['run', '--execute', '--fallback-original']), 7)
                self.assertEqual(run.call_count, 1)

    def test_failed_session_never_falls_back_or_retries(self):
        class Client:
            base_url = 'http://127.0.0.1:8080'
            _api_key = 'k' * 32
            def health(self): return {'status': 'ok'}
            def models(self): return ['gpt-6-astra']
        with patch.object(codex_cli, 'load_client', return_value=Client()):
            with patch.object(codex_cli.subprocess, 'call', return_value=9) as run:
                self.assertEqual(codex_cli.main(['run', '--execute', '--fallback-original']), 9)
                self.assertEqual(run.call_count, 1)
                self.assertNotIn('k' * 32, ' '.join(run.call_args.args[0]))
                self.assertEqual(run.call_args.kwargs['env']['CODEX_PROXY_API_KEY'], 'k' * 32)
                self.assertIn('model="gpt-6-astra"', run.call_args.args[0])
                self.assertIn('model_reasoning_effort="ultra"', run.call_args.args[0])


if __name__ == '__main__':
    unittest.main()
