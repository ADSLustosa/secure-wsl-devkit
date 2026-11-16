#!/usr/bin/env bash
# Teste de integração: executa o setup.sh duas vezes em um Ubuntu zerado (runner do GitHub Actions)
# com um WSL simulado e verifica a idempotência, o resultado final e as guardas de segurança.
set -euo pipefail

if [[ "${CI:-}" != "true" ]]; then
  echo "Este teste altera o sistema (apt, /etc/wsl.conf, ~/.bashrc) e só deve rodar no CI." >&2
  exit 1
fi

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
readonly RAIZ
readonly FAKE="${RUNNER_TEMP:-/tmp}/fake-wsl"
readonly USUARIO_WINDOWS="ci-user"
FALHAS=0

# ===== Auxiliares =====
# ::group:: e ::error:: são comandos de log do GitHub Actions (grupos recolhíveis e anotações de erro).
grupo() { echo "::group::$*"; }
fim_grupo() { echo "::endgroup::"; }
ok() { printf '\033[1;32m✔ %s\033[0m\n' "$*"; }
falha() { echo "::error::$*"; FALHAS=$((FALHAS + 1)); }

esperar_igual() {  # descrição, valor obtido, valor esperado
  if [[ "$2" == "$3" ]]; then ok "$1"; else falha "$1 (obtido: '$2', esperado: '$3')"; fi
}

esperar_bloqueio() {  # descrição, mensagem esperada, comando...
  local descricao="$1" mensagem="$2" saida
  shift 2
  if saida="$("$@" 2>&1)"; then
    falha "$descricao: o setup.sh deveria ter sido interrompido"
  elif grep -qF "$mensagem" <<< "$saida"; then
    ok "$descricao"
  else
    falha "$descricao: interrompido pelo motivo errado: $saida"
  fi
}

# ===== Etapas do teste =====
simular_wsl() {
  grupo "Simulando o ambiente WSL"
  local vscode="$FAKE/c/Users/$USUARIO_WINDOWS/AppData/Local/Programs/Microsoft VS Code/bin"
  mkdir -p "$FAKE/c/Windows/System32" "$vscode"

  # Simula o cmd.exe respondendo ao "echo %USERNAME%" com o final de linha do Windows (CRLF),
  # para provar que o setup.sh remove o \r invisível.
  cat > "$FAKE/c/Windows/System32/cmd.exe" <<EOF
#!/usr/bin/env bash
printf '%s\r\n' "$USUARIO_WINDOWS"
EOF
  chmod +x "$FAKE/c/Windows/System32/cmd.exe"

  echo "Linux version 6.18.0-microsoft-standard-WSL2 (simulado)" > "$FAKE/proc-version-wsl"
  echo "Linux version 6.18.0-generic (simulado)" > "$FAKE/proc-version-linux"

  export DEVKIT_WINDOWS_ROOT="$FAKE/c"
  export DEVKIT_PROC_VERSION="$FAKE/proc-version-wsl"
  ok "WSL simulado em $FAKE"
  fim_grupo
}

testar_guardas() {
  grupo "Testes negativos: as guardas devem interromper o script"
  esperar_bloqueio "recusa executar como root" "Não execute como root" \
    sudo --preserve-env=DEVKIT_WINDOWS_ROOT,DEVKIT_PROC_VERSION "$RAIZ/setup.sh"
  esperar_bloqueio "recusa executar fora do WSL" "feito para o WSL 2" \
    env DEVKIT_PROC_VERSION="$FAKE/proc-version-linux" "$RAIZ/setup.sh"
  fim_grupo
}

executar_duas_vezes() {
  grupo "Primeira execução (máquina zerada)"
  "$RAIZ/setup.sh"
  fim_grupo

  grupo "Segunda execução (idempotência)"
  "$RAIZ/setup.sh" | tee "$FAKE/segunda-execucao.log"
  fim_grupo
}

verificar_resultado() {
  grupo "Verificações do resultado"
  local log="$FAKE/segunda-execucao.log"

  esperar_igual "wsl.conf com um único appendWindowsPath" "$(grep -c appendWindowsPath /etc/wsl.conf || true)" "1"
  esperar_igual ".bashrc com um único bloco de PATH" "$(grep -c "Caminhos do Windows liberados" "$HOME/.bashrc" || true)" "1"
  esperar_igual "PATH aponta para o VS Code do usuário Windows" "$(grep -c "Users/$USUARIO_WINDOWS/AppData" "$HOME/.bashrc" || true)" "1"
  esperar_igual "nenhum \\r (CRLF) gravado no .bashrc" "$(grep -c $'\r' "$HOME/.bashrc" || true)" "0"
  esperar_igual "segunda execução detectou as etapas já feitas" "$(grep -c "Já configurado" "$log" || true)" "2"

  esperar_igual "Git: branch padrão main" "$(git config --global init.defaultBranch)" "main"
  esperar_igual "Git: pull com rebase" "$(git config --global pull.rebase)" "true"
  esperar_igual "Git: fetch.prune ativo" "$(git config --global fetch.prune)" "true"
  esperar_igual "Git: assinatura adiada sem chave SSH" "$(git config --global --get commit.gpgsign || echo ausente)" "ausente"

  if command -v shellcheck > /dev/null; then ok "shellcheck instalado"; else falha "shellcheck não instalado"; fi

  # O runner já tem um Node do sistema: conferimos o CAMINHO, não só a existência.
  local caminho_node
  # shellcheck disable=SC2016  # $HOME deve ser expandido pelo bash filho, não aqui
  caminho_node="$(bash -c 'source "$HOME/.nvm/nvm.sh" && command -v node' 2>/dev/null || true)"
  if [[ "$caminho_node" == "$HOME/.nvm/"* ]]; then
    ok "Node.js LTS ativo vem do nvm ($caminho_node)"
  else
    falha "Node.js ativo não vem do nvm: '${caminho_node:-nenhum}'"
  fi
  fim_grupo
}

main() {
  simular_wsl
  testar_guardas
  executar_duas_vezes
  verificar_resultado

  if (( FALHAS > 0 )); then
    echo "::error::$FALHAS verificação(ões) falharam."
    exit 1
  fi
  ok "Todas as verificações passaram."
}

main "$@"
