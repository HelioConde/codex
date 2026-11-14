# Registro de ideias e decisões — Codex + produção de YouTube com IA

**Data de consolidação:** 2026-11-14  
**Estado:** decisões e propostas de arquitetura; este repositório documenta ideias, não comprova sua implementação em VideoForge-IA.  
**Projetos relacionados:** [VideoForge-IA](https://github.com/HelioConde/VideoForge-IA), [AutoEditorVideo](https://github.com/HelioConde/AutoEditorVideo) e canais de YouTube geridos pelo usuário.

## Objetivo central

Diminuir gastos e consumo de tokens/créditos do Codex, sobretudo ao usar **GPT-6 Astra** e modos acelerados, sem reduzir a qualidade da criação de imagens, animações e vídeos destinados ao YouTube. Em vez de uma única IA fazer todas as etapas, dividir tarefas entre agentes/modelos e ferramentas especializadas.

O objetivo imediato **não é criar um jogo no Godot**: é usar IA para produzir **conteúdo audiovisual para YouTube**, com automação confiável, qualidade visual, roteiros próprios e custo controlado.

## Princípios acordados

1. **A IA barata faz o trabalho repetitivo; a IA cara resolve o difícil.** Pesquisa organizada, seleção de pauta, roteiro inicial, prompts, JSON de cenas, títulos e descrições não devem consumir Astra por padrão.
2. **Codex é engenheiro e depurador, não o motor de cada vídeo.** Usá-lo para construir e corrigir código, agentes, workflows, integrações, QA e automação. Executar o pipeline pronto sem invocar um agente de código a cada cena.
3. **Duas IAs não significam dois custos menores automaticamente.** A segunda IA deve reduzir o contexto que chega ao modelo caro; não duplicar análise, texto ou geração.
4. **Gerar a cena completa primeiro; separar depois os elementos animáveis.** Preservar identidade visual, personagem, cenário e objetos, em vez de criar cada elemento sem referência consistente.
5. **Rig real em vez de deslocar um PNG inteiro.** Cabeça, braços, cabelos, capa, olhos e objetos precisam de articulação, malha ou controles apropriados quando a cena pedir.
6. **Produção por etapas verificáveis.** Ideia → roteiro → storyboard → cena-mãe → camadas → validação → rig/animação → narração → montagem → MP4/QA → publicação.
7. **O custo é decidido antes da geração.** Orçamento por vídeo, limites de tentativas, aprovação de imagens antes de pagar por vídeo e comparação de provedores.
8. **Organizar por canal.** Não misturar histórico editorial, pesquisas, personagens, roteiros, custos e artes de canais diferentes; verificar duplicação antes de produzir.
9. **Autonomia não substitui verificação.** Agentes podem propor e executar partes autorizadas, mas entregas precisam de evidências (artefatos, testes, logs e arquivos).
10. **Não criar despesas desnecessárias.** Preferir reaproveitamento do que já existe, imagem/renderização local onde viável, modelos econômicos e imagens-base aprovadas.

## Ideias priorizadas

### Economia e IA
- Modelo econômico como assistente do Astra; tarefa pequena fica com modelo menor.
- Contexto mínimo: enviar só arquivos, logs e testes relacionados ao erro, com resumo estruturado do que já foi decidido.
- Reusar artefatos, prompt caching quando suportado, deduplicação de requisições e modelos roteados por dificuldade.
- Proxy de IA centralizado com logs de custo, limite por tarefa, controle de concorrência, tratamento de HTTP 429 e fallback autorizado.
- Usar Astra Standard apenas quando necessário; não adotar Ultrafast como padrão econômico.

### Produção de YouTube
- Ideias escolhidas pelo desempenho real do canal, público e tendências atuais, sem repetir vídeo/tema.
- Um gerente por canal com apoio de subgerente/auditor e especialistas para roteiro, narração, arte, animação, título, descrição, legendas, QA e publicação.
- Personagens recorrentes com bíblia visual, estilos fixos e identificadores versionados.
- Imagens estáticas com parallax/rig/Remotion como base; geração de vídeo neural somente nas tomadas que se beneficiam dela.
- Narração, legendas e render com ferramentas mais econômicas; guardar JSON de cenas, prompts, versões, aprovações e medições.
- Em vídeos com personagens protegidos de terceiros, avaliar licenças, originalidade e riscos antes de publicar.

### Animação 2D e engenharia
- Cena-mãe completa, depois extração consistente de background, personagem, foreground, acessórios e objetos RGBA.
- Rig de ossos/malha/controles, com piscadas, cabelo, capa ao vento, braços, respiração, oclusão e movimentos de câmera planejados por cena.
- Remotion/React para composição e timeline; Three.js quando indicado para deformação/articulação; FFmpeg/FFprobe principalmente para áudio e validação de MP4.
- QA de pixels, alpha, recortes, recomposição, profundidade, costura e consistência temporal antes do render definitivo.

## Escopo das notas

Estas páginas consolidam conversas e pesquisa até 14/11/2026. **Preço, catálogo de modelos e políticas de fornecedores são referências datadas**, não compromissos nem garantias. Decisões já discutidas e sugestões ainda pendentes são distinguidas nos documentos.

## Índice

- [01 — Economia de tokens, Astra e Proxy](01-economia-codex-e-proxy.md)
- [02 — Agentes, pesquisa e orquestração](02-agentes-pesquisa-e-orquestracao.md)
- [03 — Pipeline editorial e audiovisual](03-pipeline-youtube.md)
- [04 — Animação 2D por camadas, rig e Remotion](04-animacao-rig-remotion.md)
- [05 — Pesquisa de ferramentas, custos e direitos](05-ferramentas-custos-direitos.md)
- [06 — Roadmap, gates e indicadores](06-roadmap-e-validacao.md)
