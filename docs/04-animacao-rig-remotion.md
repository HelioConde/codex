# Manual principal de animação 2D — camadas, rig, Three.js e Remotion

**Prioridade:** guia de requisitos de animação discutidos para o VideoForge-IA. Este arquivo serve como referência para agentes e programadores; a implementação real pertence ao repositório [VideoForge-IA](https://github.com/HelioConde/VideoForge-IA).

## Regra fundamental: personagem de verdade, não PNG inteiro movendo

A animação deve dar vida a **componentes do personagem e objetos**: olhos, boca, cabeça, tronco, braços, mãos, pernas, cabelos, capa, roupa, armas, acessórios. Mover/rotacionar/esticar a imagem inteira de forma artificial **não satisfaz** a intenção. Quando uma parte precisa dobrar ou ondular, aplicar pivôs, ossos, malha deformável e pesos de vértice apropriados.

A proposta discutida combina:
- **Cena-mãe completa** aprovada como referência canônica.
- **Camadas RGBA** consistentes com os pixels originais: fundo, personagem, acessórios, objetos, foreground.
- **Rig 2D / mesh** (por exemplo, Three.js quando fizer sentido) com pivôs, pesos e deformações.
- **Remotion** para timeline, composições React, câmeras 2D, efeitos, sincronização e exportação.
- **FFmpeg/FFprobe** para tarefas auxiliares de áudio, compatibilidade e QA, não como substituto da animação articulada.

## Ordem obrigatória de produção

1. Gerar **imagem completa da cena** com estilo visual congelado.
2. Aprovar os pixels da cena-mãe e registrar hash/versão.
3. Separar **background limpo**, personagem e objetos com alpha verdadeiro. Restaurar fundo nos locais ocultos pelo personagem usando referência consistente.
4. Recortar **subpartes apenas quando o movimento exigir**: cabeça, tronco, braços, olhos, cabelo, capa, peças de roupa. Se o elemento já foi desenhado isolado, **reutilizar o asset original** em vez de recortá-lo de outro elemento.
5. Determinar hierarquia, pivôs, deformação, oclusão e relacionamento frente/trás.
6. Repor camadas na pose neutra e comparar com a cena-mãe; **a recomposição deve corresponder visualmente à arte aprovada**.
7. Aplicar animação e testar sequências curtas, depois QA frame a frame.
8. Somente após aprovação gerar MP4 final.

## Falhas anteriores que o manual deve impedir

- Cabelo cortado sem necessidade quando a **capa já tinha asset próprio**.
- Capa rígida que oscila como uma placa em vez de ondular sob vento.
- Rosto ficando transparente em determinados quadros; pedaços da capa revelando marcas do recorte.
- Camadas com bordas serrilhadas, halos escuros ou manchas de alpha.
- Personagens de fundo incorporados ao recorte da personagem principal.
- Estilo mudando entre desenho e realismo ao longo do mesmo vídeo.
- Piscada correta sacrificada quando se troca todo o rosto em vez de animar a região certa.
- Dar como concluído um rig que só move o sprite inteiro.

## Caso de referência: Anya

Na cena discutida, isolar a **cabeça da Anya** sem incluir Loid e Yor, preservar **piscada aprovada** e validar recomposição com corpo e cabelo. O recorte determinístico com OpenCV pode conservar pixels originais; isso **não libera** um rig se testa apenas segmentação. Antes de articular:
- garantir máscara exclusiva da personagem e ausência de pixels de vizinhos;
- testar alpha do contorno e regiões de rosto/cabelo;
- recompor cabeça, corpo e fundo sem "fantasmas" de Loid/Yor;
- definir pivôs compatíveis com pescoço e olhos;
- verificar cada frame, especialmente movimentos nos quais uma camada descobre outra;
- guardar imagens esperadas e diferenças para regressão.

Esse exemplo documenta requisitos, **não afirma que o QA ou os workflows tenham sido concluídos com sucesso**.

## Capa, cabelo e vento

Para uma capa sob vento:
- dividir porções do tecido em malha com pontos de ancoragem nos ombros;
- animar com ondas de amplitude e atraso progressivos, variando direção, intensidade e frequência;
- aplicar inércia, sobreposição e atraso entre parte superior e bordas soltas;
- limitar deformação para evitar atravessar o rosto e a geometria do tronco;
- preservar cabelo como camada independente, com movimento próprio quando visível;
- evitar translação uniforme que faça todo o tecido parecer madeira;
- manter máscara e malha fechadas para não aparecer rosto transparente no recorte;
- usar teste de vento baixo, médio e alto, inspecionando quadros extremos.

No cabelo: raízes presas à cabeça; mechas com atraso e amplitude variável; não recortar o cabelo para animar uma capa que já é separada.

## Contrato de animação por cena

~~~json
{
  "scene_id": "julgamento-01",
  "assets": {
    "scene_mother": "images/scene-01-approved.png",
    "background": "layers/background.png",
    "head": "layers/kael-head.png",
    "body": "layers/kael-body.png",
    "hair": "layers/kael-hair.png",
    "cape": "layers/kael-cape.png"
  },
  "coordinate_system": "scene-pixels",
  "fps": 30,
  "rig": {
    "head": {"parent": "neck", "pivot": [0.50, 0.92], "rot_deg": [-2, 3]},
    "eyes": {"type": "blink", "keyframes": [40, 44, 47]},
    "cape": {"type": "mesh", "anchor": "shoulders", "wind": {"strength": 0.28, "frequency": 0.65}},
    "hair": {"type": "secondary_motion", "lag_frames": 4}
  },
  "camera": [
    {"frame": 0, "zoom": 1.4, "target": "kael"},
    {"frame": 120, "zoom": 1.0, "target": "throne"}
  ],
  "checks": [
    "recomposition_matches_reference",
    "no_neighbor_pixels",
    "face_never_transparent",
    "cape_does_not_cut_hair",
    "visible_motion_is_articulated"
  ]
}
~~~

Pivôs e números são **exemplo de especificação**, não coordenadas definitivas de assets reais.

## Direção e filmagem: animação não é apenas o personagem

A direção deve indicar **sequência de planos** e revelações. Exemplo do dorama MMORPG: fundo preto → close de espada sendo desembainhada e som metálico → Kael ajoelhado diante de trono → travelling/zoom para trás → revelação de dois guardas com lanças cruzadas atrás dele. Cada shot precisa de ação, duração, câmera, movimento dos objetos e trilha especificados; cortes e sobreposições devem ficar sincronizados.

## QA automático e visual

| Gate | Evidência esperada |
|---|---|
| Pixel/alpha | diferenças quantificáveis entre cena neutra recomposta e cena aprovada |
| Contorno | sem halos, serrilhados excessivos ou buracos |
| Oclusão | mãos, cabelo, roupa e acessórios na profundidade correta |
| Movimento | pontos/pivôs articulados e sem atravessar outra malha |
| Continuidade | identidade, escala e iluminação entre shots |
| Animação | expressões preservadas e mudanças coerentes frame a frame |
| Render | MP4 H.264/AAC ou formato validado, fps/duração/resolução e áudio corretos |
| Regressão | fixtures para cenas aprovadas; comparação antes de aceitar mudanças |

Rodar teste unitário de geometria/rig, teste de composição neutra e render curto **sem IA paga** antes de usar APIs de geração.

## Relação com ferramentas

Remotion deve consumir o **contrato de cena** e os assets versionados; Three.js ajuda no rig/deformação quando é a melhor opção; OpenCV ajuda em máscaras/QA; FFprobe inspeciona o resultado. Não é exigência instalar ferramentas novas se o pipeline existente já entrega o recurso desejado. Preferir reuso dos runners pré-construídos.
