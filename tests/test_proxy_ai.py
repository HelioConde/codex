"""Testes com mocks offline: nao usam rede nem secrets reais."""
import base64
import io
import json
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

from proxy_ai import ProxyClient, ProxyError, parse_response_text
from proxy_ai.client import _NoRedirect, _decode_image, normalize_base_url
from proxy_ai.__main__ import main


class FakeResponse:
    def __init__(self, data):
        self.data = data

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self, maximum):
        return self.data[:maximum]


class FakeOpener:
    def __init__(self, result, *, status=None):
        self.result = result
        self.status = status
        self.requests = []

    def open(self, request, timeout):
        self.requests.append((request, timeout))
        if self.status is not None:
            raise urllib.error.HTTPError(request.full_url, self.status, "PRIVATE BODY", {}, None)
        payload = json.dumps(self.result).encode("utf-8") if isinstance(self.result, dict) else self.result
        return FakeResponse(payload)


class ProxyAITests(unittest.TestCase):
    KEY = "q" * 32

    def test_url_validation(self):
        self.assertEqual(normalize_base_url("https://proxy.example.com/v1/"), "https://proxy.example.com")
        self.assertEqual(normalize_base_url("http://127.0.0.1:18080"), "http://127.0.0.1:18080")
        for url in ("http://proxy.example.com", "http://127.0.0.1",
                    "https://user:pw@proxy.example.com", "https://proxy.example.com/a",
                    "https://proxy.example.com/?q=key", "file:///etc/passwd", ""):
            with self.subTest(url=url), self.assertRaises(ProxyError):
                normalize_base_url(url)

    def test_credentials_and_restricted_routes(self):
        with self.assertRaises(ProxyError):
            ProxyClient("https://proxy.example.com", "short")
        client = ProxyClient("https://proxy.example.com", self.KEY)
        with self.assertRaises(ProxyError):
            client._json("/admin/accounts")
        self.assertIsNone(_NoRedirect().redirect_request(None, None, 302, "move", {}, "https://evil.example/"))

    def test_text_response_format(self):
        self.assertEqual(parse_response_text({"output_text": "ola"}), "ola")
        self.assertEqual(parse_response_text({"output": [
            {"type": "reasoning", "content": [{"type": "text", "text": "segredo"}]},
            {"type": "message", "content": [{"type": "output_text", "text": "Roteiro pronto"}]},
        ]}), "Roteiro pronto")
        with self.assertRaises(ProxyError):
            parse_response_text({"output": [{"type": "reasoning", "content": []}]})

    def test_text_request_headers_payload_and_usage(self):
        fake = FakeOpener({"output": [{"type": "message", "content": [
            {"type": "output_text", "text": "Uma cena."}]}],
            "usage": {"input_tokens": 12, "output_tokens": 6, "secret": "x"}})
        client = ProxyClient("https://proxy.example.com/v1", self.KEY)
        with patch("proxy_ai.client.urllib.request.build_opener", return_value=fake):
            result, usage = client.text("Crie o roteiro", instructions="seja breve", effort="low")
        self.assertEqual(result, "Uma cena.")
        self.assertEqual(usage, {"input_tokens": 12, "output_tokens": 6})
        req, timeout = fake.requests[0]
        self.assertEqual(req.full_url, "https://proxy.example.com/v1/responses")
        self.assertEqual(req.get_header("Authorization"), "Bearer " + self.KEY)
        body = json.loads(req.data)
        self.assertEqual(body["model"], "gpt-6.1-sol")
        self.assertFalse(body["stream"])
        self.assertEqual(body["input"], "Crie o roteiro")
        self.assertEqual(body["instructions"], "seja breve")
        self.assertEqual(body["reasoning"], {"effort": "low"})
        self.assertTrue(0 < timeout <= 300)

    def test_no_retry_and_redacts_http_error(self):
        fake = FakeOpener({}, status=429)
        client = ProxyClient("https://proxy.example.com", self.KEY)
        with patch("proxy_ai.client.urllib.request.build_opener", return_value=fake):
            with self.assertRaisesRegex(ProxyError, "Nao repetir automaticamente") as err:
                client.text("Teste")
        self.assertEqual(len(fake.requests), 1)
        self.assertNotIn(self.KEY, str(err.exception))
        self.assertNotIn("PRIVATE BODY", str(err.exception))

    def test_auth_and_timeout_are_sanitized_without_retry(self):
        client = ProxyClient('https://proxy.example.com', self.KEY, timeout=2)
        for status in (401, 403):
            fake = FakeOpener({}, status=status)
            with patch('proxy_ai.client.urllib.request.build_opener', return_value=fake):
                with self.assertRaisesRegex(ProxyError, 'autenticacao'):
                    client.health()
            self.assertEqual(len(fake.requests), 1)
        with patch('proxy_ai.client.urllib.request.build_opener') as factory:
            factory.return_value.open.side_effect = TimeoutError('private endpoint')
            with self.assertRaises(ProxyError) as error:
                client.health()
            self.assertNotIn('private endpoint', str(error.exception))
            self.assertEqual(factory.return_value.open.call_count, 1)

    def test_cached_tokens_are_measured_separately(self):
        client = ProxyClient('https://proxy.example.com', self.KEY)
        with patch.object(client, '_json', return_value={
            'output_text': 'ok', 'usage': {'input_tokens': 10, 'output_tokens': 2,
                                        'input_tokens_details': {'cached_tokens': 7}}}):
            _, usage = client.text('teste')
        self.assertEqual(usage['cached_input_tokens'], 7)

    def test_direct_client_does_not_misrepresent_ultra_orchestration(self):
        client = ProxyClient('https://proxy.example.com', self.KEY)
        with patch.object(client, '_json') as request:
            with self.assertRaisesRegex(ProxyError, 'Codex CLI'):
                client.text('teste', model='gpt-6-astra', effort='ultra')
        request.assert_not_called()

    def test_health_and_models(self):
        client = ProxyClient("https://proxy.example.com", self.KEY)
        a = FakeOpener({"status": "ok", "accounts": 2})
        b = FakeOpener({"data": [{"id": "gpt-6.1-sol"}, {"id": "gpt-6-astra"}]})
        with patch("proxy_ai.client.urllib.request.build_opener", return_value=a):
            self.assertEqual(client.health(), {"status": "ok", "accounts_configured": 2})
        with patch("proxy_ai.client.urllib.request.build_opener", return_value=b):
            self.assertEqual(client.models(), ["gpt-6-astra", "gpt-6.1-sol"])

    def test_no_account_health_is_rejected(self):
        client = ProxyClient("https://proxy.example.com", self.KEY)
        with patch("proxy_ai.client.urllib.request.build_opener", return_value=FakeOpener({"status": "ok", "accounts": 0})):
            with self.assertRaises(ProxyError):
                client.health()

    def test_prevent_paid_call_when_output_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "resposta.txt"
            dest.write_text("existente", encoding="utf-8")
            with patch("proxy_ai.__main__.ProxyClient.from_env", side_effect=AssertionError("network")):
                with patch("sys.stderr", new_callable=io.StringIO) as err:
                    rc = main(["text", "--prompt-file", "missing", "--output", str(dest), "--execute"])
            self.assertEqual(rc, 2)
            self.assertIn("nao chamar a IA", err.getvalue())

    def test_dry_run_not_even_create_client(self):
        with patch("proxy_ai.__main__.ProxyClient.from_env", side_effect=AssertionError("network")):
            with patch("sys.stdout", new_callable=io.StringIO) as out:
                self.assertEqual(main(["text", "--prompt-file", "does-not-exist"]), 0)
                self.assertIn("--execute", out.getvalue())
            with patch("sys.stdout", new_callable=io.StringIO) as out:
                self.assertEqual(main(["image", "--prompt-file", "missing", "--output", "out.png"]), 0)
                self.assertIn("--execute", out.getvalue())

    def test_image_decode_and_safe_write(self):
        raw = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64 + b"IEND\xaeB\x60\x82"
        self.assertEqual(_decode_image({"data": [{"b64_json": base64.b64encode(raw).decode()}]})[1], ".png")
        client = ProxyClient("https://proxy.example.com", self.KEY)
        fake = FakeOpener({"data": [{"b64_json": base64.b64encode(raw).decode()}]})
        with tempfile.TemporaryDirectory() as folder, patch("proxy_ai.client.urllib.request.build_opener", return_value=fake):
            out = Path(folder) / "scene.png"
            info = client.image("Uma cidade fantastica original", out)
            self.assertTrue(out.is_file())
            self.assertEqual(info["bytes"], len(raw))
            with self.assertRaises(ProxyError):
                client.image("Uma cidade fantastica original", out)
        self.assertEqual(len(fake.requests), 1)

    def test_image_remote_url_rejected(self):
        with self.assertRaisesRegex(ProxyError, "URL remota"):
            _decode_image({"data": [{"url": "https://unsafe.example/image.png"}]})


if __name__ == "__main__":
    unittest.main()
