# Agentes, delegação, pesquisa e governança editorial

## Princípio

A arquitetura de múltiplas IAs é uma **equipe com funções delimitadas**, não uma sequência de agentes que repetem o mesmo pensamento. O **Gerente do Canal** seleciona oportunidades e distribui trabalho; o **Subgerente** audita qualidade, consistência, custo e desempenho; cada especialista entrega artefatos verificáveis.

## Equipe proposta

| Função | Responsabilidade | Saída |
|---|---|---|
| Pesquisador | métricas YouTube, tendências, público, concorrentes, fontes | insights com data e URLs |
| Gerente do Canal | priorizar pautas e definir formato, duração, público e intenção | brief editorial |
| Subgerente | ranquear qualidade dos agentes, identificar erros, auditar custos e gates | scorecard e aprovação/reprovação |
| Roteirista | gancho, estrutura narrativa, roteiro próprio | script versionado |
| Diretor de cena / storyboard | sequência, enquadramentos, movimento, ritmo, continuidade | scenes.json |
| Diretor de arte | guia visual, consistência de estilo e personagens | style bible e referências |
| Artista de imagens | cena-mãe, planos, personagens, objetos, ajustes | assets com proveniência |
| Animador / rigger | rig real, deformações, keyframes, câmera | spec de animação |
| Voz / áudio | locução, trilhas autorizadas, mixagem | WAV/MP3 sincronizados |
| Editor / render | composição com Remotion, legendas, exportação | MP4 validado |
| SEO / publicação | título, descrição, tags, miniatura e upload | metadados e status |
| QA / direitos | revisar duplicação, artefatos, legibilidade e licença | relatório de gates |

Essas são **responsabilidades conceituais**; não representam confirmação de agentes implementados. Não adicionar agentes custosos antes de validar um pipeline mínimo de ponta a ponta.

## Pesquisa de oportunidades

- Analisar métricas disponíveis via YouTube API/Analytics: retenção, visualizações, CTR, inscritos por visualização engajada, duração, formatos e temas.
- Levantar tendências com fontes e datas, sem assumir que "o que está em alta" vale para todos os canais.
- Investigar os vídeos que deram certo **no próprio canal** antes de copiar estratégias externas.
- Classificar pauta como **evergreen, trend, seasonal ou experiment**.
- Registrar hipótese, nicho, faixa etária, tamanho de vídeo, estilo visual e custo esperado.
- Comparar roteiro e tese com o histórico: não repetir vídeos, ganchos, estruturas ou pautas quase idênticas.
- Focar originalidade; em canais de anime, considerar direitos de terceiros e preferir ilustrações e narração próprias.
- O usuário pediu que pesquisas pesadas sejam produzidas/orientadas pelo ChatGPT e enviadas aos agentes, em vez de depender de um proxy sobrecarregado para redescobrir tudo.

## Organização por canal no VideoForge-IA

A estrutura abaixo é **sugestão para dados do projeto de vídeo**, não ordem para reorganizar o repositório Codex:

~~~text
canal/
  <id-do-canal>/
    config/
    pesquisa/
    historico/
    roteiros/
    personagens/
    estilos/
    videos/
      <video-id>/
        brief.md
        scenes.json
        images/
        layers/
        rig/
        audio/
        renders/
        qa/
        costs.json
        provenance.json
~~~

Os projetos de canal, inclusive Alchemy Lab, Otaku Multicena e os demais, devem manter regras e histórico próprios. Evitar reproduzir conteúdos já publicados. Para a série **Fofinho/Fofinhos**, preservar a exceção editorial já definida: **não automatizar nova pauta, continuação, roteiro ou geração sem solicitação explícita**; somente registrar métricas se autorizado.

## Contrato entre agentes

Cada passagem deve ter:
- **entrada mínima:** IDs, caminhos, versão do brief e artefatos;
- **saída estruturada:** JSON/YAML ou arquivo, não conversa ambígua;
- **critérios de aceite:** checklist de QA, formato, prazo e custo;
- **motivos de recusa:** originalidade insuficiente, asset inconsistente, orçamento excedido;
- **rastreamento:** task_id, versão do modelo, timestamps, custo real, links de artifacts;
- **independência de provedores:** interface comum, suporte a diferentes APIs e fallback planejado.

~~~json
{
  "video_id": "alchemy-lab-kael-001",
  "channel_id": "alchemy-lab",
  "stage": "storyboard",
  "depends_on": ["brief-v1", "visual-bible-v1"],
  "owner_role": "diretor_de_cena",
  "artifacts_out": ["scenes.json"],
  "quality_gates": ["originalidade", "estilo", "orcamento"],
  "approved": false
}
~~~

## Subgerente: avaliação dos trabalhadores

Registrar por agente: qualidade técnica, aderência ao estilo, erros encontrados pelo QA, taxa de retrabalho, custo por entrega aceita, prazo e capacidade de aprender com correções. Pontuação só é útil se baseada em evidência, e não em elogios de outros agentes. Agente com bom resultado pode receber tarefas mais complexas; não adicionar mais agentes sem ganho observável.

## Automação no GitHub

- **Verificações sem IA** podem ser periódicas e frequentes: status de Actions, integridade de artefatos, hashes e qualidade do MP4.
- **Pesquisa ou geração paga** deve ser acionada por demanda e respeitar autorização/orçamento; não automaticamente a cada push.
- Sempre separar "workflow iniciou", "terminou sem erro" e "vídeo gerado/publicado" — são fatos distintos.
- Persistir progresso e retomar de checkpoint para não gerar as mesmas imagens duas vezes.
- Evitar modo private-quota-live quando já se mostrou problemático; usar rotas efetivamente autorizadas, sem contornar limitação de cota.

## Decisões humanas

Pauta final, identidade visual, uso de marca/personagem, gastos acima do limite e publicação pública são decisões sujeitas às regras específicas do canal. Os gates evitam que autonomia vire publicação de imagens erradas ou conteúdo duplicado.
