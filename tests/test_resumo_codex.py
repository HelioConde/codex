"""Testes offline: sem rede, credenciais ou logs reais de usuario."""

import json
import tempfile
import unittest
from pathlib import Path

from scripts.resumo_codex import aggregate, session_paths


def token_event(input_tokens, cached, output):
    return {
        "type": "event_msg",
        "payload": {
            "type": "token_count",
            "info": {
                "total_token_usage": {
                    "input_tokens": input_tokens,
                    "cached_input_tokens": cached,
                    "output_tokens": output,
                    "total_tokens": input_tokens + output,
                }
            },
        },
    }


class UsoCodexTest(unittest.TestCase):
    def test_snapshot_cumulativo_nao_duplica(self):
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp) / "session.jsonl"
            file.write_text(
                "\n".join(json.dumps(value) for value in [
                    token_event(100, 40, 10),
                    token_event(240, 190, 30),
                    token_event(240, 190, 30),
                ]) + "\n", encoding="utf-8"
            )
            result = aggregate([Path(tmp)])
            self.assertEqual(result["sessions_scanned"], 1)
            self.assertEqual(result["input_tokens"], 240)
            self.assertEqual(result["cached_input_tokens"], 190)
            self.assertEqual(result["uncached_input_tokens"], 50)
            self.assertEqual(result["output_tokens"], 30)
            self.assertEqual(result["total_tokens"], 270)
            self.assertEqual(result["token_count_events_seen"], 3)

    def test_multiplos_arquivos_e_json_corrompido(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.jsonl").write_text(
                json.dumps(token_event(100, 80, 20)) + "\n{invalido\n",
                encoding="utf-8",
            )
            (root / "b.jsonl").write_text(
                json.dumps(token_event(50, 10, 8)) + "\n",
                encoding="utf-8",
            )
            result = aggregate([root])
            self.assertEqual(result["input_tokens"], 150)
            self.assertEqual(result["cached_input_tokens"], 90)
            self.assertEqual(result["invalid_jsonl_lines"], 1)
            self.assertEqual(result["sessions_with_usage"], 2)

    def test_limite_e_nao_arquivos(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for index in range(3):
                (root / f"{index}.jsonl").write_text(
                    json.dumps(token_event(10, 0, 2)), encoding="utf-8"
                )
            files, limited = session_paths([root], 2)
            self.assertEqual(len(files), 2)
            self.assertTrue(limited)
            result = aggregate([root], max_files=2)
            self.assertTrue(result["truncated_by_file_limit"])
            self.assertEqual(result["input_tokens"], 20)

    def test_invalido_ou_vazio(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "empty.jsonl").write_text(
                '{"type":"event_msg","payload":{"type":"token_count","info":null}}'
            )
            result = aggregate([root])
            self.assertEqual(result["sessions_with_usage"], 0)
            self.assertIsNone(result["cached_input_ratio_pct"])


if __name__ == "__main__":
    unittest.main()
