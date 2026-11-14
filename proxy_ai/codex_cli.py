"""Perfis globais e lancamento opt-in; nenhuma inferencia durante check/install.

Compatibilidade inicial: Codex CLI 0.166.0, Python 3.11+.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import tomllib
import uuid

from .client import ProxyClient, ProxyError, normalize_base_url

TIERS = {
    'ultra': ('gpt-6-astra', 'ultra'),
    'simple': ('gpt-6-luna', 'low'),
    'code': ('gpt-6.1-sol', 'medium'),
    'complex': ('gpt-6.1-sol', 'high'),
    'critical': ('gpt-6-astra', 'high'),
}


def provider_settings(base_url: str) -> dict:
    return {
        'name': 'VideoForge Codex Proxy',
        'base_url': normalize_base_url(base_url) + '/v1',
        'env_key': 'CODEX_PROXY_API_KEY',
        'wire_api': 'responses',
        'requires_openai_auth': False,
        'supports_websockets': False,
        'request_max_retries': 0,
        'stream_max_retries': 0,
        'stream_idle_timeout_ms': 120000,
    }


def _toml_value(value) -> str:
    return json.dumps(value, ensure_ascii=True)


def install_config(path: Path, base_url: str) -> Path | None:
    """Acrescenta tabelas sem reserializar o original. Recusa qualquer colisao."""
    path = Path(path)
    if path.is_symlink():
        raise ProxyError('Configuracao nao pode ser link simbolico.')
    original = path.read_bytes() if path.exists() else b''
    try:
        existing = tomllib.loads(original.decode('utf-8-sig'))
    except (UnicodeError, tomllib.TOMLDecodeError):
        raise ProxyError('Configuracao global invalida; arquivo preservado.') from None
    settings = provider_settings(base_url)
    providers = existing.get('model_providers', {})
    profiles = existing.get('profiles', {})
    if not isinstance(providers, dict) or not isinstance(profiles, dict):
        raise ProxyError('Tabelas globais invalidas; arquivo preservado.')
    present = providers.get('videoforge_proxy')
    if present is not None and present != settings:
        raise ProxyError('Provider ja existe com valores diferentes; arquivo preservado.')
    new_profiles = {}
    for tier, (model, effort) in TIERS.items():
        name = 'vf_' + tier
        if name in profiles or existing.get('profile') == name:
            raise ProxyError('Perfil legado encontrado; migrar explicitamente antes de instalar.')
        profile_settings = {
            'model': model, 'model_provider': 'videoforge_proxy',
            'model_reasoning_effort': effort,
            'service_tier': 'default',
        }
        target = path.parent / (name + '.config.toml')
        if target.is_symlink():
            raise ProxyError('Perfil nao pode ser link simbolico.')
        if target.exists():
            if tomllib.loads(target.read_text(encoding='utf-8-sig')) != profile_settings:
                raise ProxyError('Perfil ja existe com valores diferentes; arquivo preservado.')
        else:
            new_profiles[target] = ''.join(k + ' = ' + _toml_value(v) + '\n'
                                           for k, v in profile_settings.items()).encode('utf-8')
    if present is not None and not new_profiles:
        return None
    # Verificar o TOML inteiro antes de qualquer alteracao no destino.
    addition = '\n# VideoForge: provider adicionado em 2026-11-14\n[model_providers.videoforge_proxy]\n'
    addition += ''.join(k + ' = ' + _toml_value(v) + '\n' for k, v in settings.items())
    merged = original + addition.encode('utf-8') if present is None else original
    tomllib.loads(merged.decode('utf-8-sig'))
    path.parent.mkdir(parents=True, exist_ok=True)
    backup = path.with_name(path.name + '.vf-backup-' + uuid.uuid4().hex)
    fd = os.open(backup, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(original)
    fd, temporary = tempfile.mkstemp(prefix='.vf-config-', dir=path.parent)
    created = []
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(merged)
        if (path.read_bytes() if path.exists() else b'') != original:
            raise ProxyError('Configuracao alterada durante a instalacao; tente revisar novamente.')
        for target, content in new_profiles.items():
            with target.open('xb') as stream:
                created.append(target)
                stream.write(content)
        os.replace(temporary, path)
    except Exception:
        for target in created:
            target.unlink()
        raise
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return backup


def check_cli() -> str:
    try:
        result = subprocess.run(['codex', '--version'], capture_output=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        raise ProxyError('Codex CLI indisponivel.') from None
    match = re.search(rb'codex-cli (\d+)\.(\d+)\.(\d+)', result.stdout)
    if result.returncode or not match or tuple(map(int, match.groups())) < (0, 166, 0):
        raise ProxyError('Requer Codex CLI 0.166.0+; versao nao validada.')
    return match.group(0).decode('ascii')


def load_client(args) -> ProxyClient:
    base_url = args.base_url or os.environ.get('CODEX_PROXY_BASE_URL', '')
    key = os.environ.get('CODEX_PROXY_API_KEY', '')
    if args.from_docker:
        # Captura somente a API key do proxy; nunca le accounts.json/OAuth.
        try:
            result = subprocess.run(
                ['docker', 'exec', args.container, 'printenv', 'PROXY_API_KEY'],
                capture_output=True, timeout=10)
        except (OSError, subprocess.TimeoutExpired):
            raise ProxyError('Docker indisponivel; chave nao carregada.') from None
        if result.returncode:
            raise ProxyError('Nao foi possivel obter chave do container autorizado.')
        key = result.stdout.decode('utf-8').strip()
        base_url = base_url or 'http://127.0.0.1:8080'
    return ProxyClient(base_url, key, timeout=args.timeout)


def launch_args(tier: str, base_url: str) -> list[str]:
    model, effort = TIERS[tier]
    settings = {'model_provider': 'videoforge_proxy', 'model': model,
                'model_reasoning_effort': effort, 'service_tier': 'default',
                'agents.max_concurrent_threads_per_session': 2,
                'agents.default_subagent_model': 'gpt-6-luna',
                'agents.default_subagent_reasoning_effort': 'low'}
    settings.update({'model_providers.videoforge_proxy.' + k: v
                     for k, v in provider_settings(base_url).items()})
    args = ['codex']
    for key, value in settings.items():
        args.extend(['-c', key + '=' + _toml_value(value)])
    return args


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Codex com perfis VideoForge (sem gerar por padrao)')
    parser.add_argument('action', choices=('check', 'install', 'run'))
    parser.add_argument('--task', choices=TIERS, default='ultra')
    parser.add_argument('--base-url')
    parser.add_argument('--from-docker', action='store_true')
    parser.add_argument('--container', default='chatgpt-codex-proxy')
    parser.add_argument('--timeout', type=int, default=10)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--fallback-original', action='store_true')
    # Separar argumentos do Codex explicitamente; nunca interpretar prompts aqui.
    raw = list(argv) if argv is not None else sys.argv[1:]
    boundary = raw.index('--') if '--' in raw else len(raw)
    args = parser.parse_args(raw[:boundary])
    forwarded = raw[boundary + 1:]
    if args.action != 'run' and forwarded:
        parser.error('Argumentos Codex somente com run.')
    if args.action == 'run' and not args.execute:
        print('Nenhuma chamada de IA realizada. Use --execute para abrir Codex; --task seleciona o modelo.')
        return 0
    try:
        version = check_cli()
        try:
            client = load_client(args)
            health = client.health()
            models = client.models()
            if TIERS[args.task][0] not in models:
                raise ProxyError('Modelo selecionado indisponivel; nao escalar automaticamente.')
        except ProxyError:
            if args.action == 'run' and args.fallback_original:
                print('Proxy indisponivel antes da sessao; abrindo configuracao original autorizada.', file=sys.stderr)
                return subprocess.call(['codex', *forwarded])
            raise
        if args.action == 'check':
            print(json.dumps({'cli': version, 'health': health, 'models': models,
                              'streaming': 'pendente de inferencia autorizada'}))
            return 0
        if args.action == 'install':
            config_home = Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex')))
            backup = install_config(config_home / 'config.toml', client.base_url)
            print('Perfis globais instalados; backup local criado.' if backup else 'Perfis ja instalados; sem alteracao.')
            return 0
        env = os.environ.copy()
        env['CODEX_PROXY_API_KEY'] = client._api_key
        env['CODEX_PROXY_BASE_URL'] = client.base_url
        # Uma unica sessao: um erro apos iniciar nunca aciona outro provider.
        return subprocess.call([*launch_args(args.task, client.base_url), *forwarded], env=env)
    except (ProxyError, OSError, ValueError) as exc:
        message = str(exc) if isinstance(exc, ProxyError) else 'Falha local; detalhes privados ocultados.'
        print('ERRO: ' + message, file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
