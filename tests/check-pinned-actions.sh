#!/usr/bin/env bash
# Garante que toda action usada nos workflows esteja fixada pelo SHA completo de um commit.
# Tags como @v5 são móveis: o dono do repositório pode apontá-las para outro código a qualquer momento.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

# Linhas "uses:" que NÃO terminam em @<40 caracteres hexadecimais>.
# Actions locais (./) e imagens Docker (docker://) não têm tag e ficam de fora.
mapfile -t sem_sha < <(
  grep -HnE '^[[:space:]]*(-[[:space:]]*)?uses:' .github/workflows/*.yml |
    grep -vE 'uses:[[:space:]]*(\./|docker://)' |
    grep -vE 'uses:[[:space:]]*[^@[:space:]]+@[0-9a-f]{40}([[:space:]]|$)' || true
)

if (( ${#sem_sha[@]} > 0 )); then
  for linha in "${sem_sha[@]}"; do
    echo "::error::Action sem SHA fixado: $linha"
  done
  echo "Fixe cada action pelo SHA do commit, com a versão em comentário. Ex.: uses: dono/action@<sha> # v1.2.3" >&2
  exit 1
fi
echo "Todas as actions estão fixadas por SHA."
