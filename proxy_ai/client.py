"""Cliente seguro de IA de texto e imagens para o proxy ja usado no VideoForge-IA.

Nao gerencia contas, nao renova OAuth, nao faz retry automatico e nao
publica prompts/segredos. O servidor upstream e nao oficial e pode mudar.
"""
from __future__ import annotations

import base64
import binascii
import hashlib
import json
import os
from pathlib import Path
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

MAX_TEXT_RESPONSE = 1024 * 1024
MAX_IMAGE_RESPONSE = 48 * 1024 * 1024
MAX_IMAGE_BYTES = 32 * 1024 * 1024
MAX_INPUT_CHARS = 60000
MAX_INSTRUCTIONS_CHARS = 24000
IMAGE_MODELS = frozenset({"gpt-image-2", "gpt-image-1.5"})
IMAGE_SIZES = frozenset({"1024x1024", "1024x1536", "1536x1024"})
MODEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{1,100}$")


class ProxyError(RuntimeError):
    """Erro sanitizado; nunca inclui URL, payload, prompt ou chave."""


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Impede envio de Authorization a redirects para outras origens."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def normalize_base_url(base_url: str) -> str:
    if not isinstance(base_url, str) or not base_url.strip():
        raise ProxyError("CODEX_PROXY_BASE_URL ausente.")
    try:
        p = urllib.parse.urlsplit(base_url.strip())
        port = p.port
    except ValueError:
        raise ProxyError("URL do proxy invalida.") from None
    if p.scheme == "https" and p.hostname:
        pass
    elif p.scheme == "http" and p.hostname == "127.0.0.1" and port is not None and 1 <= port <= 65535:
        pass
    else:
        raise ProxyError("Usar HTTPS ou HTTP com porta explicita em 127.0.0.1 (local).")
    if p.username or p.password or p.query or p.fragment or p.path.rstrip("/") not in ("", "/v1"):
        raise ProxyError("URL deve conter apenas origem HTTPS (opcional /v1), sem credenciais ou query.")
    return urllib.parse.urlunsplit((p.scheme, p.netloc, "", "", ""))


def parse_response_text(response: dict[str, Any]) -> str:
    value = response.get("output_text")
    if isinstance(value, str) and value.strip():
        return value
    chunks: list[str] = []
    output = response.get("output", [])
    if not isinstance(output, list):
        raise ProxyError("Formato da resposta de IA invalido.")
    for item in output:
        if not isinstance(item, dict) or item.get("type") != "message":
            continue
        content = item.get("content", [])
        if not isinstance(content, list):
            continue
        for part in content:
            if isinstance(part, dict) and part.get("type") in ("output_text", "text") and isinstance(part.get("text"), str):
                chunks.append(part["text"])
    if chunks and "".join(chunks).strip():
        return "".join(chunks)
    raise ProxyError("Proxy respondeu sem texto de assistente utilizavel.")


def _decode_image(response: dict[str, Any]) -> tuple[bytes, str]:
    images = response.get("data")
    if not isinstance(images, list) or len(images) != 1 or not isinstance(images[0], dict):
        raise ProxyError("Resposta de imagem invalida: esperada uma imagem.")
    raw = images[0].get("b64_json")
    if raw is None:
        raw = images[0].get("url")
    if not isinstance(raw, str):
        raise ProxyError("Resposta nao inclui imagem base64.")
    if raw.startswith("data:image/"):
        if ";base64," not in raw:
            raise ProxyError("Data URL invalida.")
        raw = raw.split(";base64,", 1)[1]
    elif "://" in raw or raw.startswith("data:"):
        raise ProxyError("Nao baixar imagem de URL remota.")
    if len(raw) > MAX_IMAGE_BYTES * 4 // 3 + 128:
        raise ProxyError("Imagem base64 excede limite.")
    try:
        binary = base64.b64decode(raw, validate=True)
    except (ValueError, binascii.Error):
        raise ProxyError("Base64 invalido.") from None
    if not 50 <= len(binary) <= MAX_IMAGE_BYTES:
        raise ProxyError("Imagem vazia ou muito grande.")
    if binary.startswith(b"\x89PNG\r\n\x1a\n") and b"IEND" in binary[-20:]:
        return binary, ".png"
    if binary.startswith(b"\xff\xd8\xff") and binary.endswith(b"\xff\xd9"):
        return binary, ".jpg"
    if binary.startswith(b"RIFF") and binary[8:12] == b"WEBP" and int.from_bytes(binary[4:8], "little") + 8 == len(binary):
        return binary, ".webp"
    raise ProxyError("Assinatura de imagem nao suportada.")


class ProxyClient:
    def __init__(self, base_url: str, api_key: str, *, timeout: int = 120):
        self.base_url = normalize_base_url(base_url)
        if not isinstance(api_key, str) or len(api_key) < 20 or "\n" in api_key or "\r" in api_key:
            raise ProxyError("CODEX_PROXY_API_KEY ausente ou invalida (minimo 20 caracteres).")
        self._api_key = api_key
        if not 1 <= timeout <= 300:
            raise ProxyError("Timeout fora dos limites (1 a 300 s).")
        self.timeout = timeout

    @classmethod
    def from_env(cls) -> "ProxyClient":
        return cls(os.environ.get("CODEX_PROXY_BASE_URL", ""), os.environ.get("CODEX_PROXY_API_KEY", ""))

    def _json(self, route: str, payload: dict[str, Any] | None = None,
              *, max_size: int = MAX_TEXT_RESPONSE) -> dict:
        if route not in ("/health", "/v1/models", "/v1/responses", "/v1/images/generations"):
            raise ProxyError("Rota nao autorizada pelo cliente.")
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None
        req = urllib.request.Request(
            self.base_url + route, data=body,
            headers={
                "Authorization": "Bearer " + self._api_key,
                "Accept": "application/json",
                **({"Content-Type": "application/json"} if body is not None else {}),
            },
            method="POST" if body is not None else "GET",
        )
        opener = urllib.request.build_opener(_NoRedirect())
        try:
            with opener.open(req, timeout=self.timeout) as response:
                data = response.read(max_size + 1)
        except urllib.error.HTTPError as exc:
            exc.close()
            if exc.code == 429:
                raise ProxyError("HTTP 429: limite/cota do proxy. Nao repetir automaticamente.") from None
            if exc.code in (401, 403):
                raise ProxyError(f"HTTP {exc.code}: falha de autenticacao/permissao; verificar credencial autorizada.") from None
            raise ProxyError(f"Proxy retornou HTTP {exc.code}; resposta ocultada.") from None
        except (urllib.error.URLError, TimeoutError, OSError):
            raise ProxyError("Falha ao conectar ao proxy; endereco e credenciais ocultados.") from None
        if len(data) > max_size:
            raise ProxyError("Resposta do proxy excedeu o tamanho maximo.")
        try:
            value = json.loads(data)
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ProxyError("Resposta do proxy nao e JSON valido.") from None
        if not isinstance(value, dict):
            raise ProxyError("Resposta JSON do proxy nao e um objeto.")
        return value

    def health(self) -> dict[str, Any]:
        result = self._json("/health")
        if result.get("status") != "ok":
            raise ProxyError("Health nao confirmou status ok.")
        accounts = result.get("accounts")
        if not isinstance(accounts, int) or accounts < 1:
            raise ProxyError("Proxy acessivel, mas sem conta autenticada cadastrada.")
        return {"status": "ok", "accounts_configured": accounts}

    def models(self) -> list[str]:
        response = self._json("/v1/models")
        models = response.get("data")
        if not isinstance(models, list):
            raise ProxyError("Catalogo de modelos indisponivel.")
        return sorted({m["id"] for m in models if isinstance(m, dict) and isinstance(m.get("id"), str)})

    def text(self, prompt: str, *, model: str = "gpt-6.1-sol", instructions: str = "",
             effort: str = "low", max_output_tokens: int | None = None) -> tuple[str, dict[str, Any]]:
        if not isinstance(model, str) or not MODEL_RE.fullmatch(model):
            raise ProxyError("Identificador de modelo invalido.")
        if not isinstance(prompt, str) or not 1 <= len(prompt.strip()) <= MAX_INPUT_CHARS:
            raise ProxyError("Prompt vazio ou superior a 60 mil caracteres.")
        if not isinstance(instructions, str) or len(instructions) > MAX_INSTRUCTIONS_CHARS:
            raise ProxyError("Instrucoes longas demais (maximo 24 mil caracteres).")
        if effort not in ("low", "medium", "high"):
            raise ProxyError("Reasoning effort invalido.")
        if max_output_tokens is not None and (type(max_output_tokens) is not int or not 1 <= max_output_tokens <= 32000):
            raise ProxyError("max_output_tokens deve estar entre 1 e 32000.")
        payload: dict[str, Any] = {
            "model": model, "input": prompt, "stream": False,
            "reasoning": {"effort": effort},
        }
        if instructions.strip():
            payload["instructions"] = instructions
        if max_output_tokens is not None:
            payload["max_output_tokens"] = max_output_tokens
        response = self._json("/v1/responses", payload)
        usage = response.get("usage")
        if not isinstance(usage, dict):
            usage = {}
        safe_usage = {field: usage[field] for field in ("input_tokens", "output_tokens", "total_tokens")
                      if isinstance(usage.get(field), int) and usage[field] >= 0}
        details = usage.get('input_tokens_details')
        cached = details.get('cached_tokens') if isinstance(details, dict) else None
        if type(cached) is int and 0 <= cached <= safe_usage.get('input_tokens', 0):
            safe_usage['cached_input_tokens'] = cached
        return parse_response_text(response), safe_usage

    def image(self, prompt: str, path: Path, *, model: str = "gpt-image-2",
              size: str = "1024x1024") -> dict[str, Any]:
        if model not in IMAGE_MODELS or size not in IMAGE_SIZES:
            raise ProxyError("Modelo ou tamanho de imagem nao autorizado.")
        if not isinstance(prompt, str) or not 10 <= len(prompt.strip()) <= 5000:
            raise ProxyError("Prompt de imagem deve ter 10 a 5000 caracteres.")
        target = Path(path)
        if target.exists() or target.is_symlink():
            raise ProxyError("Nao sobrescrever imagem existente.")
        if not target.suffix and any(target.with_suffix(ext).exists() or target.with_suffix(ext).is_symlink()
                                     for ext in (".png", ".jpg", ".webp")):
            raise ProxyError("Ja existe imagem neste destino; nao gerar novamente.")
        if target.parent.is_symlink():
            raise ProxyError("Diretorio de destino nao pode ser link simbolico.")
        response = self._json(
            "/v1/images/generations",
            {"model": model, "prompt": prompt, "size": size, "n": 1,
             "stream": False, "response_format": "b64_json"},
            max_size=MAX_IMAGE_RESPONSE,
        )
        binary, ext = _decode_image(response)
        if target.suffix.lower() not in ("", ext):
            raise ProxyError("Extensao de destino nao corresponde ao retorno.")
        if not target.suffix:
            target = target.with_suffix(ext)
        if target.exists() or target.is_symlink():
            raise ProxyError("Imagem existente nao sera substituida.")
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.parent.is_symlink():
            raise ProxyError("Diretorio de destino nao pode ser link simbolico.")
        try:
            with target.open("xb") as stream:
                stream.write(binary)
        except FileExistsError:
            raise ProxyError("Imagem existente nao sera substituida.") from None
        return {"path": str(target), "sha256": hashlib.sha256(binary).hexdigest(),
                "bytes": len(binary), "model": model, "size_requested": size,
                "qa_visual": "pendente"}
