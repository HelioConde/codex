# Integracao do Codex Proxy do VideoForge como IA de texto e imagem

**Atualizado:** 14/11/2026. **Status:** cliente e workflow implementados; credenciais e verificacao live ainda dependem do proprietario.

## O que foi implementado

O repo `HelioConde/codex` agora pode reutilizar o proxy de `HelioConde/VideoForge-IA` para **planejamento, roteiros, pesquisa guiada por contexto fornecido, prompts, JSON de cenas, analise de erros, revisao de codigo e geracao de imagens**. O cliente fala diretamente com:

| Comando | Rota | Usa inferencia? |
|---|---|---|
| `python -m proxy_ai health` | GET `/health` | Nao |
| `python -m proxy_ai models` | GET `/v1/models` | Nao |
| `python -m proxy_ai text --prompt-file ... --execute` | POST `/v1/responses` | Sim |
| `python -m proxy_ai image --prompt-file ... --output ... --execute` | POST `/v1/images/generations` | Sim |

O `--execute` e obrigatorio para qualquer criacao de texto ou imagem. Sem ele, os comandos sao inofensivos; push/PR executa **apenas testes offline**.

**Origem**: o mesmo [adaptador documentado no VideoForge-IA](https://github.com/HelioConde/VideoForge-IA/blob/main/docs/CODEX-PROXY-ACTIONS.md) usa [10/chatgpt-codex-proxy](https://github.com/10/chatgpt-codex-proxy) no commit fixado `02f8ce3581c15eb11b2d65daf93c3d4e3bd0e635` e a imagem precompilada `ghcr.io/helioconde/videoforge-codex-proxy:upstream-02f8ce3581c1`. **O upstream usa APIs privadas e nao oficiais, que podem mudar**. Nem o cliente nem a conta ganham creditos ilimitados; os limites e termos do servico continuam aplicaveis.

## 1. No Windows, usar localmente

Na pasta clonada do repositorio, configure no **PowerShell atual**, sem inserir valores em arquivos do Git:

```powershell
$env:CODEX_PROXY_BASE_URL = 'https://seu-proxy-autorizado.example.com'
$env:CODEX_PROXY_API_KEY = Read-Host 'Chave privada do proxy'

python -m proxy_ai health
python -m proxy_ai models

New-Item -Type Directory -Force outputs | Out-Null
Set-Content -Encoding utf8 outputs/brief.txt 'Crie um roteiro original e divida em cenas JSON para YouTube.'

# Apenas avisa (nao faz chamada)
python -m proxy_ai text --prompt-file outputs/brief.txt

# Usa o proxy como IA para trabalho escrito
python -m proxy_ai text --prompt-file outputs/brief.txt --model gpt-6.1-sol --effort low --output outputs/roteiro.txt --execute

# Gera imagem apenas quando autorizado
python -m proxy_ai image --prompt-file outputs/brief.txt --output outputs/cena --execute
```

O nome real do modelo deve existir em `/v1/models`. `outputs/` e ignorado pelo Git. Nao enviar dados secretos a prompts. Modelos de imagem autorizados pelo cliente: `gpt-image-2` e `gpt-image-1.5`.

## 2. Em outro programa Python

```python
from proxy_ai import ProxyClient

client = ProxyClient.from_env()
resposta, uso = client.text(
    'Elabore ideias de cenas sem repetir o roteiro fornecido.',
    instructions='Responda em portugues com JSON compacto.',
    model='gpt-6.1-sol',
    effort='low',
)
print(resposta)
```

O programa acima **fara uma chamada gerativa quando executado**. Nao existe worker automatico, renovacao de contas nem retry silencioso. O cliente proibe redirecionamentos HTTP que poderiam divulgar a chave. Em HTTP 429, retorna erro sem repetir.

## 3. Usar tambem como provedor do Codex CLI

Arquivo de exemplo: [config/codex-proxy.user.toml.example](../config/codex-proxy.user.toml.example).

Em versoes recentes da CLI, providers personalizados devem ser configurados em **`%USERPROFILE%\.codex\config.toml`** (global do usuario, Windows) ou **`~/.codex/config.toml`** no Linux. A configuracao `.codex/config.toml` do repositorio **nao registra um provider global**.

1. Fazer backup da configuracao global original; mesclar o exemplo, sem sobrescrever outros providers.
2. Substituir `https://seu-proxy.example.com/v1` pela URL HTTPS autorizada do proxy.
3. Manter a chave somente em `CODEX_PROXY_API_KEY` no ambiente, nunca no TOML.
4. Abrir nova sessao da CLI Codex e verificar se o provider `videoforge_proxy` e o modelo `gpt-6.1-sol` estao realmente ativos.
5. Se a CLI nao aceitar o protocolo SSE do proxy, voltar ao provider anterior e usar `python -m proxy_ai text` para tarefas de IA. **Nao contornar limites ou autenticacao.**

Nao usar Ultrafast como modo padrao de economia. O proxy nao muda automaticamente a IA desta conversa do ChatGPT.

## 4. Usar pelo GitHub Actions

Workflow manual: [.github/workflows/proxy-ia-manual.yml](../.github/workflows/proxy-ia-manual.yml).

No repositório **HelioConde/codex**, configurar os Secrets em **Settings → Secrets and variables → Actions**:

- **persistent (preferido):** `CODEX_PROXY_BASE_URL` (origem HTTPS do proxy existente) e `CODEX_PROXY_API_KEY`.
- **ephemeral:** `CODEX_PROXY_API_KEY` e `CODEX_PROXY_ACCOUNTS_JSON` (sessao autorizada do proprio usuario). O job usa a **mesma imagem GHCR fixada** do VideoForge. Se o GHCR exigir autorizacao, conceder permissao de leitura do pacote ao repo `codex`.

Os valores dos Secrets de **outro repositório nao podem ser recuperados pela API**, mesmo pelo dono; e necessario cadastra-los separadamente sem expor tokens. **Nao comitar accounts.json, cookies ou chaves**.

Em **Actions → Codex - Proxy IA (manual, texto e imagem)**, iniciar por `health` e depois `models`. Para `text` ou `image`, informar somente um prompt **nao sensivel** e marcar `execute=true`. Nao ocorre publicacao no YouTube. O resultado fica em artifact por **1 dia**.

**Atencao:** o repo `codex` e publico. Inputs do workflow e arquivos publicados como artifacts nao sao adequados para prompts, chaves ou resultados sensiveis. Para isso, usar o CLI **local**, nao o Actions.

## 5. Testar e medir

```bash
python -m unittest discover -s tests -v
```

O teste de regressao inclui respostas simuladas (sem rede), modelos, health, formatacao de texto, imagem base64, protecao contra HTTP 429 e `--execute`. O CI [test-proxy-ai.yml](../.github/workflows/test-proxy-ai.yml) roda sem credenciais ou inferencia em alteracoes de codigo.

**Ja implementado:** interface IA de texto e imagem, comandos, modelo de provider, workflow manual e testes unitarios offline.

**Pendente:** configurar Secrets reais no `codex`, conferir acesso ao GHCR, validar `health` e `models` ao vivo, e executar um smoke test de texto com autorizacao e medicao de custo. Nao afirmar que o proxy esta operacional na conta antes desses testes.

## Separacao do VideoForge-IA

O pipeline de imagens e animacao continua no VideoForge-IA, com regras de cena-mae, mascaras RGBA, rig Three.js e Remotion. Este repo fornece um **cliente generico de IA** e um exemplo de ponte para o Codex CLI; nao substitui o pipeline nem altera workflows do VideoForge.
