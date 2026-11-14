# Importar a sessão local do proxy VideoForge-IA para o repositório codex

**Modo escolhido:** reutilizar a sessão já salva no computador, sem copiar Secrets de outro repositório.  
**Script:** [scripts/importar-sessao-videoforge.ps1](../scripts/importar-sessao-videoforge.ps1).  
**Data:** 14/11/2026.

## Pré-requisitos

- Windows PowerShell 5.1 ou posterior.
- [GitHub CLI](https://cli.github.com/) instalado e autenticado (`gh auth login`), com acesso para definir Actions Secrets no repositório `HelioConde/codex`.
- Docker com o **contêiner do proxy já em execução** no computador, contendo `/app/data/accounts.json`, ou backup local **privado** desse arquivo.
- Repositório `HelioConde/codex` clonado/atualizado na máquina.

## Comando recomendado

Execute na raiz do repositório `codex`:

```powershell
git pull
gh auth status
.\scripts\importar-sessao-videoforge.ps1
```

O script tenta localizar automaticamente um container ativo com `codex` e `proxy` no nome. Se houver mais de um:

```powershell
docker ps --format '{{.Names}}'
.\scripts\importar-sessao-videoforge.ps1 -Container chatgpt-codex-proxy
```

Ou, usando um backup privado:

```powershell
.\scripts\importar-sessao-videoforge.ps1 -ArquivoContas 'C:\privado\accounts.json'
```

**Não envie o arquivo de contas para esta conversa, GitHub, issues ou artifacts.**

## O que será configurado

O script valida a presença de `records` e tokens no JSON, cria uma nova chave aleatória para o projeto e envia os valores pelo **stdin** da CLI `gh`, sem imprimi-los nem gravar arquivos com tokens no repositório.

- `CODEX_PROXY_ACCOUNTS_JSON`: snapshot das sessões de contas autorizadas.
- `CODEX_PROXY_API_KEY`: chave de autenticação do proxy **nova e exclusiva do codex**.

**Os Secrets e os arquivos do VideoForge-IA não serão alterados.** O script não precisa acessar os Secrets antigos do GitHub, cujos valores não podem ser revelados pela API.

## Validação no GitHub

Após o script confirmar gravação:

1. Abra [Actions — Codex Proxy IA](https://github.com/HelioConde/codex/actions/workflows/proxy-ia-manual.yml).
2. Selecione `operation=health`, `mode=ephemeral` e `execute=false` e execute.
3. Se funcionar, use `operation=models` com `mode=ephemeral` para conferir os modelos disponíveis.
4. Somente depois, **com autorização e cota disponíveis**, use `operation=text` e `execute=true`; pode consumir a franquia.

O workflow usa a imagem pré-compilada `ghcr.io/helioconde/videoforge-codex-proxy:upstream-02f8ce3581c1`, com permissão de leitura GHCR para o repo `codex` se o pacote for privado. Nenhuma nova compilação do servidor é necessária.

## Limitações e segurança

- Sessões OAuth podem expirar. O GitHub Actions usa **um snapshot**: tokens atualizados dentro do job não são sincronizados automaticamente com o Secret.
- Se Docker não tiver um contêiner ativo e não houver backup local, não podemos extrair os valores de Secrets antigos. Será necessário autorizar uma nova sessão por meios permitidos.
- O backend do proxy de terceiros usa interfaces privadas, não oficiais; ele pode deixar de funcionar e deve respeitar os limites de conta e as condições de uso do provedor.
- Não colocar chave no README, TOML de projeto ou prompt de IA. O repo `codex` é público; inputs de workflow e artifacts podem ser visíveis a pessoas com acesso.
- Não rodar `text`/`image` antes de confirmar que `health` e `models` funcionam; e nunca repetir automaticamente chamadas diante de HTTP 429.

## Alternativa: servidor persistente

Se houver servidor HTTPS persistente em funcionamento, usar [configurar-proxy-existente.ps1](../scripts/configurar-proxy-existente.ps1), quando disponível, é diferente deste procedimento: compartilha o **serviço** em vez de duplicar snapshot. Esta página corresponde à opção solicitada: **sessão salva no computador**.
