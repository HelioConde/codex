# Codex CLI usando o proxy VideoForge

**Data:** 14/11/2026. **Implementacao:** `proxy_ai/codex_cli.py`, `proxy_ai/tasks.py`. **Fontes:** pedido do proprietario, CLI instalada 0.166.0 (`--help`, `exec --help`), [referencia oficial](https://developers.openai.com/codex/config-reference/) e [perfis](https://developers.openai.com/codex/config-advanced/#profiles).

## Diagnostico e decisoes

O cliente de texto/imagem ja existia; o template nao ativava o provider local. A configuracao global original usava OpenAI/Astra. O Docker publica `127.0.0.1:8080`; o cliente aceitava HTTP loopback somente em 18080. Agora aceita porta explicita valida em 127.0.0.1, mantendo HTTPS obrigatorio para servidores remotos. Nao le contas OAuth nem altera o pipeline VideoForge.

O proprietario escolheu mesclar provider e perfis globais. A CLI instalada rejeita `[profiles.vf_code]` legado: o instalador usa arquivos V2 em CODEX_HOME. A primeira verificacao identificou essa diferenca; a configuracao foi restaurada do backup e reinstalada no formato V2. Nao houve inferencia nessa verificacao.

## Configuracao e uso

Requisitos: Python 3.11+, CLI Codex 0.166.0+ no PATH. Compatibilidade estrutural verificada na 0.166.0; versoes futuras precisam de nova verificacao. `install` e `check` nao geram conteudo.

```powershell
python -m proxy_ai.codex_cli check --from-docker
python -m proxy_ai.codex_cli install --from-docker
```

`--from-docker` consulta somente PROXY_API_KEY do container autorizado `chatgpt-codex-proxy`, capturada em memoria. Pode-se especificar `--container`. Sem essa opcao, exige CODEX_PROXY_BASE_URL e CODEX_PROXY_API_KEY no ambiente. A URL pode ser informada em `--base-url`; nunca passar a chave como argumento. Redirecionamentos sao recusados no preflight.

O instalador acrescenta `model_providers.videoforge_proxy` ao config.toml, preserva os bytes anteriores, cria um `config.toml.vf-backup-<id>` privado no mesmo diretorio e recusa provider/perfis conflitantes. E idempotente. Cria `vf_simple.config.toml`, `vf_code.config.toml`, `vf_complex.config.toml`, `vf_critical.config.toml`. Nenhum desses arquivos contem chave.

| Classe | Modelo | Esforco |
|---|---|---|
| simple | gpt-6-luna | low |
| code (padrao do comando proxy) | gpt-6.1-sol | medium |
| complex | gpt-6.1-sol | high |
| critical (explicito) | gpt-6-astra | high |

```powershell
# AUTORIZA inferencia: abrir sessao interativa Sol
python -m proxy_ai.codex_cli run --from-docker --execute
# Engenharia mais complexa, sem trocar para Astra:
python -m proxy_ai.codex_cli run --from-docker --task complex --execute
# Astra somente por escolha explicita:
python -m proxy_ai.codex_cli run --from-docker --task critical --execute
```

O lancador verifica health/modelos e passa overrides `-c` que prevalecem sobre o projeto. Define concorrencia de agentes em 2, subagente Luna/low, service_tier default, Responses/SSE, WebSocket desativado, retries HTTP/stream zero e idle timeout de 120 s. Nao cria subagentes automaticamente. Uma sessao interativa pode fazer varias inferencias: `--execute` autoriza essa sessao, nao promete uma unica chamada. `--timeout` controla somente o preflight Python. Argumentos adicionais da CLI podem ser passados depois de `--`.

Os perfis tambem podem ser escolhidos com `codex -p vf_code` quando a chave ja estiver no ambiente. Nesse uso direto nao existe preflight do lancador. O comando `codex` sem perfil continua usando os defaults originais, inclusive o modelo original; isso preserva o fallback. Este trabalho nao troca o modelo desta conversa no aplicativo.

`--fallback-original` permite abrir a configuracao original se o proxy/modelo estiver indisponivel antes da sessao. Sem essa flag, retorna erro. HTTP 401/403 e timeouts sao sanitizados; 429 nao e repetido. Apos iniciar Codex, qualquer codigo de erro retorna ao usuario sem outro provider, evitando duplicacao de trabalho/custo.

Para desfazer: encerrar sessoes proxy, restaurar o backup correto de config.toml (verificar alteracoes posteriores), e remover somente os quatro arquivos vf_*.config.toml criados por esta instalacao. O backup pode conter preferencias privadas e fica fora do Git. Nao apagar outros perfis ou providers.

## Interface reutilizavel para VideoForge

```python
from pathlib import Path
from proxy_ai import ProxyClient
from proxy_ai.tasks import TaskPolicy, TaskRunner

runner = TaskRunner(ProxyClient.from_env(),
    policy=TaskPolicy(max_calls=1, max_concurrency=1, token_budget=8000,
                      max_output_tokens=1024, max_input_chars=12000),
    metrics=Path('outputs/usage.jsonl'))
# Executar SOMENTE com autorizacao para consumir cota:
texto, uso = runner.text('Analise este trecho de erro Remotion fornecido...',
                         tier='code', execute=True)
# Depois de revisar e aprovar o resultado real:
runner.approve(1)
```

O mesmo contrato atende roteiro, storyboard, JSON de cenas, rig, prompts e workflows recebendo apenas contexto relevante. O chamador conserva `canal/<id>/`, o manual principal, RGBA, rig articulado e QA; esta biblioteca nao escreve nessas pastas nem publica videos.

Limites configuraveis: chamadas por tarefa, concorrencia por instancia, caracteres de contexto, max_output_tokens enviado ao servidor, tokens API observados. Uma falha conta como tentativa; nenhuma chamada e repetida. Uso desconhecido bloqueia continuacao. A primeira chamada e chamadas em voo podem ultrapassar o budget observado: **nao e teto garantido de cobranca**. Estes limites sao do SDK TaskRunner, nao do ciclo interno da CLI.

JSONL guarda ID aleatorio, numero da chamada, horario, classe/modelo, contadores API e resultado pendente/aprovado/falhou. Aprovacao e evento separado sem repetir contadores. Somar somente eventos finish; `usage=null` significa desconhecido. Nao grava prompts, respostas, URLs ou chaves. cached_input_tokens ja faz parte de input_tokens: nao somar de novo. Para sessoes normais da CLI, usar o [resumo offline existente](../scripts/resumo_codex.py); TaskRunner nao intercepta a CLI.

Classificacao explicita e deterministica evita uma inferencia extra somente para escolher modelo. Divisao e escalada ficam a cargo do operador/agente responsavel, depois de testes; nao existe loop autonomo de classificacao/delegacao. Cache so e medido quando reportado; nao ha cache de respostas que reutilize codigo desatualizado. Tokens API nao equivalem aos creditos da assinatura.

## Evidencias e pendencias

- Suite inicial: 15 testes offline aprovados; suite ampliada: 36 aprovados, incluindo merge, perfis V2, limites, fallback, erros e SSE simulado. No CI sem CLI instalada, os tres testes nativos opcionais sao ignorados; os demais continuam sem rede.
- CLI 0.166.0: perfil V2 aceito em `debug prompt-input`, sem inferencia; nao publicar o prompt interno.
- CLI real contra servidor SSE simulado: uma requisicao `/v1/responses`, bearer de teste, stream=true, Sol, resposta MOCK_OK. Demonstra protocolo da CLI, nao inferencia pelo proxy real.
- CLI real contra HTTP 429 e 401 simulados: encerrou com erro depois de uma unica requisicao em cada caso, sem retry.
- CI da implementacao: [execucao offline 43603791906](https://github.com/HelioConde/codex/actions/runs/43603791906) concluiu success. Alteracoes publicadas na [PR draft #1](https://github.com/HelioConde/codex/pull/1), sem merge enquanto a validacao real permanece pendente.
- Proxy Docker real: GET `/health` HTTP 200, status ok, uma conta configurada; GET `/v1/models` inclui gpt-6-luna, gpt-6.1-sol, gpt-6-astra. Nenhuma inferencia nesses GETs.
- Actions anteriores confirmadas success: [health 43601574401](https://github.com/HelioConde/codex/actions/runs/43601574401), [models 43601760640](https://github.com/HelioConde/codex/actions/runs/43601760640), [texto 43601944682](https://github.com/HelioConde/codex/actions/runs/43601944682). O pedido relata 17 tokens de entrada e 10 de saida nessa inferencia Astra; nao e medicao nova desta implementacao.

**Pendente:** teste real curto pela CLI Sol, com autorizacao, para comprovar SSE do proxy e comportamento do modelo. Sem esse teste nao declarar os criterios integralmente atendidos. Nao ha percentual de economia medido nem conversao confiavel de tokens em creditos.

O teste esta preparado em [scripts/smoke_codex_proxy.py](../scripts/smoke_codex_proxy.py). `python -m scripts.smoke_codex_proxy` apenas informa o gate, sem acessar Docker/rede. **Somente apos autorizar cota**, `python -m scripts.smoke_codex_proxy --execute` abre uma sessao CLI isolada/efemera Sol/low com timeout de 120 s e sem retries, pede uma funcao soma sem ferramentas e compara sua AST sem executar codigo gerado. Imprime apenas validacao e contadores numericos, nunca logs internos. O prompt pede uma resposta unica; o ciclo interno da CLI nao e um teto garantido de requisicoes/tokens. Creditos de assinatura permanecem desconhecidos. Nao executar esse comando gerativo no CI.

O proxy usa interfaces nao oficiais e pode deixar de funcionar. Compatibilidade tecnica nao comprova autorizacao contratual; usar somente conta propria/autorizada e respeitar termos, cotas e autenticacao. O fallback preservado e a alternativa operacional, sem contornar limites.
