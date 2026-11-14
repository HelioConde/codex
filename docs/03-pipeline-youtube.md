# Pipeline de produção audiovisual para YouTube

## Objetivo técnico

Entregar **vídeo original, coerente, com boa movimentação e MP4 realmente reproduzível**, gastando o mínimo necessário de IA paga. Separar pesquisa/planejamento, geração de mídia, renderização e publicação.

## Passo a passo

1. **Análise do canal**: coletar dados históricos, histórico de conteúdo, público e tendências. Identificar oportunidade sem duplicação.
2. **Brief**: objetivo do vídeo, formato (Short/longform), duração, estilo fixo, personagens e orçamento.
3. **Roteiro**: gancho forte, desenvolvimento, conclusão e cenas visuais próprias. Para o projeto de dorama MMORPG, a história e as ações devem ser planejadas dramaticamente, não só como narração.
4. **JSON de cenas**: cada cena especifica duração, enquadramento, transição, movimentos de câmera e de cada elemento, áudio e dependências.
5. **Storyboard e cena-mãe**: gerar uma imagem completa com personagens e objetos no lugar; aprovar a arte e o estilo antes de separar camadas.
6. **Separação de camadas**: derivar da cena-mãe background limpo, personagem RGBA, objetos RGBA, efeitos e foreground; restaurar áreas ocultas quando preciso.
7. **QA visual**: comparar recomposição com a referência, detectar duplicatas, transparência irregular e incompatibilidade de pixels.
8. **Rig/animatic**: especificar articulações, malhas, deformações, keyframes, expressões, câmera e oclusões por cena.
9. **Geração premium seletiva**: reservar image-to-video/text-to-video para tomadas impossíveis ou muito caras de fazer com rig/parallax.
10. **Voz/áudio**: TTS, música/efeitos licenciados, sincronização e níveis adequados.
11. **Composição**: Remotion renderiza o timeline, textos e layers; usar FFmpeg/FFprobe para QA, compatibilização e tarefas auxiliares.
12. **Validação final**: codec, resolução, frames, duração, sincronização, áudio, legendas, revisão visual e custo.
13. **Metadados/publicação**: thumb, título, descrição, tags, revisão de direitos, upload somente nos canais autorizados; registrar status real e URL de publicação.

## Regra de consistência

Um erro recorrente observado: imagens alternando desenho, outro desenho e realismo de uma cena para outra. O diretor de arte deve **congelar estilo, referência, paleta, proporções, personagens e iluminação** para o vídeo inteiro. Não permitir que o gerador reinterprete do zero a cada prompt.

**Bíblia visual por personagem**: ID e versão, frente/perfil/corpo inteiro, poses-chave, expressões, cabelos, figurino, acessórios, negativos e exemplos aprovados. Reaproveitar imagem-base em vez de pagar por reinterpretações.

## Short vs. vídeo longo

**Short**: gancho nos segundos iniciais, muitas ações visualmente claras; combinar ilustrações animadas, câmera, parallax, partículas, rig e alguns clipes generativos. O exemplo econômico da pesquisa foi de 60 s, mas **não sobrescreve o requisito de duração usado no VideoForge-IA: Shorts de pelo menos 1min30s, enquanto essa regra estiver vigente.**

**Vídeo longo**: alternar narração, imagens originais, animação por rig, gráficos, montagens e clipes premium localizados. Não gastar API de vídeo para cobrir integralmente todos os minutos.

## JSON de cena — exemplo autoral do dorama MMORPG

~~~json
{
  "project_id": "alchemy-lab-dorama-mmorpg",
  "visual_style": "dark-fantasy-2d-consistente-v1",
  "scene_id": "julgamento-01",
  "duration_frames": 270,
  "fps": 30,
  "canvas": {"width": 1080, "height": 1920},
  "continuity": {
    "characters": ["kael-v1", "guarda-a-v1", "guarda-b-v1"],
    "props": ["espada-v1", "lança-a-v1", "lança-b-v1", "trono-v1"]
  },
  "shots": [
    {
      "start_frame": 0,
      "end_frame": 45,
      "background": "preto",
      "action": "som e imagem parcial da espada sendo desembainhada",
      "camera": {"framing": "close-up", "motion": "static"},
      "sound": "metal_draw_v1"
    },
    {
      "start_frame": 45,
      "end_frame": 150,
      "camera": {"framing": "medium", "target": "kael", "motion": "dolly-out_suave"},
      "action": "Kael ajoelhado diante do trono; respiração, cabeça baixa e movimento sutil da capa"
    },
    {
      "start_frame": 150,
      "end_frame": 270,
      "camera": {"framing": "wide", "motion": "dolly-out"},
      "action": "o enquadramento revela dois guardas com lanças cruzadas atrás de Kael; luz das tochas reage à cena"
    }
  ],
  "layers": ["background", "guards", "kael-body", "kael-head", "cape", "spears", "foreground"],
  "qa": ["visual_consistency", "no_duplicate_characters", "rig_valid", "alpha_valid"]
}
~~~

Valores e tempos acima são **exemplo editorial**, não render concluído.

## Padrão de artefatos

- **brief.md** — propósito, pauta, referências, veto a repetições e limites.
- **scenes.json** — plano técnico completo; sempre versionado.
- **style-bible.md** — identidade visual consistente.
- **images/** — cenas-mãe aprovadas e versões.
- **layers/** — PNGs RGBA, máscaras, sprites e mapa de composição.
- **rig/** — estrutura de ossos/malhas, pivôs e movimentos.
- **audio/** — narração e efeitos com licenças.
- **renders/** — MP4, thumbnail e previews.
- **qa/report.json** — falhas de pixel, alpha, sincronização e MP4.
- **costs.json** — custo por provedor, tentativas, custo rejeitado e total.
- **provenance.json** — origem do asset e permissões de uso.

## Critérios objetivos de entrega

- O arquivo MP4 existe e é baixável; não basta um workflow com status verde.
- FFprobe confirma duração, codec e stream de áudio quando necessário.
- Cenas mantêm personagem e estilo; transições não mostram transparências ou recortes.
- Camadas recompostas não duplicam personagens/objetos.
- Publicação só é declarada concluída com evidência do YouTube.
- Qualquer falha volta à etapa mínima afetada, sem recriar o vídeo inteiro.
