"""Interface reutilizavel para tarefas, sem ciclos de agentes ou retries.

O budget e de tokens API observados, nao de creditos de assinatura.
Nao e um teto de faturamento: a primeira chamada/em voo pode ultrapassa-lo.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import threading
import uuid

from .client import ProxyClient, ProxyError
from .codex_cli import TIERS


@dataclass(frozen=True)
class TaskPolicy:
    max_calls: int = 1
    max_concurrency: int = 1
    token_budget: int = 8000
    max_output_tokens: int = 2048
    max_input_chars: int = 12000

    def __post_init__(self):
        limits = {'max_calls': 20, 'max_concurrency': 4, 'token_budget': 1000000,
                  'max_output_tokens': 32000, 'max_input_chars': 60000}
        for name, maximum in limits.items():
            value = getattr(self, name)
            if type(value) is not int or not 1 <= value <= maximum:
                raise ProxyError('Limite de tarefa invalido: ' + name)


class TaskRunner:
    def __init__(self, client: ProxyClient, *, policy: TaskPolicy | None = None,
                 metrics: Path | None = None):
        self.client = client
        self.policy = policy or TaskPolicy()
        self.metrics = Path(metrics) if metrics else None
        self.task_id = uuid.uuid4().hex
        self._lock = threading.Lock()
        self._slots = threading.BoundedSemaphore(self.policy.max_concurrency)
        self._calls = 0
        self._tokens = 0
        self._unknown_usage = False
        self._reviewable: set[int] = set()

    def _record(self, record: dict) -> None:
        if self.metrics is not None:
            self.metrics.parent.mkdir(parents=True, exist_ok=True)
            with self.metrics.open('a', encoding='utf-8') as stream:
                stream.write(json.dumps({'task_id': self.task_id,
                                         'time_utc': datetime.now(timezone.utc).isoformat(),
                                         **record}) + '\n')

    def approve(self, call_number: int) -> None:
        """Registrar aprovacao SOMENTE depois da revisao externa do resultado."""
        with self._lock:
            if call_number not in self._reviewable:
                raise ProxyError('Chamada ausente, falhou ou ja foi aprovada.')
            self._record({'call': call_number, 'event': 'review', 'result': 'approved'})
            self._reviewable.remove(call_number)

    def text(self, prompt: str, *, tier: str = 'code', instructions: str = '',
             execute: bool = False) -> tuple[str, dict]:
        if not execute:
            raise ProxyError('Requer execute=True para consumir cota.')
        if tier == 'ultra':
            raise ProxyError('Ultra requer orquestracao nativa do Codex CLI; use proxy_ai.codex_cli run --task ultra.')
        if tier not in TIERS:
            raise ProxyError('Classe de tarefa invalida.')
        if not isinstance(prompt, str) or not isinstance(instructions, str) or len(prompt) + len(instructions) > self.policy.max_input_chars:
            raise ProxyError('Contexto excede limite da tarefa.')
        with self._slots:
            with self._lock:
                if self._calls >= self.policy.max_calls or self._tokens >= self.policy.token_budget or self._unknown_usage:
                    raise ProxyError('Limite atingido ou consumo anterior desconhecido; revisar antes de continuar.')
                self._calls += 1
                call_number = self._calls
                # Validar arquivo de metricas antes da chamada gerativa.
                self._record({'call': call_number, 'event': 'start', 'tier': tier})
            model, effort = TIERS[tier]
            try:
                result, usage = self.client.text(prompt, model=model, effort=effort,
                                                instructions=instructions,
                                                max_output_tokens=self.policy.max_output_tokens)
            except Exception:
                with self._lock:
                    self._unknown_usage = True
                    self._record({'call': call_number, 'event': 'finish', 'model': model,
                                  'result': 'failed', 'usage': None})
                raise
            usage = {key: value for key, value in usage.items()
                     if key in ('input_tokens', 'output_tokens', 'total_tokens', 'cached_input_tokens') and type(value) is int and value >= 0}
            with self._lock:
                known = 'total_tokens' in usage or all(key in usage for key in ('input_tokens', 'output_tokens'))
                self._unknown_usage = self._unknown_usage or not known
                self._tokens += usage.get('total_tokens', usage.get('input_tokens', 0) + usage.get('output_tokens', 0))
                self._record({'call': call_number, 'event': 'finish', 'model': model,
                              'result': 'pending_review', 'usage': usage if known else None})
                self._reviewable.add(call_number)
            return result, usage
