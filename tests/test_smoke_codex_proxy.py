import io
import unittest
from unittest.mock import patch

from scripts import smoke_codex_proxy


class SmokeTests(unittest.TestCase):
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
