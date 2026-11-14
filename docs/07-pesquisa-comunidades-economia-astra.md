# Economia de tokens Astra/Codex — pesquisa aplicada da comunidade

**Data:** 14/11/2026 · **Origem:** pesquisa aprofundada em GitHub, issues, Reddit, Hacker News e documentação oficial.

## Resumo executivo

GPT-6 Astra é o modelo; **Ultrafast é um modo de velocidade**, não um segundo modelo chamado Astra Ultra. Referências oficiais citam uso incluído a 8× e créditos a 6× Standard em situações específicas de planos Pro/Enterprise. Isso **não significa** que esses fatores sejam a taxa da conta do usuário: verificar Settings → Usage. Para economia, não usar Ultrafast como padrão.

Os maiores desperdícios observados pela comunidade são loops modelo→ferramenta→modelo, polling de subagentes, contexto enorme, logs de ferramentas e cache que continua processando milhões de tokens.

## Evidências concretas

| Projeto ou relato | Resultado citado | Limitações |
|---|---|---|
| [TokenEconomizer](https://github.com/microsoft/TokenEconomizer) (Microsoft Research/UC Berkeley) | Redução média de custo de **18,4% a 30,9%** em cinco combinações agente/modelo no SWE-Bench | Não testado no VideoForge-IA; conferir suporte à versão da CLI |
| [Lattice](https://github.com/moulwyse/lattice/blob/main/docs/evidence/owner-run-gpt-6-astra.md) | **76,3%** menos tokens frescos em fixture pequena Astra: 16.872→4.005 | Cinco arquivos, benchmark do mantenedor e condições não perfeitamente simétricas |
| [Compressoor](https://github.com/M4cs/compressoor) | Compressão textual ~27–60%; **apenas 0,1%** de economia total em teste curto real | Overhead de contexto superou compressão |
| [HN: compressão de saída de ferramentas](https://news.ycombinator.com/item?id=49911910) | Autor relata **29,6%** menos tokens | Sem benchmark independente; risco de remover erro importante |
| [Reddit: quota Astra vs Sol](https://www.reddit.com/r/codex/comments/1wgs7yo/your_codex_logs_track_your_quota_on_every_turn_i/) | ~3,6× quota/token para Astra na amostra do autor | Não é taxa oficial, apenas uma conta |
| [Reddit: polling de agentes](https://www.reddit.com/r/codex/comments/1wa9c9d/i_investigated_why_gpt6_astra_burns_quota_so_fast/) | 47 consultas sem mudança de estado; ~7,13 milhões de tokens do agente pai | Caso específico |
| [Codex issue #42357](https://github.com/openai/codex/issues/42357) | 96,8% input cacheado, mesmo assim uso elevado | Relato não comprova bug de cobrança |
| [Codex issue #37305](https://github.com/openai/codex/issues/37305) | Compaction em versão específica teria elevado input não-cacheado em ~70% | Bug relatado em versão e configuração específicas |

**Nunca somar percentuais ou apresentar resultados externos como economia comprovada do usuário.**

## Técnicas selecionadas para o VideoForge-IA

1. **Sol Standard como padrão para código normal; Astra Standard sob escalada explícita.** Luna para subagentes de tarefas triviais, se suportada.
2. **Orçamento de ferramentas:** iniciar com tool_output_token_limit=8000, garantindo que trechos críticos de erros permaneçam disponíveis.
3. **Dois subagentes simultâneos** como hipótese inicial; evitar polling pelo Astra. Usar tarefas independentes e passar resultados apenas quando mudarem.
4. **AGENTS.md curto e estável quando possível.** Evitar carregar manuais completos em cada tarefa. No VideoForge-IA, qualquer redução precisa preservar o manual prioritário de animação e regras de QA — **não cortar instruções obrigatórias automaticamente**.
5. **Prompt caching:** manter prefixos, ferramentas e parâmetros estáveis; cache reduz custo de API quando disponível, mas não zera consumo da franquia Work/Codex.
6. **Repo map e micro-skills:** atalhos para símbolos, testes e scripts sem reexploração de código; úteis quando economizam múltiplas buscas.
7. **Ferramentas determinísticas:** FFprobe, testes, JSON Schema, validação de camadas/alpha, linter e render de prévia não devem chamar Astra por padrão.
8. **Triage → pacote mínimo → escalada:** entregar arquivo relevante, trecho de erro, comando reproduzível, resultado esperado e teste de aceite.
9. **Qualidade antes de economia:** medir tarefa aprovada/crédito, taxa de bugs, retrabalho, tokens, turns e cache. A/B com mesmas fixtures.
10. **Sem proxy interceptador terceiro sem auditoria.** Verificar licenças, segurança, compatibilidade, custo e riscos de quebrar cache; nunca contornar limites de serviço.

## Ferramentas para avaliar, NÃO instaladas

- [TokenEconomizer: README e plugin](https://github.com/microsoft/TokenEconomizer/blob/main/plugin/README.md): microskills, toolprune, loopguard, repo map. A pesquisa identificou suporte declarado a Codex 0.153.1–0.164.0 na data; confirmar versão atual.
- [Lattice](https://github.com/moulwyse/lattice): execução determinística fora do loop de modelo com contexto delimitado e testes.
- [RepoSpend](https://github.com/mehmetdemircs/RepoSpend): leitura local de sessões e consumo por repo.
- [codex-monitor](https://github.com/falyx6851-byte/codex-monitor): relatórios locais de tokens/custos estimados.
- [Compressoor](https://github.com/M4cs/compressoor): somente experimento isolado; resultado real pode ser insignificante.

## Configuração conservadora de referência

Os arquivos .codex/config.toml em ambos os projetos foram criados como configuração inicial de **Codex CLI por projeto**. Eles **não alteram** o proxy privado, modelos disponíveis na conta, teto de gastos ou configuração de APIs de mídia.

~~~toml
model = "gpt-6.1-sol"
model_reasoning_effort = "medium"
tool_output_token_limit = 8000

[agents]
enabled = true
max_concurrent_threads_per_session = 2
default_subagent_model = "gpt-6-luna"
default_subagent_reasoning_effort = "low"
~~~

São controles documentados pela [referência oficial](https://learn.chatgpt.com/docs/config-file/config-reference); 8.000 e 2 são **parâmetros de experimento**, não defaults oficiais. Aplicação requer cliente compatível, modelos disponíveis e configuração de confiança de projeto. Para escalar pontualmente: executar a CLI em modo Standard selecionando o modelo Astra com parâmetro --model gpt-6-astra.

## Protocolo para medir a economia real

1. **Baseline:** executar 5 tarefas representativas, com versões de código e testes congelados: rig/capa, máscara RGBA, Remotion, FFprobe e workflow Actions (sem mídia paga).
2. Medir modelo, reasoning effort, tier, tokens frescos/cacheados/output, tool calls, tempo, resultado do teste, QA e custo/quota observado. Guardar só os agregados, nunca JSONL bruto no GitHub.
3. Alterar **uma variável por vez**: modelo padrão, tamanho de tool output, agentes, repo map ou TokenEconomizer.
4. Repetir as mesmas tarefas; comparar custo **e** conclusão aprovada. Calcular economia = 1 - (custo otimizado / custo base).
5. Reverter ajustes que aumentem erros, retrabalho ou perda de informação relevante.
6. Não aplicar plugins ou interceptadores de terceiros diretamente em produção antes de auditar código/versão/permissões.

## Pacote compacto de escalada

~~~json
{
  "task_id": "rig-cape-qa-001",
  "goal": "corrigir rosto transparente na transição da capa",
  "affected_files": ["motion-remotion/arquivo-relevante.tsx"],
  "error_excerpt": "apenas a linha de erro relevante",
  "reproduce": "comando de teste sem API paga",
  "acceptance": ["rosto sempre opaco", "rig articulado preservado"],
  "restrictions": ["sem novas imagens", "sem publicação", "sem gasto autorizado"]
}
~~~

## Fontes de referência

- [Uso e cota de Astra/Ultrafast](https://help.openai.com/en/articles/20001516-managing-usage-with-gpt-6-astra-in-work-and-codex)
- [Referência de config.toml](https://learn.chatgpt.com/docs/config-file/config-reference)
- [Exemplo de config.toml](https://learn.chatgpt.com/docs/config-file/config-sample)
- [Prompt caching](https://developers.openai.com/api/docs/guides/prompt-caching)
- [Código do carregamento de AGENTS.md](https://github.com/openai/codex/blob/main/codex-rs/core/src/agents_md.rs)
- [Discussão de contexto inicial](https://github.com/openai/codex/discussions/12668)
- [Issue: AGENTS.md duplicado após edição](https://github.com/openai/codex/issues/43295)
- [Issue: sessão retomada após longa pausa](https://github.com/openai/codex/issues/56050)

**Pendente:** medir consumo real da conta; testar A/B; avaliar ferramentas terceiras; melhorar AGENTS sem perder manual; adaptar o proxy existente com limites reais mediante nova revisão; nenhuma geração de vídeo nem cobrança foi acionada nesta aplicação.

## Medição local opcional, sem plugins pagos

Este repositório inclui [scripts/resumo_codex.py](../scripts/resumo_codex.py), um resumo **offline** de sessões JSONL do Codex. Não lê para fora nem publica mensagens/prompt; contabiliza apenas os campos de uso e considera o maior contador cumulativo por arquivo para evitar somar snapshots repetidos. Requer Python 3.10+ e usa somente biblioteca padrão.

~~~bash
# A partir da raiz do repo codex, no computador que possui as sessões
python scripts/resumo_codex.py --json
# Ou indicar uma pasta local específica
python scripts/resumo_codex.py "/caminho/local/codex/sessions"
# Testes sem conexão e com fixtures artificiais
python -m unittest discover -s tests -v
~~~

Limitações: o Codex pode alterar o formato de JSONL; reinícios de contadores dentro do mesmo arquivo podem exigir tratamento adicional; chamadas sem evento cumulativo ficam ausentes; esta ferramenta **não calcula valor em dinheiro, quota de assinatura ou custo real da API**. Não adicionar seus arquivos JSONL reais ao GitHub. Guardar apenas agregados e resultados dos testes aprovados.
