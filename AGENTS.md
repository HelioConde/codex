# Orientações para agentes — repositório codex

Este repositório documenta economia de tokens e **implementa um cliente Python reutilizável** de IA de texto e imagem para o mesmo proxy do [VideoForge-IA](https://github.com/HelioConde/VideoForge-IA). O pipeline audiovisual continua no VideoForge-IA.

## Antes de executar qualquer tarefa

1. Ler [README.md](README.md) e [visão geral](docs/00-visao-e-decisoes.md).
2. Consultar **somente** o documento pertinente: custos/proxy, agentes, pipeline, animação, ferramentas ou roadmap.
3. Distinguir **decisão**, **proposta**, **exemplo** e **implementação verificada**.
4. Nunca declarar teste, animação, geração, MP4 ou publicação como concluídos sem evidência do projeto de origem.
5. Manter conteúdos de canais isolados; nunca repetir pauta, vídeo, arte ou prompt já aprovado sem justificativa.
6. Proteger credenciais e dados privados. **Este repositório é público.** Nunca adicionar tokens, cookies, credenciais, payloads secretos ou dados pessoais sensíveis.
7. Não iniciar chamadas de IA paga, contratar APIs nem criar workflows com cobrança recorrente sem política de custo e autorização.
8. Não usar Astra/Ultrafast para tarefas rotineiras; modelo barato + testes determinísticos primeiro.
9. Não substituir **animação articulada** por movimentação do PNG inteiro quando a especificação exige rig.
10. As chamadas de `proxy_ai text` e `proxy_ai image` somente ocorrem com `--execute`; não gerar conteúdo em CI/push ou testes.
11. O proxy não é API oficial do Codex; respeitar autorização e limites, não usar contas de terceiros, não automatizar reintentos após HTTP 429.
12. Em uma alteração: preservar links e decisões anteriores; acrescentar data, fonte e justificativa; validar Markdown e referências.
13. CLI 0.166.0 usa perfis V2 em `<nome>.config.toml` no CODEX_HOME; nao inserir tabelas legadas `[profiles]`. Usar `python -m proxy_ai.codex_cli check/install/run`; `run` exige `--execute` e usa Sol por padrao. Preservar backup e configuracao OpenAI original.
14. Fallback somente no preflight e com `--fallback-original`; nunca reenviar tarefa apos iniciar inferencia. Limites de TaskRunner sao de tokens API observados, nao de creditos nem teto garantido de faturamento. Aprovacao de resultado so depois de revisao.

## Documentos

- [00 — Visão e decisões](docs/00-visao-e-decisoes.md)
- [01 — Economia Codex/Proxy](docs/01-economia-codex-e-proxy.md)
- [02 — Agentes e pesquisa](docs/02-agentes-pesquisa-e-orquestracao.md)
- [03 — Pipeline audiovisual](docs/03-pipeline-youtube.md)
- [04 — Rig e Remotion](docs/04-animacao-rig-remotion.md)
- [05 — Ferramentas, custos e direitos](docs/05-ferramentas-custos-direitos.md)
- [06 — Roadmap e validação](docs/06-roadmap-e-validacao.md)
- [07 — Pesquisa em repositórios e comunidades sobre economia Astra](docs/07-pesquisa-comunidades-economia-astra.md)
- [08 — Integrar IA de texto e imagem via proxy VideoForge](docs/08-proxy-ia-texto-codex.md)
- [Configuração experimental Codex CLI](.codex/config.toml)
- [Template global para usar proxy como provider Codex](config/codex-proxy.user.toml.example)
- [10 — Codex CLI, perfis V2 e evidencias locais](docs/10-codex-cli-proxy.md)
