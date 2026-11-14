import io
import json
import subprocess
import unittest
from unittest.mock import patch

from scripts import smoke_codex_proxy


class SmokeTests(unittest.TestCase):
    def test_selected_ultra_reaches_smoke_cli_and_report(self):
        class Client:
            base_url = 'http://127.0.0.1:8080'
            _api_key = 'offline-key'
            def health(self): return {'status': 'ok'}
            def models(self): return ['gpt-6-astra']
        events = [{'type': 'item.completed', 'item': {'type': 'agent_message',
                   'text': 'def soma(a, b):\n    return a + b'}},
                  {'type': 'turn.completed', 'usage': {'input_tokens': 1, 'output_tokens': 1}}]
        response = subprocess.CompletedProcess([], 0, '\n'.join(map(json.dumps, events)).encode(), b'')
        with patch.object(smoke_codex_proxy, 'check_cli', return_value='codex-cli 0.166.0'), \
             patch.object(smoke_codex_proxy, 'load_client', return_value=Client()), \
             patch('subprocess.run', return_value=response) as run, \
             patch('sys.stdout', new_callable=io.StringIO) as output:
            self.assertEqual(smoke_codex_proxy.main(['--task', 'ultra', '--execute']), 0)
        command = run.call_args.args[0]
        self.assertIn('vf_ultra', command)
        self.assertNotIn('model_reasoning_effort="low"', command)
        self.assertEqual(json.loads(output.getvalue())['effort'], 'ultra')

    def test_smoke_requires_authorization_before_any_subprocess(self):
        with patch('subprocess.run', side_effect=AssertionError('external call')):
            with patch('sys.stdout', new_callable=io.StringIO):
                self.assertEqual(smoke_codex_proxy.main([]), 0)

    def test_generated_code_is_validated_without_execution(self):
        self.assertTrue(smoke_codex_proxy.valid_sum('def soma(a, b):\n    return a + b'))
        for code in ('import os\ndef soma(a,b): return a+b',
                     'def soma(a,b): return a-b', 'def soma(a,b): return eval(a)',
                     '@dangerous\ndef soma(a,b): return a+b'):
            self.assertFalse(smoke_codex_proxy.valid_sum(code))
