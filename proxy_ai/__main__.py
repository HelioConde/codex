"""Interface de linha de comando: geracao so acontece com --execute."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .client import ProxyClient, ProxyError


def read_prompt(path: str) -> str:
    if path == "-":
        return sys.stdin.read(60001)
    source = Path(path)
    if not source.is_file() or source.stat().st_size > 200000:
        raise ProxyError("Arquivo de prompt ausente ou muito grande.")
    return source.read_text(encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Cliente IA do Codex Proxy (texto e imagens)")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("health", help="Saude e autenticacao, sem gerar conteudo")
    sub.add_parser("models", help="Listar modelos, sem gerar conteudo")

    text_cmd = sub.add_parser("text", help="Usar /v1/responses para planejamento e analise")
    text_cmd.add_argument("--prompt-file", required=True, help="Arquivo UTF-8 ou - para stdin")
    text_cmd.add_argument("--instructions-file", help="Arquivo de instrucoes opcional")
    text_cmd.add_argument("--model", default="gpt-6.1-sol")
    text_cmd.add_argument("--effort", choices=("low", "medium", "high"), default="low")
    text_cmd.add_argument("--output", type=Path)
    text_cmd.add_argument("--execute", action="store_true", help="Autorizar requisicao gerativa")

    image_cmd = sub.add_parser("image", help="Gerar uma imagem no proxy")
    image_cmd.add_argument("--prompt-file", required=True, help="Arquivo UTF-8 ou - para stdin")
    image_cmd.add_argument("--model", default="gpt-image-2")
    image_cmd.add_argument("--size", choices=("1024x1024", "1024x1536", "1536x1024"), default="1024x1024")
    image_cmd.add_argument("--output", type=Path, required=True, help="Destino novo, sem sobrescrita")
    image_cmd.add_argument("--execute", action="store_true")

    args = parser.parse_args(argv)
    try:
        if args.command in ("text", "image") and not args.execute:
            print("Nenhuma chamada de IA realizada. Use --execute para autorizar.")
            return 0
        if args.command == "text" and args.output and (args.output.exists() or args.output.is_symlink()):
            raise ProxyError("Arquivo de resposta ja existe; nao chamar a IA de novo.")
        client = ProxyClient.from_env()
        if args.command == "health":
            print(json.dumps(client.health(), ensure_ascii=False))
        elif args.command == "models":
            print(json.dumps({"models": client.models()}, ensure_ascii=False, indent=2))
        elif args.command == "text":
            prompt = read_prompt(args.prompt_file)
            instructions = read_prompt(args.instructions_file) if args.instructions_file else ""
            output, usage = client.text(prompt, model=args.model, instructions=instructions, effort=args.effort)
            if args.output:
                if args.output.exists() or args.output.is_symlink():
                    raise ProxyError("Arquivo de resposta ja existe; nao sera sobrescrito.")
                args.output.parent.mkdir(parents=True, exist_ok=True)
                with args.output.open("x", encoding="utf-8") as f:
                    f.write(output)
                print("Resposta gravada no arquivo local indicado.")
            else:
                print(output)
            if usage:
                print("Uso informado pelo proxy: " + json.dumps(usage), file=sys.stderr)
        else:
            result = client.image(read_prompt(args.prompt_file), args.output,
                                  model=args.model, size=args.size)
            print(json.dumps(result, ensure_ascii=False))
    except (ProxyError, UnicodeError, OSError) as exc:
        if isinstance(exc, ProxyError):
            print("ERRO: " + str(exc), file=sys.stderr)
        else:
            print("ERRO: falha ao ler ou gravar arquivo local.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
