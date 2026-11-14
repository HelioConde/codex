import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from proxy_ai import ProxyClient, ProxyError
from proxy_ai.tasks import TaskPolicy, TaskRunner


class TaskTests(unittest.TestCase):
    def test_no_authorization_no_request(self):
        runner = TaskRunner(ProxyClient('https://proxy.example.com', 'k' * 32))
        with patch.object(runner.client, 'text', side_effect=AssertionError('paid')):
            with self.assertRaisesRegex(ProxyError, 'execute'):
                runner.text('Resumo')

    def test_policy_routing_limits_and_private_metrics(self):
        client = ProxyClient('https://proxy.example.com', 'k' * 32)
        with tempfile.TemporaryDirectory() as tmp:
            metrics = Path(tmp) / 'usage.jsonl'
            runner = TaskRunner(client, policy=TaskPolicy(max_calls=1, max_output_tokens=32), metrics=metrics)
            with patch.object(client, 'text', return_value=('resposta privada', {'input_tokens': 8, 'output_tokens': 2})) as text:
                result, usage = runner.text('prompt privado', tier='simple', execute=True)
                runner.approve(1)
                self.assertEqual(result, 'resposta privada')
                self.assertEqual(text.call_args.kwargs['model'], 'gpt-6-luna')
                self.assertEqual(text.call_args.kwargs['max_output_tokens'], 32)
                with self.assertRaises(ProxyError):
                    runner.text('segunda', execute=True)
                self.assertEqual(text.call_count, 1)
            records = [json.loads(line) for line in metrics.read_text().splitlines()]
            self.assertEqual(records[1]['usage']['input_tokens'], 8)
            self.assertEqual(records[2]['result'], 'approved')
            self.assertNotIn('usage', records[2])
            self.assertNotIn('privad', metrics.read_text())
            self.assertNotIn('k' * 32, metrics.read_text())

    def test_budget_and_missing_usage_stop_future_calls(self):
        for usage in ({'input_tokens': 10, 'output_tokens': 2}, {}):
            with self.subTest(usage=usage):
                client = ProxyClient('https://proxy.example.com', 'k' * 32)
                runner = TaskRunner(client, policy=TaskPolicy(max_calls=3, token_budget=10))
                with patch.object(client, 'text', return_value=('ok', usage)) as text:
                    runner.text('primeira', execute=True)
                    with self.assertRaises(ProxyError):
                        runner.text('segunda', execute=True)
                    self.assertEqual(text.call_count, 1)

    def test_error_consumes_attempt_without_retry_or_secret(self):
        client = ProxyClient('https://proxy.example.com', 'k' * 32)
        runner = TaskRunner(client)
        with patch.object(client, 'text', side_effect=ProxyError('HTTP 429')) as text:
            with self.assertRaises(ProxyError):
                runner.text('primeira', execute=True)
            with self.assertRaises(ProxyError):
                runner.text('segunda', execute=True)
            self.assertEqual(text.call_count, 1)

    def test_invalid_limits_and_prompt_fail_before_request(self):
        for kwargs in ({'max_calls': 0}, {'max_concurrency': 0}, {'token_budget': -1}, {'max_output_tokens': True}):
            with self.assertRaises(ProxyError):
                TaskPolicy(**kwargs)
        client = ProxyClient('https://proxy.example.com', 'k' * 32)
        runner = TaskRunner(client, policy=TaskPolicy(max_input_chars=5))
        with patch.object(client, 'text', side_effect=AssertionError('paid')):
            with self.assertRaises(ProxyError):
                runner.text('grande demais', execute=True)

    def test_output_token_cap_sent_to_responses(self):
        client = ProxyClient('https://proxy.example.com', 'k' * 32)
        with patch.object(client, '_json', return_value={'output_text': 'ok'}) as request:
            client.text('Teste', max_output_tokens=32)
        self.assertEqual(request.call_args.args[1]['max_output_tokens'], 32)


if __name__ == '__main__':
    unittest.main()
