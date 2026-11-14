#!/usr/bin/env python3
"""Resume uso de tokens em JSONL do Codex local, sem revelar mensagens ou credenciais.

Nao envia dados pela rede. Nao calcula custo/creditos: franqui(a) Codex e precos
da API possuem formas diferentes de cobranca.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable

FIELDS = ("input_tokens", "cached_input_tokens", "output_tokens",
          "reasoning_output_tokens", "total_tokens")


def session_paths(sources: Iterable[Path], limit: int) -> tuple[list[Path], bool]:
    """Retorna arquivos JSONL ordenados e informa se houve truncamento."""
    files: set[Path] = set()
    for source in sources:
        if source.is_file() and source.suffix.lower() == ".jsonl":
            files.add(source.resolve())
        elif source.is_dir():
            files.update(p.resolve() for p in source.rglob("*.jsonl") if p.is_file())
    ordered = sorted(files)
    return ordered[:limit], len(ordered) > limit


def session_usage(path: Path) -> tuple[dict[str, int], int, int]:
    """Toma o maior contador cumulativo por sessao; nao soma snapshots repetidos."""
    cumulative = {key: 0 for key in FIELDS}
    calls = 0
    invalid = 0
    with path.open("r", encoding="utf-8", errors="replace") as stream:
        for line in stream:
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                invalid += 1
                continue
            if not isinstance(event, dict) or event.get("type") != "event_msg":
                continue
            payload = event.get("payload")
            if not isinstance(payload, dict) or payload.get("type") != "token_count":
                continue
            info = payload.get("info")
            if not isinstance(info, dict):
                continue
            totals = info.get("total_token_usage")
            if not isinstance(totals, dict):
                continue
            calls += 1
            for field in FIELDS:
                value = totals.get(field)
                if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
                    cumulative[field] = max(cumulative[field], value)
    return cumulative, calls, invalid


def aggregate(sources: Iterable[Path], max_files: int = 5000) -> dict:
    files, limited = session_paths(sources, max_files)
    totals = {field: 0 for field in FIELDS}
    sessions_with_usage = 0
    token_events = 0
    invalid_lines = 0
    unreadable_files = 0
    for path in files:
        try:
            session, events, invalid = session_usage(path)
        except OSError:
            unreadable_files += 1
            continue
        if events:
            sessions_with_usage += 1
        token_events += events
        invalid_lines += invalid
        for field in FIELDS:
            totals[field] += session[field]

    if not totals["total_tokens"]:
        totals["total_tokens"] = totals["input_tokens"] + totals["output_tokens"]
    tokens_in = totals["input_tokens"]
    cached = min(totals["cached_input_tokens"], tokens_in)
    return {
        "sessions_scanned": len(files),
        "sessions_with_usage": sessions_with_usage,
        "truncated_by_file_limit": limited,
        "unreadable_files": unreadable_files,
        "invalid_jsonl_lines": invalid_lines,
        "token_count_events_seen": token_events,
        "input_tokens": tokens_in,
        "cached_input_tokens": cached,
        "uncached_input_tokens": max(0, tokens_in - cached),
        "output_tokens": totals["output_tokens"],
        "reasoning_output_tokens": totals["reasoning_output_tokens"],
        "total_tokens": totals["total_tokens"],
        "cached_input_ratio_pct": round(100.0 * cached / tokens_in, 2)
        if tokens_in else None,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Resumo privado de tokens Codex em JSONL. Sem rede e sem prompts."
    )
    parser.add_argument(
        "paths", nargs="*", type=Path,
        help="Arquivos/diretorios JSONL (padrao: ~/.codex/sessions)",
    )
    parser.add_argument("--json", action="store_true", help="Saida JSON agregada")
    parser.add_argument("--max-files", type=int, default=5000,
                        help="Teto de arquivos lidos (padrao: 5000)")
    args = parser.parse_args(argv)
    if args.max_files < 1:
        parser.error("--max-files deve ser positivo")
    paths = args.paths or [Path.home() / ".codex" / "sessions"]
    result = aggregate(paths, args.max_files)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("Resumo LOCAL de uso Codex (sem logs privados)")
        for name, value in result.items():
            print(f"{name}: {value}")
        print("Nota: contadores cumulativos por sessao; quota/custo nao inferidos.")
    if result["sessions_scanned"] == 0:
        print("Nenhum JSONL encontrado nos caminhos fornecidos.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
