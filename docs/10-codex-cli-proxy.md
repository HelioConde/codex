# Codex CLI usando o proxy VideoForge

**Data:** 14/11/2026. **Implementacao:** `proxy_ai/codex_cli.py`, `proxy_ai/tasks.py`. **Fontes:** pedido do proprietario, CLI instalada 0.166.0 (`--help`, `exec --help`), [referencia oficial](https://developers.openai.com/codex/config-reference/) e [perfis](https://developers.openai.com/codex/config-advanced/#profiles).

## Diagnostico e decisoes

O cliente de texto/imagem ja existia; o template nao ativava o provider local. A configuracao global original usava OpenAI/Astra. O Docker publica `127.0.0.1:8080`; o cliente aceitava HTTP loopback somente em 18080. Agora aceita porta explicita valida em 127.0.0.1, mantendo HTTPS obrigatorio para servidores remotos. Nao le contas OAuth nem altera o pipeline VideoForge.

O proprietario escolheu mesclar provider e perfis globais. A CLI instalada rejeita `[profiles.vf_code]` legado: o instalador usa arquivos V2 em CODEX_HOME. A primeira verificacao identificou essa diferenca; a configuracao foi restaurada do backup e reinstalada no formato V2. Nao houve inferencia nessa verificacao.

**Escolha final do usuario em 14/11/2026, esclarecida por imagem do seletor:** Astra no modo Ultra como principal. Isso substitui o default inicial Sol do lancador. O perfil global `vf_ultra.config.toml` e `.codex/config.toml` selecionam `gpt-6-astra` e `model_reasoning_effort="ultra"`; o provider original continua preservado para fallback.

Ultra e um modo nativo do Codex com delegacao a subagentes, conforme [documentacao oficial](https://learn.chatgpt.com/docs/models#know-when-to-use-max-or-ultra). Na CLI 0.166.0, o catalogo Astra define `multi_agent_reasoning_effort="xhigh"`, `multi_agent_version="v2"`; o [resolvedor oficial dessa versao](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/protocol/src/openai_models/reasoning_effort.rs) converte a selecao Ultra para esse esforco na requisicao. O teste com a CLI real confirmou `reasoning.effort="xhigh"` e ferramentas nativas de delegacao no contexto. Portanto, manter `ultra` na configuracao e deixar a CLI construir a requisicao; nao forcar o literal ultra no payload HTTP.

## Configuracao e uso

Requisitos: Python 3.11+, CLI Codex 0.166.0+ no PATH. Compatibilidade estrutural verificada na 0.166.0; versoes futuras precisam de nova verificacao. `install` e `check` nao geram conteudo.

```powershell
python -m proxy_ai.codex_cli check --from-docker
python -m proxy_ai.codex_cli install --from-docker
```

`--from-docker` consulta somente PROXY_API_KEY do container autorizado `chatgpt-codex-proxy`, capturada em memoria. Pode-se especificar `--container`. Sem essa opcao, exige CODEX_PROXY_BASE_URL e CODEX_PROXY_API_KEY no ambiente. A URL pode ser informada em `--base-url`; nunca passar a chave como argumento. Redirecionamentos sao recusados no preflight.

O instalador acrescenta `model_providers.videoforge_proxy` ao config.toml, preserva os bytes anteriores, cria um `config.toml.vf-backup-<id>` privado no mesmo diretorio e recusa provider/perfis conflitantes. E idempotente. Cria `vf_ultra.config.toml`, `vf_simple.config.toml`, `vf_code.config.toml`, `vf_complex.config.toml`, `vf_critical.config.toml`. Nenhum desses arquivos contem chave. Reexecutar install acrescenta o novo perfil Ultra a uma instalacao anterior, preservando os demais.

| Classe | Modelo | Esforco |
|---|---|---|
| ultra (padrao do lancador) | gpt-6-astra | ultra (modo nativo Codex) |
| simple | gpt-6-luna | low |
| code | gpt-6.1-sol | medium |
| complex | gpt-6.1-sol | high |
| critical (explicito) | gpt-6-astra | high |

```powershell
# AUTORIZA inferencia: abrir sessao interativa Astra/Ultra
python -m proxy_ai.codex_cli run --from-docker --execute
# Alternativa economica explicita:
python -m proxy_ai.codex_cli run --from-docker --task code --execute
# Engenharia mais complexa, sem trocar para Astra:
python -m proxy_ai.codex_cli run --from-docker --task complex --execute
# Astra somente por escolha explicita:
python -m proxy_ai.codex_cli run --from-docker --task critical --execute
```

O lancador verifica health/modelos e passa overrides `-c` que prevalecem sobre o projeto. Define concorrencia de agentes em 2, subagente padrao Luna/low, service_tier default, Responses/SSE, WebSocket desativado, retries HTTP/stream zero e idle timeout de 120 s. A delegacao fica sob controle do Codex em Ultra; nao existe loop de agentes criado pelo lancador. Uma sessao interativa pode fazer varias inferencias: `--execute` autoriza essa sessao, nao promete uma unica chamada. `--timeout` controla somente o preflight Python. Argumentos adicionais da CLI podem ser passados depois de `--`.

Os perfis tambem podem ser escolhidos com `codex -p vf_ultra` quando a chave ja estiver no ambiente. Nesse uso direto nao existe preflight do lancador. O comando `codex` sem perfil usa o provider global original e as configuracoes aplicaveis ao projeto (neste repositorio, Astra/Ultra). O seletor exibido no aplicativo nao comprova por si so que uma conversa existente esta roteada pelo proxy; esta integracao configura novas sessoes CLI.

`--fallback-original` permite abrir a configuracao original se o proxy/modelo estiver indisponivel antes da sessao. Sem essa flag, retorna erro. HTTP 401/403 e timeouts sao sanitizados; 429 nao e repetido. Apos iniciar Codex, qualquer codigo de erro retorna ao usuario sem outro provider, evitando duplicacao de trabalho/custo.

Para desfazer: encerrar sessoes proxy, restaurar o backup correto de config.toml (verificar alteracoes posteriores), e remover somente os cinco arquivos vf_*.config.toml criados por esta instalacao. O backup pode conter preferencias privadas e fica fora do Git. Nao apagar outros perfis ou providers.

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

Classificacao explicita e deterministica evita uma inferencia extra somente para escolher modelo. O SDK de texto TaskRunner conserva `code` como default auxiliar e nao implementa orquestracao Ultra; pedir ultra por esse cliente retorna orientacao para usar a CLI antes de inferir. Divisao e escalada nativas ficam a cargo do Codex/operador. Cache so e medido quando reportado; nao ha cache de respostas que reutilize codigo desatualizado. Tokens API nao equivalem aos creditos da assinatura.

## Evidencias e pendencias

- Suite inicial: 15 testes offline aprovados; suite atual: 40 aprovados, incluindo merge, perfis V2, limites, fallback, erros, Ultra e SSE simulado. No CI sem CLI instalada, os quatro testes nativos opcionais sao ignorados; os demais continuam sem rede. Houve um timeout intermitente de 30 s no teste opcional da CLI/Ultra simulada em uma rodada; a causa nao foi determinada, o diagnostico de timeout foi melhorado e a rodada completa seguinte passou em 8,49 s. Nenhuma inferencia real foi repetida por esse evento.
- CLI 0.166.0: perfil V2 aceito em `debug prompt-input`, sem inferencia; nao publicar o prompt interno.
- CLI real contra servidor SSE simulado: uma requisicao `/v1/responses`, bearer de teste, stream=true, Sol, resposta MOCK_OK. Demonstra protocolo da CLI, nao inferencia pelo proxy real.
- CLI real contra HTTP 429 e 401 simulados: encerrou com erro depois de uma unica requisicao em cada caso, sem retry.
- CI da implementacao: [execucao offline 43603791906](https://github.com/HelioConde/codex/actions/runs/43603791906) concluiu success. Alteracoes publicadas na [PR #1](https://github.com/HelioConde/codex/pull/1).
- Proxy Docker real: GET `/health` HTTP 200, status ok, uma conta configurada; GET `/v1/models` inclui gpt-6-luna, gpt-6.1-sol, gpt-6-astra. Nenhuma inferencia nesses GETs.
- Actions anteriores confirmadas success: [health 43601574401](https://github.com/HelioConde/codex/actions/runs/43601574401), [models 43601760640](https://github.com/HelioConde/codex/actions/runs/43601760640), [texto 43601944682](https://github.com/HelioConde/codex/actions/runs/43601944682). O pedido relata 17 tokens de entrada e 10 de saida nessa inferencia Astra; nao e medicao nova desta implementacao.

**Inferencia real validada em 14/11/2026:** depois de autorizacao explicita do proprietario, `python -m scripts.smoke_codex_proxy --execute` encerrou com codigo 0 usando CLI 0.166.0, gpt-6.1-sol, esforco low e o proxy Docker existente. A funcao soma retornada correspondeu a AST esperada, sem executar codigo gerado. Isso comprova uma tarefa curta de geracao de codigo pelo transporte nativo da CLI; nao comprova qualidade em problemas complexos ou todas as ferramentas/agentes/modelos.

| Medicao informada pela CLI | Tokens |
|---|---:|
| Entrada total (inclui cache) | 12335 |
| Entrada em cache (subconjunto) | 9344 |
| Entrada fora do cache (diferenca calculada) | 2991 |
| Saida | 15 |

Creditos da assinatura: desconhecidos. Nenhum percentual de economia foi medido. A entrada elevada para uma funcao pequena evidencia o custo do contexto interno da CLI; tarefas textuais simples podem usar o cliente direto/TaskRunner para evitar esse contexto, mas essa alternativa ainda nao teve comparacao pareada nesta implementacao. O teste nao realizou imagens nem chamadas Astra. Fallback, 401/429 e limites permanecem validados em simulacao, sem provocar falhas reais deliberadas.

O teste esta preparado em [scripts/smoke_codex_proxy.py](../scripts/smoke_codex_proxy.py). `python -m scripts.smoke_codex_proxy` apenas informa o gate, sem acessar Docker/rede. **Somente apos autorizar cota**, `python -m scripts.smoke_codex_proxy --execute` abre uma sessao CLI isolada/efemera Sol/low com timeout de 120 s e sem retries, pede uma funcao soma sem ferramentas e compara sua AST sem executar codigo gerado. Imprime apenas validacao e contadores numericos, nunca logs internos. O prompt pede uma resposta unica; o ciclo interno da CLI nao e um teto garantido de requisicoes/tokens. Creditos de assinatura permanecem desconhecidos. Nao executar esse comando gerativo no CI.

**Teste real Astra/Ultra, tambem em 14/11/2026 e autorizado:** `python -m scripts.smoke_codex_proxy --task ultra --execute` encerrou com codigo 0, modelo gpt-6-astra, selecao ultra e AST correta. Uso reportado: **12312 tokens de entrada, 0 em cache, 15 de saida**. O teste comprova inferencia/streaming com o perfil Ultra; a tarefa curta nao exigiu execucao de subagentes, cuja presenca no protocolo foi verificada em simulacao. Nao medir economia comparando diretamente esse teste com Sol: modelo, esforco e cache diferem. Creditos consumidos continuam desconhecidos.

O proxy usa interfaces nao oficiais e pode deixar de funcionar. Compatibilidade tecnica nao comprova autorizacao contratual; usar somente conta propria/autorizada e respeitar termos, cotas e autenticacao. O fallback preservado e a alternativa operacional, sem contornar limites.
