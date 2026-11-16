#!/usr/bin/env bash
# secure-wsl-devkit — setup automatizado e seguro do ambiente de desenvolvimento no WSL 2
# Idempotente: pode ser executado várias vezes sem duplicar configurações.
set -euo pipefail

# ===== Configuração =====
readonly DEVKIT_GIT_NAME="ADSLustosa"
readonly DEVKIT_GIT_EMAIL="161537433+ADSLustosa@users.noreply.github.com"
readonly DEVKIT_NVM_VERSION="v0.40.3"
readonly DEVKIT_MARCADOR_PATH="# --- Caminhos do Windows liberados manualmente"

# ===== Funções auxiliares =====
log() { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
erro() { printf '\033[1;31mERRO: %s\033[0m\n' "$*" >&2; }

# ===== Etapas =====
verificar_ambiente() {
  log "Verificando o ambiente"
  if [[ $EUID -eq 0 ]]; then
    erro "Não execute como root (sem sudo). O script pede a senha quando precisar."
    exit 1
  fi
  if ! grep -qi microsoft /proc/version; then
    erro "Este script foi feito para o WSL 2."
    exit 1
  fi
  echo "Usuário: $USER | Distro: ${WSL_DISTRO_NAME:-desconhecida}"
}

instalar_pacotes() {
  log "Atualizando o sistema e instalando pacotes base"
  sudo apt-get update
  sudo DEBIAN_FRONTEND=noninteractive apt-get upgrade -y
  sudo apt-get install -y build-essential curl unzip keychain shellcheck
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

configurar_path_windows() {
  log "Liberando apenas o VS Code e o C:\\Windows no PATH"
  if grep -qF "$DEVKIT_MARCADOR_PATH" "$HOME/.bashrc"; then
    echo "Já configurado. Nada a fazer."
    return
  fi

  local usuario_windows
  usuario_windows="$(/mnt/c/Windows/System32/cmd.exe /c "echo %USERNAME%" 2>/dev/null | tr -d '\r')"
  if [[ -z "$usuario_windows" ]]; then
    erro "Não foi possível descobrir o usuário do Windows."
    return 1
  fi

  local vscode_bin="/mnt/c/Users/${usuario_windows}/AppData/Local/Programs/Microsoft VS Code/bin"
  if [[ ! -d "$vscode_bin" ]]; then
    erro "VS Code não encontrado em: $vscode_bin"
    return 1
  fi

  {
    printf '\n%s (appendWindowsPath = false) ---\n' "$DEVKIT_MARCADOR_PATH"
    # shellcheck disable=SC2016  # $PATH deve ficar literal, para ser expandido em cada terminal
    printf 'export PATH="$PATH:%s:/mnt/c/Windows"\n' "$vscode_bin"
  } >> "$HOME/.bashrc"
  echo "PATH configurado para o usuário Windows: $usuario_windows"
}

instalar_node() {
  log "Instalando o nvm e o Node.js LTS"
  export NVM_DIR="$HOME/.nvm"

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

  # Verificação explícita: não confiamos só na ausência de erro.
  if ! command -v node > /dev/null; then
    erro "Node.js não foi instalado corretamente."
    exit 1
  fi
  echo "Node $(node -v) | npm $(npm -v)"
}

lembrar_passos_manuais() {
  cat <<'EOF'

✅ Setup automático concluído. Passos manuais (de propósito):
  1. ssh-keygen -t ed25519 -C "$(hostname)-wsl" -f ~/.ssh/id_ed25519
  2. Cadastrar a chave pública no GitHub como Authentication e Signing Key
  3. ssh -T git@github.com e conferir a fingerprint oficial do GitHub
  4. Rodar o script de novo para ativar a assinatura de commits
  5. No PowerShell: wsl --terminate <distro> para aplicar o wsl.conf
EOF
}

main() {
  verificar_ambiente
  instalar_pacotes
  configurar_git
  configurar_wsl_conf
  configurar_path_windows
  instalar_node
  lembrar_passos_manuais
}

main "$@"
