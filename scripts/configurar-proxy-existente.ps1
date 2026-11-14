#requires -Version 5.1
<#
.SYNOPSIS
  Reutiliza um proxy Codex persistente ja em execucao no repositorio HelioConde/codex.
.DESCRIPTION
  Configura somente CODEX_PROXY_BASE_URL e CODEX_PROXY_API_KEY no GitHub Actions.
  Nenhuma conta OAuth ou accounts.json e copiada.
  A chave vem do ambiente atual, do Docker local (opcional) ou de entrada oculta.
  Valores sao enviados ao gh via stdin, nunca via argumentos, arquivo ou console.
  Requer gh autenticado com permissao de editar Actions secrets.
.EXAMPLE
  .\scripts\configurar-proxy-existente.ps1 -ProxyUrl 'https://proxy.seudominio.com'
.EXAMPLE
  .\scripts\configurar-proxy-existente.ps1 -ProxyUrl 'https://proxy.seudominio.com' -FromDocker
.EXAMPLE
  .\scripts\configurar-proxy-existente.ps1 -ProxyUrl 'https://proxy.seudominio.com' -FromDocker -Container chatgpt-codex-proxy
#>
[CmdletBinding()]
param(
    [string] $ProxyUrl = $env:CODEX_PROXY_BASE_URL,
    [switch] $FromDocker,
    [string] $Container = '',
    [switch] $SkipHealth
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$repo = 'HelioConde/codex'
$apiKey = $null

function Require-Command([string] $Name) {
    $cmd = Get-Command $Name -ErrorAction SilentlyContinue
    if (-not $cmd) { throw "Comando '$Name' nao encontrado no PATH." }
    return $cmd.Source
}

function Get-ValidatedProxyUrl([string] $Value) {
    if ([string]::IsNullOrWhiteSpace($Value)) {
        throw 'Informe a URL HTTPS do proxy persistente usando -ProxyUrl.'
    }
    $uri = $null
    if (-not [Uri]::TryCreate($Value.Trim(), [UriKind]::Absolute, [ref]$uri)) {
        throw 'URL do proxy invalida.'
    }
    if ($uri.Scheme -ne 'https') {
        throw 'O GitHub Actions precisa de um proxy acessivel por HTTPS. localhost/HTTP serve apenas para execucao local.'
    }
    if ($uri.Host -in @('localhost', '127.0.0.1', '::1')) {
        throw 'localhost nao e acessivel pelo runner do GitHub. Informe endereco HTTPS externo autorizado.'
    }
    if ($uri.UserInfo -or $uri.Query -or $uri.Fragment -or $uri.AbsolutePath.TrimEnd('/') -notin @('', '/v1')) {
        throw 'URL nao pode incluir credenciais, caminhos extras, query ou fragmento.'
    }
    return $uri.GetLeftPart([UriPartial]::Authority)
}

function Get-KeyFromDocker([string] $Name) {
    $null = Require-Command 'docker'
    if ([string]::IsNullOrWhiteSpace($Name)) {
        $active = @(& docker ps --format '{{.Names}}' 2>$null)
        if ($LASTEXITCODE -ne 0) { throw 'Docker nao esta acessivel.' }
        $matches = @($active | Where-Object { $_ -match '(?i)(codex.*proxy|proxy.*codex)' })
        if ($matches.Count -ne 1) {
            throw 'Container nao identificado de modo unico. Use -Container com o nome correto.'
        }
        $Name = $matches[0]
    }
    # A chave fica em memoria; nenhum token e enviado ao terminal nem armazenado.
    $lines = @(& docker exec $Name sh -c 'printf %s "$PROXY_API_KEY"' 2>$null)
    if ($LASTEXITCODE -ne 0) {
        throw 'Nao foi possivel consultar PROXY_API_KEY no container local.'
    }
    return [string]::Join('', $lines)
}

function Read-HiddenKey() {
    $secure = Read-Host 'Chave API do proxy (nao sera exibida)' -AsSecureString
    $handle = [IntPtr]::Zero
    try {
        $handle = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
        return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($handle)
    } finally {
        if ($handle -ne [IntPtr]::Zero) {
            [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($handle)
        }
        $secure.Dispose()
    }
}

function Set-ActionSecret([string] $GhPath, [string] $Name, [string] $Value) {
    if ([string]::IsNullOrEmpty($Value)) { throw "Valor de $Name nao pode estar vazio." }
    $startInfo = New-Object Diagnostics.ProcessStartInfo
    $startInfo.FileName = $GhPath
    $startInfo.Arguments = "secret set $Name --repo HelioConde/codex --app actions"
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $true
    $startInfo.RedirectStandardInput = $true
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true

    $p = New-Object Diagnostics.Process
    $p.StartInfo = $startInfo
    try {
        if (-not $p.Start()) { throw 'Nao foi possivel iniciar gh.' }
        $enc = New-Object Text.UTF8Encoding($false)
        $bytes = $enc.GetBytes($Value)
        try {
            $p.StandardInput.BaseStream.Write($bytes, 0, $bytes.Length)
            $p.StandardInput.Close()
        } finally {
            [Array]::Clear($bytes, 0, $bytes.Length)
        }
        $null = $p.StandardOutput.ReadToEnd()
        $null = $p.StandardError.ReadToEnd()
        $p.WaitForExit()
        if ($p.ExitCode -ne 0) {
            throw "Falha ao salvar $Name; confira autenticacao e permissao Actions Secrets."
        }
    } finally {
        if ($p.Id -gt 0 -and -not $p.HasExited) { $p.Kill() }
        $p.Dispose()
    }
}

try {
    $validatedUrl = Get-ValidatedProxyUrl $ProxyUrl
    $gh = Require-Command 'gh'
    & $gh auth status *> $null
    if ($LASTEXITCODE -ne 0) {
        throw 'GitHub CLI nao autenticado. Execute gh auth login.'
    }
    & $gh repo view $repo --json nameWithOwner --jq '.nameWithOwner' *> $null
    if ($LASTEXITCODE -ne 0) {
        throw "Sem acesso ao repositorio $repo."
    }

    if ($FromDocker) {
        $apiKey = Get-KeyFromDocker $Container
    } elseif (-not [string]::IsNullOrWhiteSpace($env:CODEX_PROXY_API_KEY)) {
        $apiKey = $env:CODEX_PROXY_API_KEY
    } else {
        $apiKey = Read-HiddenKey
    }
    if ($apiKey.Length -lt 20 -or $apiKey.Contains([char]13) -or $apiKey.Contains([char]10)) {
        throw 'Chave ausente ou invalida; nenhum Secret foi salvo.'
    }

    if (-not $SkipHealth) {
        $headers = @{ Authorization = "Bearer $apiKey" }
        try {
            $health = Invoke-RestMethod -Uri "$validatedUrl/health" -Method Get -Headers $headers -TimeoutSec 12 -ErrorAction Stop
            if ($health.status -ne 'ok' -or [int]$health.accounts -lt 1) {
                throw 'Servidor sem conta configurada ou sem status ok.'
            }
        } catch {
            throw 'Nao foi possivel validar autenticacao no proxy via HTTPS. Nenhum Secret foi salvo. Confira URL/rede/chave.'
        }
        Write-Host 'Proxy autenticado respondeu health=ok (sem gerar IA).'
    }

    Set-ActionSecret $gh 'CODEX_PROXY_BASE_URL' $validatedUrl
    Set-ActionSecret $gh 'CODEX_PROXY_API_KEY' $apiKey
    Write-Host "Configurados os dois Secrets do proxy persistente em $repo (valores ocultos)."
    Write-Host 'Proximo teste: GitHub > codex > Actions > Codex - Proxy IA (manual, texto e imagem) > operation=health e mode=persistent.'
    Write-Host 'Health nao consome inferencia; nao execute text/image antes de revisar a cota.'
} finally {
    $apiKey = $null
}
