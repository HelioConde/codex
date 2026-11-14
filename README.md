# Codex — estratégia de economia de IA e produção audiovisual para YouTube

Repositório de **ideias, pesquisas e ferramentas reais** sobre uso eficiente do Codex e do proxy de IA compartilhado com VideoForge-IA, para roteiros, planejamento, análise e geração de imagens.

**Atualizado em:** 14/11/2026  
**Status:** cliente Python de IA de texto/imagem e workflow manual implementados; conexão com credenciais reais ainda pendente de validação. A produção de vídeo permanece no VideoForge-IA.  
**Projeto principal de execução:** [VideoForge-IA](https://github.com/HelioConde/VideoForge-IA).  
**Projeto relacionado:** [AutoEditorVideo](https://github.com/HelioConde/AutoEditorVideo).

## Objetivo

Criar conteúdo audiovisual de qualidade para YouTube **sem desperdiçar tokens, créditos ou gerações de mídia**. Dividir o trabalho entre IAs econômicas, modelos especializados, renderização determinística e Codex para engenharia complexa.

O foco desta documentação é **YouTube — imagens, personagens, rig 2D, animação, vídeo, roteiros, agentes e automação**, e não um projeto de jogo.

## Proxy IA do VideoForge no Codex

O diretório [proxy_ai](proxy_ai) implementa chamadas de **IA de texto pela rota `/v1/responses`**, imagens, saúde e catálogo de modelos. Não reimplementa nem duplica o servidor: reutiliza o proxy existente. Somente `--execute` autoriza chamadas gerativas.

```powershell
python -m proxy_ai health
python -m proxy_ai models
python -m proxy_ai text --prompt-file outputs/brief.txt --execute
```

Para executar, configure localmente `CODEX_PROXY_BASE_URL` e `CODEX_PROXY_API_KEY` e leia o [guia de integração](docs/08-proxy-ia-texto-codex.md). O [workflow manual do GitHub](.github/workflows/proxy-ia-manual.yml) também oferece texto/imagens após configurar Secrets no repo `codex`. É possível usar o proxy como provider na CLI Codex por meio do [template de configuração global](config/codex-proxy.user.toml.example), sem inserir chaves no repositório. **O cliente Python usa modelos e cotas reais da conta; não fornece acesso ilimitado.**

## Índice de todas as ideias consolidadas

1. [Visão geral e decisões](docs/00-visao-e-decisoes.md) — prioridades, decisões já discutidas e escopo.
2. [Economia de tokens, Astra e Codex Proxy](docs/01-economia-codex-e-proxy.md) — modelos, custo, caching, contexto mínimo, HTTP 429 e segurança.
3. [Agentes, pesquisa e orquestração](docs/02-agentes-pesquisa-e-orquestracao.md) — Gerente, Subgerente, especialistas, métricas YouTube e distribuição de trabalho.
4. [Pipeline para YouTube](docs/03-pipeline-youtube.md) — pesquisa → storyboard → imagens → camadas → rig → áudio → Remotion → MP4 → publicação; inclui exemplo JSON do dorama MMORPG.
5. [Manual principal de animação 2D com rig e Remotion](docs/04-animacao-rig-remotion.md) — cena-mãe, pixels originais, máscaras, articulação, cape/hair, Three.js, caso Anya e QA.
6. [Ferramentas, preços estimados e direitos](docs/05-ferramentas-custos-direitos.md) — ComfyUI, Pika, Runway, Kling, Wan, Luma, TTS, referências oficiais e simulações de custo.
7. [Roadmap e validação](docs/06-roadmap-e-validacao.md) — prioridades, gates, critérios objetivos, custos e pontos ainda em aberto.
8. [Pesquisa em comunidades: economias reais no Astra/Codex](docs/07-pesquisa-comunidades-economia-astra.md) — TokenEconomizer, Lattice, cache, logs, subagentes, configurações e plano de medição.
9. [Configuração experimental Codex CLI](.codex/config.toml) — Sol por padrão e limites iniciais de subagentes e ferramentas.
10. [Resumo local de tokens Codex](scripts/resumo_codex.py) e [testes de validação](tests/test_resumo_codex.py) — auditoria offline de contadores JSONL sem enviar prompts para a rede.
11. [Integração do proxy como IA de texto e imagem](docs/08-proxy-ia-texto-codex.md) — cliente, Codex CLI, GitHub Actions, credenciais e limites.
12. [AGENTS.md](AGENTS.md) — instruções que agentes devem ler antes de consultar ou alterar estes registros.

## Regras essenciais

- **Modelo econômico primeiro** para pauta, pesquisa, roteiro, prompts, storyboard e metadados; Codex/Astra só para engenharia que realmente exija o modelo caro.
- **Não tratar Ultrafast como economia:** verificar tabela de créditos vigente e evitar modo caro por padrão.
- **Não repetir trabalho ou conteúdo:** pesquisar histórico de cada canal, reaproveitar resultados e impedir vídeos/temas duplicados.
- **Imagem aprovada → camadas consistentes → rig real → Remotion.** Não mover um PNG inteiro quando olhos, cabelo, capa ou braços devem ter movimentos próprios.
- **Aprovação visual antes de API de vídeo paga.** Preferir imagens animadas/parallax e poucos clipes generativos selecionados.
- **Checkpoints, métricas e QA obrigatório.** MP4 reproduzível, consistência visual, direitos, custo por vídeo e evidência de publicação.
- **Sem secrets no GitHub público** e sem iniciar despesas ou publicação automaticamente sem controles aplicáveis.

## Como manter estas notas

Nova ideia ou decisão relevante deve ser incorporada ao capítulo correspondente, com data e distinção entre **ideia**, **decisão**, **teste** e **resultado comprovado**. A implementação e a execução real continuam sob responsabilidade do repositório de produção. Antes de trabalhar, agentes devem consultar [AGENTS.md](AGENTS.md).

> **Nota:** o catálogo de ferramentas e valores monetários retrata uma pesquisa em 14/11/2026 e deve ser revalidado antes de contratar qualquer serviço.
