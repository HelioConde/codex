# Pesquisa de ferramentas, custos e direitos — referência de 14/11/2026

**Status:** pesquisa e estimativas para orientar testes. **Não há contratação, acesso API ou preço garantido implícito.** Reconfirmar em documentação oficial na data de implementação.

## Resultado estratégico

**Modelo econômico para pensar + ferramentas especializadas para gerar mídia + software determinístico para montar + Codex para engenharia quando necessário**.

Imagens consistentes animadas com rig/parallax/Remotion tendem a custar menos do que gerar por IA cada segundo de vídeo. Aprovar imagens antes de contratar um clipe generativo. Reservar modelos premium para tomadas essenciais.

## Opções consideradas

| Etapa | Opções pesquisadas | Uso pretendido |
|---|---|---|
| Planejamento e roteiro | IA econômica / modelo menor | briefing, roteiro, prompts, scenes.json |
| Imagem | ComfyUI local, APIs econômicas de imagem, Runway Image, Luma Uni | imagens-base e referências consistentes |
| Image-to-video e clipes | Pika, Runway, Kling, Wan, Luma | movimento difícil, cenas curtas |
| Narração | ElevenLabs, Edge TTS ou outro TTS local/econômico | locução, vozes originais |
| Legendas | Whisper local, CapCut ou editor | sincronização e leitura |
| Montagem/rig | Remotion, Three.js, ferramentas próprias | articulação, câmeras, efeitos e timeline |
| Edição opcional manual | DaVinci Resolve | correção, áudio e edição fina |
| QA/exportação | FFmpeg/FFprobe, testes e OpenCV | validação automatizada |
| Engenharia | Codex; Astra quando necessário | integração, depuração, runners e Actions |

**ComfyUI** serve para workflows de imagem e integração local. Modelos de vídeo local podem exigir VRAM elevada; testar capacidade real antes de comprar GPU. Diferenciar licenças da interface e dos **pesos dos modelos**.

## Preços públicos aproximados encontrados na pesquisa

Valores em **USD**, informados pela pesquisa realizada até 14/11/2026; variam com resolução, API, áudio, planos e provedor:

| Referência | Faixa indicada na pesquisa |
|---|---:|
| Pika 2.5, 720p | ~US$ 0,04 por segundo |
| Runway Gen-4 Turbo | ~US$ 0,05 por segundo |
| Kling 3 Standard, sem áudio | ~US$ 0,09 por segundo |
| Wan 3.0 via Runway Dev, 720p | ~US$ 0,10 por segundo |
| Runway Gen-4.5 | ~US$ 0,12 por segundo |
| Kling 3 Standard, com áudio | ~US$ 0,13 por segundo |
| Luma Ray 3.2, 720p | ~US$ 0,30 por cinco segundos |
| Modelos premium | podem ultrapassar US$ 0,20/s e muito mais |

Imagem econômica: pesquisa citou cerca de **US$ 0,01–0,05 por imagem** em opções específicas. ElevenLabs: certas vozes/modelos na casa de **centavos por mil caracteres**, dependendo do produto/plano. Evitar generalizar essas referências a qualquer API.

## Cenários econômicos da pesquisa

**Exemplo teórico de Short de 60 s**, não meta de duração dos canais:
- 20 s finais de vídeo realmente generativo e 40 s de imagem animada, zoom, parallax, texto e efeitos.
- Com fator de retrabalho de 1,5×: gerar 30 s brutos de mídia generativa.
- 12 imagens em API econômica.
- Resultado estimado da pesquisa: **US$ 1,80–3,70 por vídeo de 60 s**, antes de câmbio/impostos/assinaturas.
- Para Shorts do VideoForge-IA, **preservar o requisito mínimo de 90 s** vigente; recalcular conforme quantidade de segundos generativos e cenas, não apenas escalar pelo tempo total.

**Exemplo teórico de vídeo de 8 minutos**:
- 90 s de clipes generativos no resultado, 135 s brutos com 50% de retrabalho.
- Cerca de 30 imagens, voz e montagem locais/econômicas.
- Estimativa: **US$ 8–16 por vídeo**, antes de extras e variação de fornecedor.
- Gerar os 480 s integralmente em uma API de US$ 0,09/s, com 50% de retrabalho, elevaria **somente o vídeo** a ~US$ 64,80.

Essas contas são **simulações**, não orçamento validado no ambiente real. Prever falhas, minimum charges, armazenamento, impostos, conversão cambial, TTS, recursos premium e eventual pós-processamento.

## Como medir orçamento na prática

~~~json
{
  "video_id": "alchemy-lab-example",
  "budget_usd": 5,
  "cost_entries": [
    {"stage": "image", "provider": "example", "attempts": 12, "cost_usd": 0.36},
    {"stage": "video", "provider": "example", "billable_seconds": 30, "cost_usd": 1.50}
  ],
  "gate": {
    "approved_art": true,
    "allowed_to_spend": false,
    "reason": "exemplo; autorização e provedores ainda não configurados"
  }
}
~~~

Orçamento acima é **ilustrativo** e não autorização de gastos. Medir gasto real via provedor e parar ao exceder teto.

## Mudanças de mercado citadas na pesquisa

- A pesquisa de novembro/2026 indicou que **Sora web/app e API foram descontinuados** no decorrer de 2026; não desenhar dependências de produção novas sem reconfirmar o status.
- Foi diferenciada a disponibilidade de **Wan 2.2 local** de versões posteriores comercializadas via API. Não presumir que anúncio de repositório de código signifique pesos completos disponíveis.
- Preferir integração por **interfaces de provedores substituíveis**. Serviços, disponibilidade, preços e licenças mudam.

## Direito autoral e monetização

- **YouTube** permite conteúdo com IA, mas pode restringir conteúdo repetitivo, massificado ou inautêntico e exige atenção a reutilização de obras de terceiros.
- Material realista gerado/alterado por IA que possa ser confundido com realidade pode exigir **disclosure**. Fantasia/2D claramente fictício costuma ter regras distintas; verificar caso a caso.
- Licença comercial de uma plataforma **não concede automaticamente direitos** sobre personagens, música, vídeos, marcas, imagens ou vozes de outras pessoas.
- Verificar separadamente autorização de uso comercial de cada plano/modelo (por exemplo, plano gratuito vs pago) antes de monetizar.
- Guardar provas de proveniência, IDs de assets, licenças, prompts e aprovações.
- Para fan content/anime, priorizar análise própria, cenas e ilustrações originais e evitar uso não autorizado de quadros oficiais, músicas ou vozes.

## Fontes oficiais para revalidação

- [OpenAI — uso de Astra](https://help.openai.com/en/articles/20001516-managing-usage-with-gpt-6-astra-in-work-and-codex)
- [OpenAI — preços API](https://developers.openai.com/api/docs/pricing)
- [Runway — preços da API](https://docs.dev.runwayml.com/guides/pricing/)
- [Pika — preços API](https://dev.pika.art/pricing)
- [Luma — API](https://lumalabs.ai/api)
- [Luma — preços](https://docs.agents.lumalabs.ai/guides/pricing/)
- [ComfyUI — projeto e licença](https://github.com/Comfy-Org/ComfyUI)
- [ElevenLabs — preços](https://elevenlabs.io/pricing)
- [ElevenLabs — termos](https://elevenlabs.io/terms-of-use)
- [DaVinci Resolve](https://www.blackmagicdesign.com/br/products/davinciresolve/)
- [YouTube — monetização](https://support.google.com/youtube/answer/1311392)
- [YouTube — conteúdo alterado ou sintético](https://support.google.com/youtube/answer/14328491)
- [Runway — direito de uso](https://help.runwayml.com/hc/en-us/articles/18927776141715-Usage-rights)
- [Sora — descontinuação](https://help.openai.com/pt-br/articles/20001152-what-to-know-about-the-sora-discontinuation)

A comparação é **registro histórico**; consultar sempre as páginas atuais antes de implementar, contratar ou publicar.
