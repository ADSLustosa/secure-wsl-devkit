<div align="center">

# 🛡️ secure-wsl-devkit

**Setup automatizado, idempotente e com foco em segurança para um ambiente de desenvolvimento no WSL 2.**

Um script. O mesmo ambiente em todas as máquinas. Nenhum vazamento entre Windows e Linux.

[![ShellCheck](https://github.com/ADSLustosa/secure-wsl-devkit/actions/workflows/shellcheck.yml/badge.svg)](https://github.com/ADSLustosa/secure-wsl-devkit/actions/workflows/shellcheck.yml)
![Plataforma](https://img.shields.io/badge/plataforma-WSL%202-0078D6?logo=windows&logoColor=white)
![Ubuntu](https://img.shields.io/badge/Ubuntu-26.04%20LTS-E95420?logo=ubuntu&logoColor=white)
![Bash](https://img.shields.io/badge/Bash-script-4EAA25?logo=gnubash&logoColor=white)
![Conventional Commits](https://img.shields.io/badge/Conventional%20Commits-1.0.0-FE5196?logo=conventionalcommits&logoColor=white)
[![Licença: MIT](https://img.shields.io/badge/licen%C3%A7a-MIT-blue.svg)](LICENSE)

🇺🇸 [English](README.md) · 🇧🇷 Português

</div>

---

## 📌 Por que este projeto existe

Configurar o WSL 2 manualmente em mais de um computador causa três problemas silenciosos:

| Problema | Impacto real |
|---|---|
| **O PATH do Windows vaza para o Linux** | Por padrão, o WSL importa todas as pastas do Windows para o `PATH` do Linux. Comandos como `npm` podem executar, sem aviso, o programa **do Windows** dentro do Linux, causando erros difíceis de diagnosticar e deixando o terminal mais lento. |
| **Os ambientes divergem** | Passos manuais são esquecidos ou feitos de forma diferente em cada máquina, e o código que funciona no notebook quebra no desktop. |
| **Identidade não verificável** | Qualquer pessoa pode fazer commits usando seu nome e e-mail. Sem commits assinados, não há prova de que um commit veio de você. |

O `secure-wsl-devkit` resolve os três com um único script, que pode ser executado com segurança quantas vezes for necessário.

## ✨ Destaques

- 🔁 **Idempotente** — rodar duas vezes produz o mesmo resultado que rodar uma. Nada é duplicado.
- 🔐 **PATH com menor privilégio** — em vez de importar dezenas de pastas do Windows, apenas **2** são liberadas explicitamente.
- ✍️ **Commits assinados** — o Git assina cada commit via SSH, exibindo o selo **Verified** no GitHub.
- 🛑 **Fail fast** — `set -euo pipefail` interrompe a execução no primeiro erro inesperado.
- 🧪 **Verificação explícita** — o script confere os resultados em vez de confiar apenas na ausência de erros.
- 🤖 **Integração contínua** — todo pull request passa por análise estática com o ShellCheck.

## ⚙️ Como funciona

```mermaid
flowchart TD
    A([./setup.sh]) --> B{Executando como root<br/>ou fora do WSL?}
    B -- sim --> X([❌ Interrompe])
    B -- não --> C[Atualiza o sistema e instala os pacotes base]
    C --> D[Configura o Git]
    D --> E{Chave SSH existe?}
    E -- sim --> F[Ativa a assinatura de commits]
    E -- não --> G[Adia a assinatura para a próxima execução]
    F --> H{wsl.conf já configurado?}
    G --> H
    H -- não --> I[Desliga a importação do PATH do Windows]
    H -- sim --> J
    I --> J{Liberação do PATH já está no .bashrc?}
    J -- não --> K[Libera apenas o VS Code e o C:\Windows]
    J -- sim --> L
    K --> L[Instala o nvm + Node.js LTS]
    L --> M{node disponível?}
    M -- não --> X
    M -- sim --> N([✅ Exibe os passos manuais])
```

Cada **losango** é uma verificação de idempotência: a etapa só é executada quando a configuração ainda não existe.

## 🧰 O que é configurado

| Etapa | O que faz | Por quê |
|---|---|---|
| Verificação do ambiente | Bloqueia a execução como `root` e fora do WSL | Evita configurar o usuário ou o sistema errado |
| Pacotes base | `build-essential`, `curl`, `unzip`, `keychain`, `shellcheck` | Compiladores para módulos nativos do Node, agente SSH e análise de scripts |
| Git | Identidade, `main` como branch padrão, `pull.rebase`, `autocrlf input`, `fetch.prune` | Histórico linear, quebras de linha no padrão Linux e lista de branches sempre limpa |
| Assinatura de commits | `gpg.format ssh`, chave de assinatura e `allowed_signers` | Prova criptográfica de autoria |
| `wsl.conf` | `appendWindowsPath = false` | Impede que o PATH do Windows vaze para o Linux |
| Liberação do PATH | Apenas o VS Code e o `C:\Windows` | Mantém o `code .` e o `explorer.exe .` funcionando, e nada além disso |
| Node.js | `nvm` + versão LTS mais recente | Versões de Node por projeto, sem `sudo` |

## 🔐 Decisões de segurança

| Decisão | Justificativa |
|---|---|
| **A geração da chave SSH é manual, de propósito** | Cada máquina tem sua própria chave. Se um dispositivo for perdido, apenas aquela chave é revogada. Chaves privadas nunca são copiadas nem automatizadas. |
| **A fingerprint do GitHub é conferida manualmente** | Aceitar uma fingerprint desconhecida sem conferir abre caminho para ataques *man-in-the-middle*. |
| **E-mail `noreply` nos commits** | Os commits continuam vinculados à conta do GitHub sem expor um e-mail pessoal a robôs de coleta. |
| **Versão fixa do instalador do nvm** | A URL aponta para uma versão específica, e não para a "mais recente", que poderia mudar sem aviso. |
| **`curl -fsSL`** | O `-f` faz erros HTTP falharem, então uma página de erro nunca é executada pelo `bash`. |
| **Variáveis com prefixo (`DEVKIT_`)** | Evita colisões com variáveis de scripts carregados via `source`, como o `nvm.sh`. |
| **Token do CI somente leitura** | O workflow declara `permissions: contents: read`, seguindo o princípio do menor privilégio. |
| **Nenhum segredo no repositório** | Senhas, *passphrases* e tokens ficam em um gerenciador de senhas, nunca no código. |

## 🚀 Como usar

### Requisitos

- Windows 10/11 com **WSL 2**
- Uma distribuição **Ubuntu** (testado no 26.04 LTS)
- **VS Code** instalado no Windows

### 1. Clonar e executar

Em uma máquina nova ainda não existe chave SSH, então clone via **HTTPS**:

```bash
mkdir -p ~/projetos && cd ~/projetos
git clone https://github.com/ADSLustosa/secure-wsl-devkit.git
cd secure-wsl-devkit
./setup.sh
```

> ⚠️ Não execute com `sudo`. O script pede a senha apenas quando precisa.

### 2. Passos manuais (intencionais)

```bash
# Gera uma chave exclusiva desta máquina
ssh-keygen -t ed25519 -C "$(hostname)-wsl" -f ~/.ssh/id_ed25519

# Exibe a chave pública para cadastrar no GitHub
cat ~/.ssh/id_ed25519.pub
```

1. No GitHub, acesse **Settings → SSH and GPG keys** e cadastre a chave **duas vezes**: como *Authentication Key* e como *Signing Key*.
2. Rode `ssh -T git@github.com` e compare a fingerprint com as [fingerprints oficiais do GitHub](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/githubs-ssh-key-fingerprints). Você pode colar o valor oficial como resposta, e o SSH faz a comparação por você.
3. Execute `./setup.sh` novamente para ativar a assinatura de commits.
4. No **PowerShell**, reinicie apenas esta distribuição para aplicar o `wsl.conf`:

```powershell
wsl --terminate Ubuntu-26.04
```

## ✅ Verificando o resultado

```bash
# Apenas o VS Code e o C:\Windows devem vir de /mnt/c
echo "$PATH" | tr ':' '\n' | grep '^/mnt/'

# node e npm devem vir de ~/.nvm, nunca de /mnt/c
command -v node npm

# Idempotência: ambos devem exibir 1, mesmo após várias execuções
grep -c "appendWindowsPath" /etc/wsl.conf
grep -c "Caminhos do Windows liberados" ~/.bashrc

# Verificação da assinatura do último commit de qualquer repositório
git log --show-signature -1
```

## 📁 Estrutura do projeto

```
secure-wsl-devkit/
├── .github/
│   └── workflows/
│       └── shellcheck.yml   # CI: análise estática a cada push e pull request
├── setup.sh                 # Script de setup idempotente
├── LICENSE
├── README.md                # English
└── README.pt-BR.md          # Português
```

## 🗺️ Roadmap

- [x] Script de setup idempotente
- [x] Commits assinados via SSH
- [x] Liberação seletiva do PATH do Windows
- [x] ShellCheck no CI
- [ ] Validar o script em uma distribuição zerada no CI
- [ ] Configuração do runtime de contêineres (integração do Docker Desktop com o WSL)
- [ ] Varredura de segredos antes de cada commit com Gitleaks + pre-commit
- [ ] Fixar as GitHub Actions pelo SHA do commit, com atualizações via Dependabot

## 📄 Licença

Distribuído sob a licença MIT. Consulte o arquivo [LICENSE](LICENSE) para mais detalhes.

---

<div align="center">

Desenvolvido por **[ADSLustosa](https://github.com/ADSLustosa)** · Desenvolvedor full-stack com foco em segurança e proteção de dados (LGPD)

</div>
