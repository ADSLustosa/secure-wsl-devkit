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
readonly NPM_WINDOWS="$FAKE/c/Users/$USUARIO_WINDOWS/AppData/Local/nvm/v24.21.0"
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

esperar_saida() {  # descrição, texto esperado na saída, comando...
  local descricao="$1" texto="$2" saida
  shift 2
  saida="$("$@" 2>&1 || true)"
  if grep -qF "$texto" <<< "$saida"; then ok "$descricao"; else falha "$descricao: saída inesperada: $saida"; fi
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

  # Simula o npm do nvm-windows vazando para o Linux, como na primeira execução real
  # (antes de reiniciar a distro). Se alguém o executar, ele deixa um marcador.
  # Ele responde ao "npm list -g" com o mesmo módulo visto no desktop: é essa lista
  # que faz o instalador do nvm imprimir o aviso "installed globally".
  mkdir -p "$NPM_WINDOWS"
  cat > "$NPM_WINDOWS/npm" <<EOF
#!/usr/bin/env bash
touch "$FAKE/npm-do-windows-executado"
case "\$1" in
  list | ls) printf '%s\n' 'C:\\Users\\$USUARIO_WINDOWS\\AppData\\Local\\nvm\\v24.21.0' '├── corepack@0.36.0' ;;
  *) echo 10.0.0 ;;
esac
EOF
  chmod +x "$NPM_WINDOWS/npm"

  export DEVKIT_WINDOWS_ROOT="$FAKE/c"
  export DEVKIT_PROC_VERSION="$FAKE/proc-version-wsl"
  ok "WSL simulado em $FAKE"
  fim_grupo
}

testar_filtro_path() {
  grupo "Filtro do PATH: nada do Windows chega ao instalador do nvm"
  # Mesmo padrão do testar_docker: carrega só as funções do setup.sh.
  local entrada="/usr/bin:/mnt/c/Windows:/mnt/d/tools::$DEVKIT_WINDOWS_ROOT/Users/x:/home/dev/bin:/mnty/ok"
  # shellcheck disable=SC2016  # $1 e $2 são expandidos pelo bash filho
  esperar_igual "remove /mnt/<letra>, a raiz simulada e entradas vazias" \
    "$(bash -c 'source "$1"; filtrar_path_windows "$2"' filtro "$RAIZ/setup.sh" "$entrada")" \
    "/usr/bin:/home/dev/bin:/mnty/ok"
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
  grupo "Primeira execução (máquina zerada, com o npm do Windows no PATH)"
  PATH="$NPM_WINDOWS:$PATH" "$RAIZ/setup.sh" 2>&1 | tee "$FAKE/primeira-execucao.log"
  fim_grupo

  grupo "Segunda execução (idempotência)"
  "$RAIZ/setup.sh" 2>&1 | tee "$FAKE/segunda-execucao.log"
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

  # O npm do Windows estava no PATH da primeira execução: o instalador do nvm não pode tê-lo visto.
  if [[ -e "$FAKE/npm-do-windows-executado" ]]; then
    falha "o npm do Windows foi executado durante o setup"
  else
    ok "o npm do Windows não foi executado"
  fi
  esperar_igual "nvm não detectou módulos globais do Windows" \
    "$(grep -c "installed globally" "$FAKE/primeira-execucao.log" || true)" "0"

  esperar_igual "Git: branch padrão main" "$(git config --global init.defaultBranch)" "main"
  esperar_igual "Git: pull com rebase" "$(git config --global pull.rebase)" "true"
  esperar_igual "Git: fetch.prune ativo" "$(git config --global fetch.prune)" "true"
  esperar_igual "Git: assinatura adiada sem chave SSH" "$(git config --global --get commit.gpgsign || echo ausente)" "ausente"

  if command -v shellcheck > /dev/null; then ok "shellcheck instalado"; else falha "shellcheck não instalado"; fi
  if command -v pre-commit > /dev/null; then ok "pre-commit instalado ($(pre-commit --version))"; else falha "pre-commit não instalado"; fi
  esperar_igual "Git: template de hooks configurado" "$(git config --global init.templateDir)" "$HOME/.git-template"

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

testar_docker() {
  grupo "Verificação do Docker: um cenário por situação"
  local bin="$FAKE/docker-bin" win="$DEVKIT_WINDOWS_ROOT/Program Files/Docker/resources/bin"
  mkdir -p "$bin/ok" "$bin/parado" "$bin/vazio" "$win"

  # Docker simulado e funcionando
  # shellcheck disable=SC2016  # o $1 é conteúdo do docker simulado, lido quando ele for executado
  printf '#!/usr/bin/env bash\n[[ "$1" == version ]] && echo 29.0.0\nexit 0\n' > "$bin/ok/docker"
  # Comando presente, mas motor desligado
  printf '#!/usr/bin/env bash\nexit 1\n' > "$bin/parado/docker"
  # Docker do Windows vazando para o Linux
  cp "$bin/ok/docker" "$win/docker"
  chmod +x "$bin/ok/docker" "$bin/parado/docker" "$win/docker"

  # Carrega só as funções do setup.sh (guarda de source) e executa a verificação.
  # O caminho vai em $1, e não em $0: a guarda compara $0 com o arquivo carregado,
  # e passá-lo como $0 faria o setup.sh se comportar como se tivesse sido executado.
  # O bash é chamado pelo caminho absoluto para que o cenário "ausente" use um PATH vazio,
  # garantindo que nenhum docker do próprio ambiente de teste seja encontrado.
  # shellcheck disable=SC2016  # o $1 deve ser expandido pelo bash filho, que recebe o caminho do setup.sh
  local chamar=("$(command -v bash)" -c 'source "$1"; verificar_docker' verificar-docker "$RAIZ/setup.sh")
  esperar_saida "Docker ausente gera orientação" "Docker não encontrado" env PATH="$bin/vazio" "${chamar[@]}"
  esperar_saida "Docker do Windows é detectado" "vem do Windows" env PATH="$win:/usr/bin:/bin" "${chamar[@]}"
  esperar_saida "Motor desligado é detectado" "motor não responde" env PATH="$bin/parado:/usr/bin:/bin" "${chamar[@]}"
  esperar_saida "Docker funcionando é reconhecido" "pronto" env PATH="$bin/ok:/usr/bin:/bin" "${chamar[@]}"
  esperar_saida "DOCKER_HOST sem TLS gera alerta" "sem TLS" \
    env PATH="$bin/ok:/usr/bin:/bin" DOCKER_HOST=tcp://localhost:2375 "${chamar[@]}"
  fim_grupo
}

testar_pre_commit() {
  grupo "pre-commit + Gitleaks: um segredo não pode chegar a um commit"
  local repo="$FAKE/repo-teste" segredo
  rm -rf "$repo"
  git init -q "$repo"

  if [[ -x "$repo/.git/hooks/pre-commit" ]]; then
    ok "git init já criou o hook (template global)"
  else
    falha "o hook não foi criado pelo template"
  fi

  cp "$RAIZ/.pre-commit-config.yaml" "$repo/"
  git -C "$repo" add .pre-commit-config.yaml
  # O primeiro commit faz o pre-commit baixar o Go e compilar o Gitleaks na versão fixada.
  if git -C "$repo" commit -q -m "chore: configura o pre-commit"; then
    ok "commit sem segredo é aceito (hooks instalados e executados)"
  else
    falha "o commit da configuração foi recusado"
  fi

  # Token no formato de um GitHub PAT, gerado na hora: o literal "ghp_" + 36 caracteres
  # nunca aparece neste arquivo, para não ser detectado no próprio repositório.
  local prefixo="ghp"
  segredo="${prefixo}_$(od -An -tx1 -N18 /dev/urandom | tr -d ' \n')"
  printf 'GITHUB_TOKEN=%s\n' "$segredo" > "$repo/config.env"
  git -C "$repo" add config.env

  local antes depois
  antes="$(git -C "$repo" rev-list --count HEAD)"
  if git -C "$repo" commit -q -m "feat: adiciona configuração" > "$FAKE/commit-segredo.log" 2>&1; then
    falha "o commit com um token foi ACEITO"
  else
    ok "commit com token bloqueado pelo Gitleaks"
  fi
  depois="$(git -C "$repo" rev-list --count HEAD)"
  esperar_igual "o histórico não recebeu o commit" "$depois" "$antes"
  esperar_igual "o token não aparece no log do bloqueio (--redact)" "$(grep -cF "$segredo" "$FAKE/commit-segredo.log" || true)" "0"
  fim_grupo
}

main() {
  simular_wsl
  testar_docker
  testar_filtro_path
  testar_guardas
  executar_duas_vezes
  verificar_resultado
  testar_pre_commit

  if (( FALHAS > 0 )); then
    echo "::error::$FALHAS verificação(ões) falharam."
    exit 1
  fi
  ok "Todas as verificações passaram."
}

main "$@"
