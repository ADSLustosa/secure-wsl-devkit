#!/usr/bin/env bash
# secure-wsl-devkit — setup automatizado e seguro do ambiente de desenvolvimento no WSL 2
# Idempotente: pode ser executado várias vezes sem duplicar configurações.
set -euo pipefail

# ===== Configuração =====
readonly DEVKIT_GIT_NAME="ADSLustosa"
readonly DEVKIT_GIT_EMAIL="161537433+ADSLustosa@users.noreply.github.com"
readonly DEVKIT_NVM_VERSION="v0.40.3"
readonly DEVKIT_MARCADOR_PATH="# --- Caminhos do Windows liberados manualmente"
readonly DEVKIT_MARCADOR_KEYCHAIN="# --- Agente SSH (keychain) do secure-wsl-devkit"
readonly DEVKIT_KEYCHAIN_TIMEOUT_MIN=60

# Pontos de injeção para testes: em uso normal, valem os padrões do WSL.
# O teste de integração (tests/fresh-install.sh) aponta para um WSL simulado.
DEVKIT_WINDOWS_ROOT="${DEVKIT_WINDOWS_ROOT:-/mnt/c}"
DEVKIT_PROC_VERSION="${DEVKIT_PROC_VERSION:-/proc/version}"

# ===== Funções auxiliares =====
log() { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
erro() { printf '\033[1;31mERRO: %s\033[0m\n' "$*" >&2; }
aviso() { printf '\033[1;33mAVISO: %s\033[0m\n' "$*" >&2; }

# Devolve o PATH recebido sem as pastas do Windows (/mnt/<letra> e a raiz configurada)
# e sem entradas vazias, que o shell interpretaria como "a pasta atual".
# Necessário na primeira execução: o corte do wsl.conf só vale depois de reiniciar a distro.
filtrar_path_windows() {
  local -a entradas mantidas=()
  local entrada
  IFS=':' read -r -a entradas <<< "$1"
  for entrada in "${entradas[@]}"; do
    case "$entrada" in
      "" | /mnt/[a-z] | /mnt/[a-z]/* | "$DEVKIT_WINDOWS_ROOT" | "$DEVKIT_WINDOWS_ROOT"/*) continue ;;
    esac
    mantidas+=("$entrada")
  done
  local IFS=':'
  printf '%s\n' "${mantidas[*]}"
}

# ===== Etapas =====
verificar_ambiente() {
  log "Verificando o ambiente"
  if [[ $EUID -eq 0 ]]; then
    erro "Não execute como root (sem sudo). O script pede a senha quando precisar."
    exit 1
  fi
  if ! grep -qi microsoft "$DEVKIT_PROC_VERSION"; then
    erro "Este script foi feito para o WSL 2."
    exit 1
  fi
  echo "Usuário: $USER | Distro: ${WSL_DISTRO_NAME:-desconhecida}"
}

instalar_pacotes() {
  log "Atualizando o sistema e instalando pacotes base"
  sudo apt-get update
  # confdef/confold: se um pacote trouxer um arquivo de configuração novo, mantém o atual sem perguntar
  sudo DEBIAN_FRONTEND=noninteractive apt-get upgrade -y \
    -o Dpkg::Options::=--force-confdef -o Dpkg::Options::=--force-confold
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y build-essential curl unzip keychain shellcheck pre-commit
}

configurar_git() {
  log "Configurando o Git"
  git config --global user.name "$DEVKIT_GIT_NAME"
  git config --global user.email "$DEVKIT_GIT_EMAIL"
  git config --global init.defaultBranch main
  git config --global pull.rebase true
  git config --global core.autocrlf input
  git config --global core.editor "code --wait"
  git config --global fetch.prune true

  if [[ -f "$HOME/.ssh/id_ed25519.pub" ]]; then
    git config --global gpg.format ssh
    git config --global user.signingkey "$HOME/.ssh/id_ed25519.pub"
    git config --global commit.gpgsign true
    printf '%s %s\n' "$DEVKIT_GIT_EMAIL" "$(cat "$HOME/.ssh/id_ed25519.pub")" > "$HOME/.ssh/allowed_signers"
    git config --global gpg.ssh.allowedSignersFile "$HOME/.ssh/allowed_signers"
    echo "Assinatura de commits ativada."
  else
    echo "Chave SSH não encontrada: a assinatura será ativada na próxima execução."
  fi
}

configurar_pre_commit() {
  log "Ativando o pre-commit em todo repositório novo (git init e git clone)"
  # O template é copiado só na criação de um repositório: os já existentes não mudam.
  # Repositórios sem .pre-commit-config.yaml são ignorados pelo hook (--skip-on-missing-config).
  local template="$HOME/.git-template"
  git config --global init.templateDir "$template"
  pre-commit init-templatedir --hook-type pre-commit "$template" > /dev/null
  echo "Repositórios novos com .pre-commit-config.yaml já nascem com os hooks ativos."
}

configurar_keychain() {
  log "Ativando o agente SSH (keychain)"
  # Sem agente, a passphrase é pedida a cada pull, push e commit assinado. O keychain
  # guarda a chave destravada na memória por um tempo limitado; no disco, ela continua cifrada.
  # A detecção procura qualquer ativação do keychain, não só a do devkit, para respeitar
  # uma configuração manual já existente em vez de duplicá-la.
  if grep -qE 'keychain .*--eval' "$HOME/.bashrc" 2>/dev/null; then
    echo "Já configurado. Nada a fazer."
    if ! grep -qE 'keychain .*--timeout' "$HOME/.bashrc"; then
      aviso "O keychain do .bashrc não tem --timeout: a chave fica destravada até a distro desligar."
    fi
    return
  fi

  {
    printf '\n%s ---\n' "$DEVKIT_MARCADOR_KEYCHAIN"
    printf '# Passphrase pedida uma vez; a chave fica destravada na memória por %s minutos.\n' "$DEVKIT_KEYCHAIN_TIMEOUT_MIN"
    # shellcheck disable=SC2016  # $HOME e $(...) devem ficar literais, para rodar em cada terminal
    printf 'if [ -f "$HOME/.ssh/id_ed25519" ]; then eval "$(keychain --eval --quiet --timeout %s id_ed25519)"; fi\n' "$DEVKIT_KEYCHAIN_TIMEOUT_MIN"
  } >> "$HOME/.bashrc"
  echo "keychain ativado (timeout de $DEVKIT_KEYCHAIN_TIMEOUT_MIN minutos). Vale a partir do próximo terminal."
}

configurar_wsl_conf() {
  log "Desligando a importação do PATH do Windows"
  if grep -qF "appendWindowsPath" /etc/wsl.conf 2>/dev/null; then
    echo "Já configurado. Nada a fazer."
    return
  fi
  if [[ -f /etc/wsl.conf ]]; then
    sudo cp /etc/wsl.conf /etc/wsl.conf.backup
  fi
  printf '\n[interop]\nappendWindowsPath = false\n' | sudo tee -a /etc/wsl.conf > /dev/null
  echo "Bloco [interop] adicionado. Reinicie a distro para aplicar."
}

# Imprime a pasta bin do VS Code do usuário Windows atual (onde fica o script "code").
localizar_vscode_bin() {
  local usuario_windows
  # "|| true": se o cmd.exe falhar, o pipefail encerraria o script em silêncio aqui mesmo;
  # assim, a falha chega ao "if" abaixo, que explica o problema.
  usuario_windows="$("$DEVKIT_WINDOWS_ROOT/Windows/System32/cmd.exe" /c "echo %USERNAME%" 2>/dev/null | tr -d '\r' || true)"
  if [[ -z "$usuario_windows" ]]; then
    erro "Não foi possível descobrir o usuário do Windows."
    return 1
  fi

  local vscode_bin="$DEVKIT_WINDOWS_ROOT/Users/${usuario_windows}/AppData/Local/Programs/Microsoft VS Code/bin"
  if [[ ! -d "$vscode_bin" ]]; then
    erro "VS Code não encontrado em: $vscode_bin"
    return 1
  fi
  printf '%s\n' "$vscode_bin"
}

configurar_path_windows() {
  log "Liberando apenas o VS Code e o C:\\Windows no PATH"
  if grep -qF "$DEVKIT_MARCADOR_PATH" "$HOME/.bashrc" 2>/dev/null; then
    echo "Já configurado. Nada a fazer."
    return
  fi

  local vscode_bin
  vscode_bin="$(localizar_vscode_bin)" || return 1

  {
    printf '\n%s (appendWindowsPath = false) ---\n' "$DEVKIT_MARCADOR_PATH"
    # shellcheck disable=SC2016  # $PATH deve ficar literal, para ser expandido em cada terminal
    printf 'export PATH="$PATH:%s:%s/Windows"\n' "$vscode_bin" "$DEVKIT_WINDOWS_ROOT"
  } >> "$HOME/.bashrc"
  echo "PATH configurado: $vscode_bin"
}

instalar_node() {
  log "Instalando o nvm e o Node.js LTS"
  export NVM_DIR="$HOME/.nvm"
  # PATH local a esta função (e exportado para o instalador): sem as pastas do Windows,
  # o instalador do nvm não encontra o npm do Windows. As etapas seguintes voltam a ver
  # o PATH original, o que mantém a detecção de um docker vindo do Windows.
  local path_linux
  path_linux="$(filtrar_path_windows "$PATH")"
  local -x PATH="$path_linux"

  if [[ ! -d "$NVM_DIR" ]]; then
    curl -fsSL "https://raw.githubusercontent.com/nvm-sh/nvm/${DEVKIT_NVM_VERSION}/install.sh" | bash
  else
    echo "nvm já instalado."
  fi

  # O nvm.sh não é compatível com -e e -u: desligamos só durante o uso do nvm.
  set +eu
  # shellcheck source=/dev/null
  source "$NVM_DIR/nvm.sh"
  nvm install --lts
  nvm alias default 'lts/*'
  set -eu

  # Verificação explícita: não basta existir um "node"; ele precisa ser o do nvm
  # (um Node do Windows ou do sistema passaria numa checagem simples de existência).
  if [[ "$(command -v node || true)" != "$NVM_DIR"/* ]]; then
    erro "O Node.js ativo não é o instalado pelo nvm: $(command -v node || echo 'nenhum')"
    exit 1
  fi
  echo "Node $(node -v) | npm $(npm -v)"
}

verificar_docker() {
  log "Verificando o Docker (integração do Docker Desktop com o WSL)"
  # A integração é ativada no Docker Desktop (Windows), então aqui apenas verificamos
  # e orientamos: um Docker ausente não deve impedir o restante do ambiente.
  local caminho
  caminho="$(command -v docker || true)"

  if [[ -z "$caminho" ]]; then
    aviso "Docker não encontrado. Ative em Docker Desktop → Settings → Resources → WSL integration → ${WSL_DISTRO_NAME:-sua distro}."
    return
  fi
  if [[ "$caminho" == "$DEVKIT_WINDOWS_ROOT"/* ]]; then
    aviso "O docker em uso vem do Windows ($caminho). Ative a integração com o WSL no Docker Desktop."
    return
  fi
  # Um motor exposto via TCP sem TLS aceita comandos de qualquer programa da rede,
  # o que equivale a dar acesso de root na máquina.
  if [[ "${DOCKER_HOST:-}" == tcp://* && "${DOCKER_TLS_VERIFY:-}" != "1" ]]; then
    aviso "DOCKER_HOST=$DOCKER_HOST sem TLS: o motor do Docker fica acessível pela rede sem autenticação."
  fi
  if ! docker info > /dev/null 2>&1; then
    aviso "O comando docker existe, mas o motor não responde. Abra o Docker Desktop."
    return
  fi
  echo "Docker $(docker version --format '{{.Server.Version}}' 2>/dev/null) pronto ($caminho)."
}

verificar_vscode_wsl() {
  log "Verificando se o comando code abre conectado ao WSL"
  # O script "code" do Windows pergunta ao VS Code onde está a extensão WSL (--locate-extension),
  # e essa consulta olha só o perfil Default. Sem resposta, ele abre a pasta por \\wsl.localhost,
  # do lado do Windows (Git, Node e terminal do Windows). Aqui repetimos a mesma consulta.
  # Chamamos o script do Windows pelo caminho: no terminal do VS Code, o "code" do PATH é outro
  # (o remote CLI do VS Code Server), que não faz essa consulta.
  local vscode_bin
  if ! vscode_bin="$(localizar_vscode_bin 2>/dev/null)"; then
    aviso "VS Code não encontrado: não foi possível verificar se o comando code abre no WSL."
    return
  fi

  local vscode_dir="${vscode_bin%/bin}" versao cli
  # Desde 2026 o cli.js fica numa pasta com o início do commit (VERSIONFOLDER no script "code").
  versao="$(sed -n 's/^VERSIONFOLDER="\([^"]*\)"$/\1/p' "$vscode_bin/code" 2>/dev/null || true)"
  cli="$vscode_dir${versao:+/$versao}/resources/app/out/cli.js"
  if [[ ! -x "$vscode_dir/Code.exe" || ! -f "$cli" ]] || ! command -v wslpath > /dev/null; then
    aviso "Não foi possível verificar se o comando code abre no WSL (estrutura do VS Code não reconhecida)."
    return
  fi

  # WSLENV leva o ELECTRON_RUN_AS_NODE para o processo do Windows: sem ele, o Code.exe
  # abriria uma janela em vez de só responder à consulta.
  local extensao
  extensao="$(WSLENV="ELECTRON_RUN_AS_NODE/w${WSLENV:+:$WSLENV}" ELECTRON_RUN_AS_NODE=1 \
    timeout 60 "$vscode_dir/Code.exe" "$(wslpath -m "$cli")" --locate-extension ms-vscode-remote.remote-wsl \
    2> /dev/null < /dev/null | tr -d '\r' || true)"
  if [[ -z "$extensao" ]]; then
    aviso "A extensão WSL não está no perfil Default do VS Code: o comando code abriria a pasta pelo lado do Windows."
    aviso "Correção, no PowerShell: code --install-extension ms-vscode-remote.remote-wsl"
    return
  fi
  echo "Extensão WSL encontrada: o comando code abre conectado ao WSL."
}

lembrar_passos_manuais() {
  cat <<'EOF'

✅ Setup automático concluído. Passos manuais (de propósito):
  1. ssh-keygen -t ed25519 -C "$(hostname)-wsl" -f ~/.ssh/id_ed25519
  2. Cadastrar a chave pública no GitHub como Authentication e Signing Key
  3. ssh -T git@github.com e conferir a fingerprint oficial do GitHub
  4. Rodar o script de novo para ativar a assinatura de commits
  5. No PowerShell: wsl --terminate <distro> para aplicar o wsl.conf
  6. Docker Desktop → Settings → Resources → WSL integration → ativar esta distro
  7. Em repositórios já clonados que tenham .pre-commit-config.yaml: pre-commit install
EOF
}

main() {
  verificar_ambiente
  instalar_pacotes
  configurar_git
  configurar_pre_commit
  configurar_keychain
  configurar_wsl_conf
  configurar_path_windows
  instalar_node
  verificar_docker
  verificar_vscode_wsl
  lembrar_passos_manuais
}

# Executa só quando chamado diretamente (./setup.sh). Com "source setup.sh",
# apenas as funções são carregadas, o que permite testá-las individualmente.
if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  main "$@"
fi
