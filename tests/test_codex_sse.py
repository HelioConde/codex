"""Teste opcional da CLI instalada contra servidor SSE inteiramente simulado."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import unittest

from proxy_ai.codex_cli import install_config, launch_args


@unittest.skipUnless(shutil.which('codex'), 'CLI Codex opcional nao instalada no CI')
class CodexSSETests(unittest.TestCase):
    def test_real_cli_accepts_v2_profile_and_mock_stream(self):
        self.exercise_cli(200)

    def test_real_cli_never_retries_429(self):
        self.exercise_cli(429)

    def test_real_cli_never_retries_auth_failure(self):
        self.exercise_cli(401)

    def test_real_cli_resolves_astra_ultra_using_native_catalog(self):
        self.exercise_cli(200, tier='ultra')

    def exercise_cli(self, status, tier='code'):
        requests = []
        model = 'gpt-6-astra' if tier == 'ultra' else 'gpt-6.1-sol'
        # CLI 0.166.0: Ultra resolves to Astra.multi_agent_reasoning_effort=xhigh.
        effort = 'xhigh' if tier == 'ultra' else 'medium'

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args): pass

            def do_GET(self):
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"models":[],"data":[]}')

            def do_POST(self):
                body = self.rfile.read(int(self.headers['Content-Length']))
                requests.append((self.path, self.headers.get('Authorization'), json.loads(body)))
                if status != 200:
                    self.send_response(status)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(b'{"error":{"message":"simulated failure","type":"test"}}')
                    return
                message = {'id': 'msg_mock', 'type': 'message', 'role': 'assistant',
                           'status': 'completed', 'content': [{'type': 'output_text', 'text': 'MOCK_OK', 'annotations': []}]}
                response = {'id': 'resp_mock', 'object': 'response', 'created_at': 1,
                            'status': 'completed', 'model': model, 'output': [message],
                            'usage': {'input_tokens': 5, 'output_tokens': 2, 'total_tokens': 7}}
                events = [
                    {'type': 'response.created', 'response': {**response, 'status': 'in_progress', 'output': []}},
                    {'type': 'response.output_item.added', 'output_index': 0, 'item': {**message, 'content': [], 'status': 'in_progress'}},
                    {'type': 'response.output_text.delta', 'item_id': 'msg_mock', 'output_index': 0, 'content_index': 0, 'delta': 'MOCK_OK'},
                    {'type': 'response.output_item.done', 'output_index': 0, 'item': message},
                    {'type': 'response.completed', 'response': response},
                ]
                self.send_response(200)
                self.send_header('Content-Type', 'text/event-stream')
                self.end_headers()
                for event in events:
                    self.wfile.write(('event: ' + event['type'] + '\ndata: ' + json.dumps(event) + '\n\n').encode())
                self.wfile.flush()

        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                home = root / 'home'
                home.mkdir()
                install_config(home / 'config.toml', 'http://127.0.0.1:' + str(server.server_port))
                env = os.environ.copy()
                env.update({'CODEX_HOME': str(home), 'CODEX_PROXY_API_KEY': 'offline-dummy-key-not-real'})
                try:
                    result = subprocess.run(
                        [*launch_args(tier, 'http://127.0.0.1:' + str(server.server_port)),
                         'exec', '-p', 'vf_' + tier, '--strict-config', '--ephemeral', '--json',
                         '--skip-git-repo-check', '--sandbox', 'read-only', '-'],
                        input=b'Respond MOCK_OK without tools.', capture_output=True,
                        cwd=root, env=env, timeout=30)
                except subprocess.TimeoutExpired as error:
                    # Only isolated test config, fake key and synthetic prompt are involved.
                    self.fail(f'CLI timeout; mock_requests={len(requests)}; '
                              + (error.stderr or b'').decode('utf-8', errors='replace')[-1500:])
                if status == 200:
                    self.assertEqual(result.returncode, 0, result.stderr.decode('utf-8', errors='replace')[-2000:])
                    self.assertIn(b'MOCK_OK', result.stdout)
                else:
                    self.assertNotEqual(result.returncode, 0)
                self.assertEqual(len(requests), 1)
                route, auth, payload = requests[0]
                self.assertTrue(route.startswith('/v1/responses'))
                self.assertEqual(auth, 'Bearer offline-dummy-key-not-real')
                self.assertTrue(payload['stream'])
                self.assertEqual(payload['model'], model)
                self.assertEqual(payload['reasoning']['effort'], effort)
                if tier == 'ultra':
                    # Native tool definitions may travel as incremental input items.
                    self.assertTrue('spawn_agent' in json.dumps(payload),
                                    'Ultra must expose native delegation tools')
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


if __name__ == '__main__':
    unittest.main()
