# Economia de tokens, créditos e operação do Codex Proxy

**Origem:** discussão sobre uso de Astra Ultra, segunda IA auxiliar, economia no Codex e dificuldades com o proxy no VideoForge-IA.

## O que significa "Astra Ultra"

- A pesquisa consolidada em 14/11/2026 não confirmou um produto oficial chamado **Astra Ultra**. Distinguimos **GPT-6 Astra** de **Ultrafast**, que é modo de velocidade/cobrança do Codex/Work.
- Referência pesquisada: Ultrafast pode consumir várias vezes a taxa de Standard (referência: aproximadamente **6×** em um modelo de cobrança por créditos e **8×** em determinada franquia Pro). **Não pressupor que esses multiplicadores se apliquem à conta atual; verificar plano e rate card antes de decidir.**
- Regra operacional: **não selecionar Ultrafast por padrão para economizar**. Astra Standard só em tarefas de engenharia complexas, diagnosticadas como necessárias.
- Os preços de API e do Codex não são intercambiáveis: créditos por trabalho, assinaturas e cobrança por tokens podem seguir regras diferentes.

## Divisão de responsabilidades entre duas ou mais IAs

| Complexidade | Agente/ferramenta | Resultado esperado |
|---|---|---|
| Pesquisa de pautas e métricas | pesquisa externa + modelo barato | relatório curto, fontes e evidências |
| Gancho, roteiro, CTA, títulos, descrição, tags | modelo econômico | arquivos estruturados, variantes pontuais |
| Storyboard, prompts e planejamento de cenas | modelo econômico | JSON/YAML validado |
| Imagens e inpainting | gerador especializado/local | imagens versionadas aprováveis |
| Rig, câmera, keyframes | algoritmos/Remotion/Three.js | sequência determinística |
| Tomadas generativas | API de vídeo especializada | poucos clipes selecionados |
| Voz, legendas e render | TTS, ASR, Remotion e FFmpeg | MP4 e artefatos de QA |
| Bug simples, configuração e testes | ferramentas locais/modelo econômico | diff pequeno e testes |
| Arquitetura ou bug difícil e persistente | Codex com Astra quando necessário | correção focalizada e teste verificável |

**Antipadrão:** pedir a um modelo barato que produza um relatório enorme e enviar o relatório integral ao Astra. O ganho vem de reduzir o contexto e fazer o Astra agir sobre o problema exato.

## Fluxo de escalonamento

1. Identificar a tarefa, arquivos relevantes, restrições e orçamento.
2. Rodar verificações determinísticas: testes, TypeScript, lint, FFprobe, validação de JSON, inspeção de logs e hashes.
3. Se o problema persistir, pedir a um modelo econômico um resumo de até alguns parágrafos com **sintoma, causa provável, evidência e mudança mínima proposta**.
4. Escalar ao Codex/Astra somente com contexto mínimo. Preservar links para referências grandes, não colar imagens e históricos inteiros.
5. Verificar a correção por teste automático; registrar resultado, número de tentativas e custo.

## Estrutura recomendada para uma chamada ao agente

~~~json
{
  "task_id": "fix-remotion-render-001",
  "goal": "corrigir falha de renderização em cena específica",
  "component": "render/remotion",
  "model_tier": "economico",
  "files": ["caminho/do/arquivo.tsx"],
  "error_excerpt": "mensagem curta e relevante",
  "expected_artifact": "patch e teste executado",
  "budget": {
    "max_attempts": 2,
    "max_tokens_input": 12000,
    "max_tokens_output": 3000
  },
  "escalation": "somente se teste continuar falhando"
}
~~~

Os números acima são **exemplo de política interna**, não prova de que a API do proxy respeita esses parâmetros. Implementar limite real por provedor, tempo, concorrência e teto de cobrança.

## Economia prática

- Manter **AGENTS.md** conciso e apontar para documentação específica; não anexar todos os documentos a cada solicitação.
- Instruções comuns podem ser mantidas no começo do prompt para aproveitar caching quando disponível; medir tokens de cache retornados.
- Separar **contexto estável** (política, estilo, IDs) de **contexto variável** (cena, erro, decisões atuais).
- Sumarizar logs longos e enviar apenas stack trace, arquivo alterado e porções relevantes.
- Enviar hashes e caminhos de assets; não reanalisar a mesma imagem em toda etapa.
- Reutilizar resultado da pesquisa por canal; não pesquisar 100 vídeos e 300 ideias a cada render.
- Não disparar pesquisas/generations pagas em eventos GitHub **push** indiscriminadamente.
- Fazer build de runner Docker/GHCR com dependências Go/Node/FFmpeg/Remotion para não reinstalar tudo a cada job.
- CI sem IA antes de chamadas pagas; pipeline deve conseguir gerar MP4 técnico simples sem nenhum token.
- Medir **custo por vídeo pronto**, não apenas custo por chamada ou quantidade de tokens.

## Proxy central e HTTP 429

Problema histórico: chamadas ao Codex Proxy sofreram **HTTP 429**, sem diagnóstico de cota confirmado inicialmente. Tratar 429 como possível limitação de taxa, cota, orçamento, concorrência ou credenciais — **não assumir que diminuir texto resolverá**.

Procedimento:
1. Anotar horário, rota, modelo, código/status, identificador da chamada (sem expor token) e resposta sanitizada.
2. Consultar rate limits, créditos, cota e escopo real da conta/ambiente.
3. Reduzir concorrência por conta/modelo; fila com semáforo e idempotência.
4. Usar exponential backoff com jitter **apenas para falhas transitórias**; parar após limite de tentativas.
5. Fallback somente entre provedores/modelos previamente permitidos e com licença adequada.
6. Nunca repetir automaticamente uma chamada de mídia paga sem checar se o job anterior gerou artefato.
7. Guardar métricas de tentativa, tokens, latência, custo e motivo do fallback.

**Segurança:** API keys, tokens, cookies e configurações privadas ficam em GitHub Secrets/Environments; não gravar credenciais, prompts com dados sensíveis nem dumps brutos de conta neste repositório público. Relatórios potencialmente sensíveis devem ter acesso restrito ou proteção adequada.

## Indicadores de eficácia

- Tokens de entrada/saída e cache por modelo e tarefa.
- Créditos ou US$ consumidos por vídeo publicado e por vídeo reprovado.
- Taxa de fallback e de HTTP 429.
- Número de chamadas pagas e rejeições por vídeo.
- Percentual das tarefas resolvidas sem Astra.
- Tempo para chegar a um MP4 aprovado.
- Erros reincidentes por workflow e custo de retrabalho.

## Referências de verificação

- [Uso de GPT-6 Astra no Codex/Work](https://help.openai.com/en/articles/20001516-managing-usage-with-gpt-6-astra-in-work-and-codex)
- [Preços de API OpenAI](https://developers.openai.com/api/docs/pricing)
- [Prompt caching](https://developers.openai.com/api/docs/guides/prompt-caching)
- [Revisão de skills e prompts para GPT-6 Astra](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra)

> Atualizar preços e multiplicadores antes de qualquer contratação: foram consultados no contexto da pesquisa de novembro/2026.
