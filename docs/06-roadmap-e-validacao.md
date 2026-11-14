# Roadmap de implementação e critérios de aceite

Este plano registra **próximos passos propostos**, não afirma que todo o trabalho esteja executado. O produto de vídeo continua no repositório **VideoForge-IA**; o repositório **codex** conserva decisões, análise e orientação da estratégia multimodelo.

## Fase 0 — Medir e estabilizar o que já existe

- [ ] Mapear custos/créditos reais do Codex, Astra, proxy e APIs de mídia por tarefa.
- [ ] Conferir o nome de cada modelo, modo de velocidade, cota e contrato da conta.
- [ ] Diagnosticar **HTTP 429** por logs saneados, limites de conta, concorrência e retries.
- [ ] Verificar Actions que falham em build, TypeScript, separação RGBA, Three.js e Remotion; priorizar uma falha reproduzível por vez.
- [ ] Executar pipeline de **MP4 técnico sem IA paga** e comprovar o arquivo com FFprobe.
- [ ] Separar verificações sem IA de pipelines que consomem créditos.
- [ ] Validar runners pré-construídos e evitar instalações repetitivas.

**Gate:** render de teste reproduzível + custos/cotas conhecidos + logs sem segredos.

## Fase 1 — Uma cena completa e consistente

- [ ] Escolher cena de teste representativa, sem abrir muitas frentes ao mesmo tempo.
- [ ] Fixar estilo e gerar/aprovar cena-mãe.
- [ ] Gerar/separar camadas RGBA e validar recomposição.
- [ ] Montar rig de cabeça, olhos, cabelo, roupa e objetos necessários.
- [ ] Adicionar animações reais e câmera com Remotion/Three.js, em vez de PNG inteiro.
- [ ] Testar piscar, vento na capa, oclusão e ausência de alpha inesperado.
- [ ] Gerar preview curto e MP4 reprodutível.

**Gate:** QA visual aprovado; sem duplicações, recortes transparentes ou perda de pixels.

## Fase 2 — Produção audiovisual mínima

- [ ] Acrescentar roteiros originais e JSON de cenas com shots, áudio, movimentos e assets.
- [ ] Integrar TTS e sincronização de legendas.
- [ ] Montar um Short completo com duração correta e custo registrado.
- [ ] Acrescentar metadados e validação editorial.
- [ ] Só então testar API generativa premium para poucos planos.

**Gate:** MP4 final válido e comparável à especificação; relatório de custo por vídeo.

## Fase 3 — Agentes e automações

- [ ] Pesquisador coleta métricas/tendências por canal com fontes datadas.
- [ ] Gerente aprova pauta sem repetição.
- [ ] Especialistas produzem entregáveis sob contrato estruturado.
- [ ] Subgerente audita qualidade, ranking dos agentes, retrabalho e custo.
- [ ] Adicionar cache de roteiros/pesquisas, checkpoints e limites reais no proxy.
- [ ] Registrar vídeo, versão dos assets, custo, conteúdo anterior e decisões por canal.

**Gate:** tarefas só são promovidas quando o pipeline de um canal funcionar de ponta a ponta.

## Fase 4 — Escala e otimização

- [ ] Comparar qualidade/custo entre IA local, APIs baratas e premium.
- [ ] Medir retenção, CTR, engajamento, inscritos por mil views engajadas e esforço.
- [ ] Fazer testes offline de gancho, ritmo, motion, títulos e duração sem publicar material experimental automaticamente.
- [ ] Priorizar vídeos com potencial de crescimento real; evitar repetição/massificação.
- [ ] Melhorar autonomia somente quando gastos, direitos e resultados forem auditáveis.

## Gatilhos para escalar ao Astra

Usar Astra somente quando:
- erro persistir após teste reproduzível e triagem barata;
- mudar arquitetura central ou corrigir integração de alta complexidade;
- questão exigir raciocínio técnico além do modelo econômico;
- existir contexto mínimo, hipótese clara e critério objetivo de sucesso.

Não usar Astra para redigir a descrição de cada vídeo, repetir a pesquisa da semana ou animar quadros.

## Regras de segurança e custo

1. **Sem segredos em commit:** tokens e contas ficam protegidos fora do repositório.
2. **Sem despesas novas por padrão:** trabalho pago depende de orçamento/autorização real do projeto.
3. **Sem falsa confirmação:** workflow disparado, render concluído e upload publicado são estados diferentes.
4. **Sem repetição editorial:** histórico é gate anterior à geração.
5. **Sem regressão visual:** fixtures, checks de alpha, oclusão e composição.
6. **Sem publicação indevida:** revisão de licença, direitos e configuração de visibilidade.
7. **Sem expansão prematura:** primeiro vídeo completo, depois autonomia multiagente.

## Decisões em aberto

- Qual o limite de gastos mensal/por vídeo que será aprovado?
- Quais provedores realmente estarão integrados, com APIs/licenças testadas?
- Quais máquinas/GPU local estão disponíveis para ComfyUI e inferência de vídeo?
- Quais regras específicas de cada canal substituem as regras gerais?
- Como integrar a pesquisa externa às filas de trabalho sem reenviar material grande ao proxy?
- Quais resultados das correções atuais já estão comprovados por artifacts e QA?

Estas perguntas **não bloqueiam o registro das ideias**; devem ser respondidas antes de autorizar implementação paga ou publicação.
