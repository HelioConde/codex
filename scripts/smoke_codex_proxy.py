"""Smoke test Sol opt-in: python -m scripts.smoke_codex_proxy --execute.

Usa Docker autorizado existente. Sem flag nao consulta nem o Docker.
"""
import argparse
import ast
import json
import os
from pathlib import Path
import subprocess
import tempfile

from proxy_ai.codex_cli import check_cli, install_config, load_client
from proxy_ai.client import ProxyError


def valid_sum(source: str) -> bool:
    """Compara AST com a funcao esperada sem executar codigo gerado."""
    try:
        actual = ast.dump(ast.parse(source), include_attributes=False)
        expected = ast.dump(ast.parse('def soma(a, b):\n    return a + b'), include_attributes=False)
        return actual == expected
    except (ValueError, TypeError, SyntaxError, RecursionError):
        return False


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true', help='Autoriza consumo de cota da CLI Sol')
    args = parser.parse_args(argv)
    if not args.execute:
        print('Nenhuma chamada realizada. --execute autoriza teste real Sol/low (cota e creditos desconhecidos).')
        return 0
    try:
        version = check_cli()
        client = load_client(argparse.Namespace(base_url=None, from_docker=True,
                            container='chatgpt-codex-proxy', timeout=10))
        client.health()
        if 'gpt-6.1-sol' not in client.models():
            raise ProxyError('Sol indisponivel.')
        with tempfile.TemporaryDirectory(prefix='codex-proxy-smoke-') as tmp:
            home = Path(tmp) / 'home'
            install_config(home / 'config.toml', client.base_url)
            env = os.environ.copy()
            env.update({'CODEX_HOME': str(home), 'CODEX_PROXY_API_KEY': client._api_key})
            completed = subprocess.run(
                ['codex', 'exec', '-p', 'vf_code', '-c', 'model_reasoning_effort="low"',
                 '--ephemeral', '--json', '--skip-git-repo-check', '--sandbox', 'read-only', '-'],
                input=b'Return ONLY Python code: def soma(a, b) with return a + b. No markdown. Do not use tools.',
                capture_output=True, cwd=tmp, env=env, timeout=120)
            # Nunca publica logs completos nem conteudo interno da CLI.
            if completed.returncode:
                raise ProxyError('CLI falhou; sem retry. Nao tratar consumo desconhecido como zero.')
            events = [json.loads(line) for line in completed.stdout.splitlines() if line.strip()]
            messages = [e['item'].get('text', '') for e in events if e.get('type') == 'item.completed'
                        and e.get('item', {}).get('type') == 'agent_message']
            usage = next((e.get('usage') for e in reversed(events) if e.get('type') == 'turn.completed'), None)
            usage = {k: v for k, v in (usage or {}).items()
                     if k in ('input_tokens', 'output_tokens', 'cached_input_tokens') and type(v) is int and v >= 0}
            passed = bool(messages) and valid_sum(messages[-1])
            print(json.dumps({'cli': version, 'model': 'gpt-6.1-sol', 'effort': 'low',
                              'python_ast_valid': passed, 'usage': usage or None,
                              'subscription_credits': 'unknown'}))
            return 0 if passed else 2
    except (ProxyError, OSError, ValueError, subprocess.TimeoutExpired) as error:
        print(str(error) if isinstance(error, ProxyError) else 'Teste interrompido; detalhes privados ocultados, sem retry.')
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
