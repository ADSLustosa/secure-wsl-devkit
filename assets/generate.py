#!/usr/bin/env python3
"""Generate the animated SVG assets used by the README files.

Usage (from the repository root):
    python3 assets/generate.py

Only the Python standard library is used. Every asset follows three rules:
  1. No scripts and no external resources (GitHub serves README images
     as plain images, so only SVG + CSS animations work).
  2. The static state is the final state, so viewers with
     "prefers-reduced-motion" see the complete image without animation.
  3. Each image carries <title> and <desc> for screen readers.
"""
from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path(__file__).resolve().parent

SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, 'Cascadia Code', Consolas, 'DejaVu Sans Mono', 'Liberation Mono', monospace"
REDUCED_MOTION = "@media (prefers-reduced-motion: reduce) { * { animation: none !important; } }"

THEMES = {
    "dark": {
        "bg": "#0d1117", "panel": "#161b22", "border": "#30363d", "grid": "#1c2129",
        "text": "#e6edf3", "muted": "#8b949e", "accent": "#22d3ee", "accent2": "#a78bfa",
        "green": "#3fb950", "red": "#f85149", "shine": "#ffffff",
    },
    "light": {
        "bg": "#ffffff", "panel": "#f6f8fa", "border": "#d0d7de", "grid": "#eef1f4",
        "text": "#1f2328", "muted": "#59636e", "accent": "#0e7490", "accent2": "#7c3aed",
        "green": "#1a7f37", "red": "#cf222e", "shine": "#22d3ee",
    },
}

TEXTS = {
    "en": {
        "tagline": "Automated, idempotent and security-first WSL 2 setup",
        "chips": ["idempotent", "signed commits", "least privilege"],
        "banner_desc": "Project banner: a shield with a check mark, the project name and its main features.",
        "impact_title": "Measured impact",
        "impact_sub": "Real numbers from the diagnostic of the author's machine, before and after setup.sh",
        "impact_desc": "Before and after: Windows folders in the Linux PATH went from 32 to 2, Windows binaries "
                       "shadowing Linux tools went from 3 to 0, and signed commits went from 0% to 100%.",
        "cards": [
            ("32", "2", "Windows folders in the Linux PATH", "only VS Code + C:\\Windows remain", 1.0, 2 / 32, "accent"),
            ("3", "0", "Windows binaries shadowing Linux", "npm · npx · docker", 1.0, 0.0, "accent"),
            ("0%", "100%", "Signed and verified commits", "SSH signature · Verified badge", 0.0, 1.0, "green"),
        ],
        "flow_title": "How setup.sh works",
        "flow_sub": "Every step either runs or detects the existing configuration, so it is safe to repeat",
        "flow_desc": "Seven steps run in order: check environment, base packages, Git and signing, cut the Windows PATH, "
                     "PATH allowlist, Node.js LTS and Docker check. The first three always run, the next three are skipped "
                     "when already done, and the Docker step only checks and warns.",
        "flow_steps": [
            ("Environment", "root? WSL 2?", "always"),
            ("Base packages", "apt-get", "always"),
            ("Git + signing", "git config", "always"),
            ("Cut Win PATH", "/etc/wsl.conf", "skip"),
            ("PATH allowlist", "~/.bashrc", "skip"),
            ("Node.js LTS", "nvm", "skip"),
            ("Docker", "docker info", "check"),
        ],
        "flow_always": "runs always",
        "flow_skip": "skips if done",
        "flow_check": "checks, warns",
        "gates_title": "Every change passes four gates",
        "gates_sub": "A signed commit reaches main only through a pull request with a green CI; a direct push is rejected",
        "gates_desc": "A signed commit passes four gates (signed commit, pull request only, ShellCheck CI and verified "
                      "commits only) and reaches the protected main branch. A direct push is rejected at the pull request gate.",
        "gates": [("Signed commit", "ssh-ed25519"), ("Pull request only", "ruleset"),
                  ("ShellCheck CI", "github actions"), ("Verified only", "ruleset")],
        "gates_ok": "✓ commit",
        "gates_bad": "✕ direct push",
        "gates_blocked": "rejected: changes must go through a pull request",
        "gates_target": "protected",
        "road_sub": "{done} of {total} milestones delivered · next: {next}",
        "road_items": [
            ("Idempotent setup", True), ("Signed commits", True), ("PATH allowlist", True),
            ("CI + protected main", True), ("Animated docs", True), ("Fresh-distro CI", True),
            ("Container runtime", True), ("Gitleaks", False), ("Pinned actions", False),
        ],
    },
    "pt": {
        "tagline": "Setup do WSL 2 automatizado, idempotente e seguro",
        "chips": ["idempotente", "commits assinados", "menor privilégio"],
        "banner_desc": "Banner do projeto: um escudo com um sinal de confirmação, o nome do projeto e suas principais características.",
        "impact_title": "Impacto medido",
        "impact_sub": "Números reais do diagnóstico da máquina do autor, antes e depois do setup.sh",
        "impact_desc": "Antes e depois: as pastas do Windows no PATH do Linux caíram de 32 para 2, os programas do Windows "
                       "que sobrepunham os do Linux caíram de 3 para 0, e os commits assinados foram de 0% para 100%.",
        "cards": [
            ("32", "2", "Pastas do Windows no PATH do Linux", "restam só o VS Code e o C:\\Windows", 1.0, 2 / 32, "accent"),
            ("3", "0", "Binários do Windows sobrepondo o Linux", "npm · npx · docker", 1.0, 0.0, "accent"),
            ("0%", "100%", "Commits assinados e verificados", "assinatura SSH · selo Verified", 0.0, 1.0, "green"),
        ],
        "flow_title": "Como o setup.sh funciona",
        "flow_sub": "Cada etapa executa ou detecta a configuração existente, por isso é seguro repetir",
        "flow_desc": "Sete etapas em ordem: verificação do ambiente, pacotes base, Git e assinatura, corte do PATH do Windows, "
                     "liberação do VS Code, Node.js LTS e verificação do Docker. As três primeiras sempre executam, as três "
                     "seguintes são puladas quando já feitas, e a do Docker apenas verifica e avisa.",
        "flow_steps": [
            ("Ambiente", "root? WSL 2?", "always"),
            ("Pacotes base", "apt-get", "always"),
            ("Git + assinat.", "git config", "always"),
            ("Corta PATH Win", "/etc/wsl.conf", "skip"),
            ("Libera VS Code", "~/.bashrc", "skip"),
            ("Node.js LTS", "nvm", "skip"),
            ("Docker", "docker info", "check"),
        ],
        "flow_always": "roda sempre",
        "flow_skip": "pula se pronto",
        "flow_check": "verifica, avisa",
        "gates_title": "Toda mudança passa por quatro portões",
        "gates_sub": "Um commit assinado só chega à main por pull request com CI verde; um push direto é recusado",
        "gates_desc": "Um commit assinado passa por quatro portões (commit assinado, somente pull request, CI com ShellCheck e "
                      "somente commits verificados) e chega à branch main protegida. Um push direto é recusado no portão do pull request.",
        "gates": [("Commit assinado", "ssh-ed25519"), ("Só via PR", "ruleset"),
                  ("CI ShellCheck", "github actions"), ("Só verificados", "ruleset")],
        "gates_ok": "✓ commit",
        "gates_bad": "✕ push direto",
        "gates_blocked": "recusado: mudanças só entram por pull request",
        "gates_target": "protegida",
        "road_sub": "{done} de {total} entregas concluídas · próxima: {next}",
        "road_items": [
            ("Setup idempotente", True), ("Commits assinados", True), ("PATH seletivo", True),
            ("CI + main protegida", True), ("Docs animadas", True), ("CI em distro zerada", True),
            ("Contêineres", True), ("Gitleaks", False), ("Actions fixadas", False),
        ],
    },
}


def svg_open(width, height, title, desc):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">\n'
        f"<title id=\"title\">{escape(title)}</title>\n<desc id=\"desc\">{escape(desc)}</desc>\n"
    )


# --------------------------------------------------------------------------- banner
def banner(lang, theme):
    t, c = TEXTS[lang], THEMES[theme]
    w, h = 1200, 340
    title_x, title_y = 330, 150

    chips, x = [], title_x
    for i, label in enumerate(t["chips"]):
        cw = len(label) * 9.4 + 36
        chips.append(
            f'<g class="fade" style="animation-delay:{0.9 + i * 0.18:.2f}s">'
            f'<rect x="{x:.0f}" y="226" width="{cw:.0f}" height="34" rx="17" fill="{c["panel"]}" stroke="{c["border"]}"/>'
            f'<text x="{x + cw / 2:.0f}" y="248" text-anchor="middle" class="chip">{escape(label)}</text></g>'
        )
        x += cw + 12

    css = f"""
text {{ font-family: {SANS}; }}
.title {{ font-size: 64px; font-weight: 800; fill: {c["text"]}; letter-spacing: -1px; }}
.tagline {{ font-size: 22px; fill: {c["muted"]}; }}
.chip {{ font-family: {MONO}; font-size: 15px; fill: {c["text"]}; }}
.prompt {{ font-family: {MONO}; font-size: 16px; fill: {c["muted"]}; }}
.prompt .dollar {{ fill: {c["green"]}; }}
.ring {{ fill: none; stroke: {c["accent"]}; stroke-width: 2; opacity: 0;
  transform-box: fill-box; transform-origin: center; animation: pulse 3.2s ease-out infinite; }}
.check {{ fill: none; stroke: #ffffff; stroke-width: 11; stroke-linecap: round; stroke-linejoin: round;
  stroke-dasharray: 90; stroke-dashoffset: 0; animation: draw 0.9s 0.4s ease-out both; }}
.shine {{ transform: translateX(-700px); animation: shine 6s 1.2s ease-in-out infinite; }}
.scan {{ transform: translateY(-140px); animation: scan 7s linear infinite; }}
.fade {{ animation: fadeUp 0.6s ease-out both; }}
.cursor {{ animation: blink 1.1s steps(1) infinite; }}
@keyframes pulse {{ 0% {{ transform: scale(0.9); opacity: 0.6; }} 100% {{ transform: scale(1.65); opacity: 0; }} }}
@keyframes draw {{ 0% {{ stroke-dashoffset: 90; opacity: 0; }} 10% {{ opacity: 1; }} 100% {{ stroke-dashoffset: 0; opacity: 1; }} }}
@keyframes shine {{ 0% {{ transform: translateX(-700px); }} 45%, 100% {{ transform: translateX(800px); }} }}
@keyframes scan {{ from {{ transform: translateY(-140px); }} to {{ transform: translateY({h + 20}px); }} }}
@keyframes fadeUp {{ from {{ opacity: 0; transform: translateY(10px); }} to {{ opacity: 1; transform: translateY(0); }} }}
@keyframes blink {{ 50% {{ opacity: 0; }} }}
{REDUCED_MOTION}
"""
    shield = "M170 88 L234 113 V168 C234 210 206 240 170 254 C134 240 106 210 106 168 V113 Z"
    title_attrs = f'x="{title_x}" y="{title_y}" class="title"'

    return (
        svg_open(w, h, "secure-wsl-devkit", t["banner_desc"])
        + f"""<defs>
  <pattern id="grid" width="32" height="32" patternUnits="userSpaceOnUse">
    <path d="M32 0H0V32" fill="none" stroke="{c["grid"]}" stroke-width="1"/>
  </pattern>
  <radialGradient id="glow"><stop offset="0" stop-color="{c["accent"]}" stop-opacity="0.28"/><stop offset="1" stop-color="{c["accent"]}" stop-opacity="0"/></radialGradient>
  <linearGradient id="shield" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{c["accent"]}"/><stop offset="1" stop-color="{c["accent2"]}"/></linearGradient>
  <linearGradient id="shineGrad" x1="0" x2="1"><stop offset="0" stop-color="{c["shine"]}" stop-opacity="0"/><stop offset="0.5" stop-color="{c["shine"]}" stop-opacity="0.65"/><stop offset="1" stop-color="{c["shine"]}" stop-opacity="0"/></linearGradient>
  <linearGradient id="scanGrad" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{c["accent"]}" stop-opacity="0"/><stop offset="0.7" stop-color="{c["accent"]}" stop-opacity="0.10"/><stop offset="1" stop-color="{c["accent"]}" stop-opacity="0"/></linearGradient>
  <clipPath id="frame"><rect width="{w}" height="{h}" rx="16"/></clipPath>
  <clipPath id="titleClip"><text {title_attrs}>secure-wsl-devkit</text></clipPath>
</defs>
<style>{css}</style>
<g clip-path="url(#frame)">
  <rect width="{w}" height="{h}" fill="{c["bg"]}"/>
  <rect width="{w}" height="{h}" fill="url(#grid)"/>
  <circle cx="170" cy="170" r="190" fill="url(#glow)"/>
  <rect class="scan" width="{w}" height="120" fill="url(#scanGrad)"/>
</g>
<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="16" fill="none" stroke="{c["border"]}"/>
<circle class="ring" cx="170" cy="170" r="84"/>
<circle class="ring" cx="170" cy="170" r="84" style="animation-delay:1.6s"/>
<path d="{shield}" fill="url(#shield)"/>
<path d="{shield}" fill="none" stroke="#ffffff" stroke-opacity="0.25" stroke-width="2"/>
<path class="check" d="M141 170 L162 191 L201 150"/>
<text {title_attrs}>secure-wsl-devkit</text>
<g clip-path="url(#titleClip)"><rect class="shine" x="{title_x}" y="80" width="180" height="90" fill="url(#shineGrad)"/></g>
<text x="{title_x}" y="194" class="tagline fade" style="animation-delay:0.5s">{escape(t["tagline"])}</text>
{"".join(chips)}
<text x="{title_x}" y="303" class="prompt fade" style="animation-delay:1.5s"><tspan class="dollar">$</tspan> ./setup.sh</text>
<g class="fade" style="animation-delay:1.5s"><rect class="cursor" x="{title_x + 12 * 9.9 + 4:.0f}" y="290" width="9" height="17" fill="{c["accent"]}"/></g>
</svg>
"""
    )


# --------------------------------------------------------------------------- terminal
def terminal():
    w, font, lh = 900, 15, 24
    x0, y0 = 28, 76
    cw_cover = 0.64 * font  # generous char width so the cover never hides the last char
    t_char, t_gap = 0.055, 0.36

    rows = [
        ("cmd", "./setup.sh"),
        ("out", "==> Verificando o ambiente", "h"),
        ("out", "Usuário: dev | Distro: Ubuntu-26.04", "o"),
        ("out", "==> Atualizando o sistema e instalando pacotes base", "h"),
        ("out", "0 upgraded, 0 newly installed, 0 to remove", "m"),
        ("out", "==> Configurando o Git", "h"),
        ("out", "Assinatura de commits ativada.", "ok"),
        ("out", "==> Desligando a importação do PATH do Windows", "h"),
        ("out", "Já configurado. Nada a fazer.", "skip"),
        ("out", "==> Liberando apenas o VS Code e o C:\\Windows no PATH", "h"),
        ("out", "Já configurado. Nada a fazer.", "skip"),
        ("out", "==> Instalando o nvm e o Node.js LTS", "h"),
        ("out", "Node v26.13.1 | npm 11.20.0", "o"),
        ("out", "✓ Setup automático concluído.", "ok"),
        ("cmd", "grep -c appendWindowsPath /etc/wsl.conf"),
        ("out", "1", "ok"),
        ("prompt",),
    ]

    # Build the timeline: when each row appears and, for commands, when typing ends.
    timeline, now = [], 0.4
    for row in rows:
        if row[0] == "cmd":
            end = now + len(row[1]) * t_char
            timeline.append((now, end))
            now = end + 0.45
        else:
            timeline.append((now, now))
            now += t_gap
    total = now + 4.5
    pct = lambda s: s / total * 100  # noqa: E731

    height = y0 + len(rows) * lh + 16
    css = [
        f"text {{ font-family: {MONO}; font-size: {font}px; fill: #e6edf3; white-space: pre; }}",
        ".h { fill: #22d3ee; font-weight: 700; } .m { fill: #8b949e; } .ok { fill: #3fb950; }",
        ".skip { fill: #a78bfa; } .dollar { fill: #3fb950; } .bar { font-size: 13px; fill: #8b949e; }",
        ".cursor { animation: blink 1.1s steps(1) infinite; } @keyframes blink { 50% { opacity: 0; } }",
    ]
    body = []
    for i, (row, (start, end)) in enumerate(zip(rows, timeline)):
        y = y0 + i * lh
        p = pct(start)
        css.append(
            f"#r{i} {{ animation: r{i} {total:.2f}s linear infinite; }} "
            f"@keyframes r{i} {{ 0%, {p:.2f}% {{ opacity: 0; }} {p + 0.05:.2f}%, 94% {{ opacity: 1; }} 98%, 100% {{ opacity: 0; }} }}"
        )
        if row[0] == "cmd":
            n = len(row[1])
            shift = (n + 1) * cw_cover
            cx = x0 + 2 * 0.6 * font
            css.append(
                f"#c{i} {{ transform: translateX({shift:.1f}px); animation: c{i} {total:.2f}s linear infinite; }} "
                f"@keyframes c{i} {{ 0% {{ transform: translateX(0); }} {p:.2f}% {{ transform: translateX(0); "
                f"animation-timing-function: steps({n}, end); }} {pct(end):.2f}%, 100% {{ transform: translateX({shift:.1f}px); }} }}"
            )
            body.append(
                f'<g id="r{i}"><text x="{x0}" y="{y}"><tspan class="dollar">$</tspan> {escape(row[1])}</text>'
                f'<rect id="c{i}" x="{cx:.1f}" y="{y - 17}" width="{w - cx:.0f}" height="{lh}" fill="#0d1117"/></g>'
            )
        elif row[0] == "out":
            body.append(f'<text id="r{i}" x="{x0}" y="{y}" class="{row[2]}">{escape(row[1])}</text>')
        else:
            body.append(
                f'<g id="r{i}"><text x="{x0}" y="{y}"><tspan class="dollar">$</tspan></text>'
                f'<rect class="cursor" x="{x0 + 18}" y="{y - 14}" width="9" height="18" fill="#22d3ee"/></g>'
            )
    css.append(REDUCED_MOTION)

    desc = ("Animated terminal: a second run of setup.sh detects that every step is already configured "
            "and changes nothing, then grep confirms the wsl.conf setting appears exactly once.")
    return (
        svg_open(w, height, "setup.sh running twice without duplicating anything", desc)
        + f"<style>{' '.join(css)}</style>\n"
        + f'<rect x="0.5" y="0.5" width="{w - 1}" height="{height - 1}" rx="12" fill="#0d1117" stroke="#30363d"/>\n'
        + f'<path d="M0.5 40 H{w - 0.5}" stroke="#30363d"/>\n'
        + '<circle cx="24" cy="20" r="6" fill="#ff5f57"/><circle cx="44" cy="20" r="6" fill="#febc2e"/>'
          '<circle cx="64" cy="20" r="6" fill="#28c840"/>\n'
        + f'<text x="{w / 2}" y="25" text-anchor="middle" class="bar">bash — ~/projetos/secure-wsl-devkit</text>\n'
        + "\n".join(body)
        + "\n</svg>\n"
    )


# --------------------------------------------------------------------------- impact
def impact(lang, theme):
    t, c = TEXTS[lang], THEMES[theme]
    w, h = 1200, 300
    card_w, gap, top, card_h = 362, 24, 108, 168
    bar_w = card_w - 48

    css = f"""
text {{ font-family: {SANS}; }}
.title {{ font-size: 26px; font-weight: 800; fill: {c["text"]}; }}
.sub {{ font-size: 15px; fill: {c["muted"]}; }}
.before {{ font-size: 26px; fill: {c["muted"]}; text-decoration: line-through; }}
.arrow {{ font-size: 22px; fill: {c["muted"]}; }}
.after {{ font-size: 46px; font-weight: 800; }}
.label {{ font-size: 16px; font-weight: 600; fill: {c["text"]}; }}
.detail {{ font-family: {MONO}; font-size: 13px; fill: {c["muted"]}; }}
.fill {{ transform-box: fill-box; transform-origin: left center; }}
.fade {{ animation: fadeUp 0.6s ease-out both; }}
@keyframes fadeUp {{ from {{ opacity: 0; transform: translateY(10px); }} to {{ opacity: 1; transform: translateY(0); }} }}
{REDUCED_MOTION}
"""
    cards, anims = [], []
    for i, (before, after, label, detail, start, end, color) in enumerate(t["cards"]):
        x = 32 + i * (card_w + gap)
        delay = 0.4 + i * 0.25
        anims.append(
            f"#f{i} {{ transform: scaleX({end:.4f}); animation: f{i} 1.6s {delay + 0.3:.2f}s cubic-bezier(.2,.8,.2,1) both; }} "
            f"@keyframes f{i} {{ from {{ transform: scaleX({start:.4f}); }} to {{ transform: scaleX({end:.4f}); }} }}"
        )
        cards.append(
            f'<g class="fade" style="animation-delay:{delay:.2f}s">'
            f'<rect x="{x}" y="{top}" width="{card_w}" height="{card_h}" rx="14" fill="{c["panel"]}" stroke="{c["border"]}"/>'
            f'<text x="{x + 24}" y="{top + 62}"><tspan class="before">{escape(before)}</tspan>'
            f'<tspan class="arrow" dx="12">→</tspan><tspan class="after" dx="12" fill="{c[color]}">{escape(after)}</tspan></text>'
            f'<text x="{x + 24}" y="{top + 98}" class="label">{escape(label)}</text>'
            f'<text x="{x + 24}" y="{top + 122}" class="detail">{escape(detail)}</text>'
            f'<rect x="{x + 24}" y="{top + 140}" width="{bar_w}" height="8" rx="4" fill="{c["border"]}"/>'
            f'<rect id="f{i}" class="fill" x="{x + 24}" y="{top + 140}" width="{bar_w}" height="8" rx="4" fill="{c[color]}"/>'
            f"</g>"
        )

    return (
        svg_open(w, h, t["impact_title"], t["impact_desc"])
        + f"<style>{css}{' '.join(anims)}</style>\n"
        + f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="16" fill="{c["bg"]}" stroke="{c["border"]}"/>\n'
        + f'<text x="32" y="54" class="title">{escape(t["impact_title"])}</text>\n'
        + f'<text x="32" y="82" class="sub">{escape(t["impact_sub"])}</text>\n'
        + "\n".join(cards)
        + "\n</svg>\n"
    )


# --------------------------------------------------------------------------- shared pieces
def header_css(c):
    return (
        f"text {{ font-family: {SANS}; }} "
        f".title {{ font-size: 26px; font-weight: 800; fill: {c['text']}; }} "
        f".sub {{ font-size: 15px; fill: {c['muted']}; }} "
        f".mono {{ font-family: {MONO}; }} "
    )


def frame(w, h, c, title, sub):
    return (
        f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="16" fill="{c["bg"]}" stroke="{c["border"]}"/>\n'
        f'<text x="32" y="54" class="title">{escape(title)}</text>\n'
        f'<text x="32" y="82" class="sub">{escape(sub)}</text>\n'
    )


def fade_keyframes(name, appear, hide_from=94):
    """Hidden until `appear`%, visible until `hide_from`%, then fades out to restart the loop."""
    return (f"@keyframes {name} {{ 0%, {appear:.2f}% {{ opacity: 0; }} "
            f"{appear + 2:.2f}%, {hide_from}% {{ opacity: 1; }} 100% {{ opacity: 0; }} }}")


# --------------------------------------------------------------------------- flow
def flow(lang, theme):
    t, c = TEXTS[lang], THEMES[theme]
    w, h = 1200, 300
    steps = t["flow_steps"]
    n, left, gap, top, card_h = len(steps), 32, 20, 104, 132
    card_w = (w - 2 * left - gap * (n - 1)) / n
    loop, travel = 7.5, 75  # loop length in seconds; % of the loop spent travelling
    track_y = top + card_h + 32
    x_start = left + card_w / 2
    dist = (n - 1) * (card_w + gap)

    css = [
        header_css(c),
        f".step {{ font-size: 14px; font-weight: 700; fill: {c['text']}; }}",
        f".detail {{ font-family: {MONO}; font-size: 12px; fill: {c['muted']}; }}",
        f".num {{ font-size: 13px; font-weight: 700; fill: {c['text']}; }}",
        f".pill {{ font-family: {MONO}; font-size: 11px; }}",
        f".track {{ transform-box: fill-box; transform-origin: left center; transform: scaleX(1); "
        f"animation: track {loop}s linear infinite; }}",
        f"@keyframes track {{ 0% {{ transform: scaleX(0); opacity: 1; }} {travel}% {{ transform: scaleX(1); }} "
        f"94% {{ opacity: 1; }} 100% {{ transform: scaleX(1); opacity: 0; }} }}",
        f".dot {{ transform: translateX({dist:.1f}px); animation: dot {loop}s linear infinite; }}",
        f"@keyframes dot {{ 0% {{ transform: translateX(0); opacity: 1; }} {travel}% {{ transform: translateX({dist:.1f}px); }} "
        f"94% {{ opacity: 1; }} 100% {{ transform: translateX({dist:.1f}px); opacity: 0; }} }}",
    ]
    cards = []
    for i, (title, detail, kind) in enumerate(steps):
        x = left + i * (card_w + gap)
        appear = i / (n - 1) * travel
        css.append(f".k{i} {{ animation: k{i} {loop}s linear infinite; }} " + fade_keyframes(f"k{i}", appear))
        color = {"always": c["muted"], "skip": c["accent2"], "check": c["accent"]}[kind]
        label = t[f"flow_{kind}"]
        bx, by = x + 28, top + 30
        cards.append(
            f'<rect x="{x:.1f}" y="{top}" width="{card_w:.1f}" height="{card_h}" rx="12" fill="{c["panel"]}" stroke="{c["border"]}"/>'
            f'<rect class="k{i}" x="{x:.1f}" y="{top}" width="{card_w:.1f}" height="{card_h}" rx="12" fill="none" '
            f'stroke="{c["accent"]}" stroke-width="2"/>'
            f'<circle cx="{bx:.1f}" cy="{by}" r="13" fill="{c["border"]}"/>'
            f'<text x="{bx:.1f}" y="{by + 5}" text-anchor="middle" class="num">{i + 1}</text>'
            f'<g class="k{i}"><circle cx="{bx:.1f}" cy="{by}" r="13" fill="{c["green"]}"/>'
            f'<text x="{bx:.1f}" y="{by + 5}" text-anchor="middle" class="num" fill="#ffffff" style="fill:#ffffff">✓</text></g>'
            f'<text x="{x + 16:.1f}" y="{top + 70}" class="step">{escape(title)}</text>'
            f'<text x="{x + 16:.1f}" y="{top + 90}" class="detail">{escape(detail)}</text>'
            f'<rect x="{x + 16:.1f}" y="{top + 102}" width="{card_w - 32:.1f}" height="20" rx="10" fill="none" stroke="{color}"/>'
            f'<text x="{x + card_w / 2:.1f}" y="{top + 116}" text-anchor="middle" class="pill" fill="{color}">{escape(label)}</text>'
        )

    track = (
        f'<rect x="{x_start:.1f}" y="{track_y - 2}" width="{dist:.1f}" height="4" rx="2" fill="{c["border"]}"/>'
        f'<rect class="track" x="{x_start:.1f}" y="{track_y - 2}" width="{dist:.1f}" height="4" rx="2" fill="{c["accent"]}"/>'
        f'<g class="dot"><circle cx="{x_start:.1f}" cy="{track_y}" r="12" fill="{c["accent"]}" fill-opacity="0.25"/>'
        f'<circle cx="{x_start:.1f}" cy="{track_y}" r="6" fill="{c["accent"]}"/></g>'
    )
    return (
        svg_open(w, h, t["flow_title"], t["flow_desc"])
        + f"<style>{' '.join(css)} {REDUCED_MOTION}</style>\n"
        + frame(w, h, c, t["flow_title"], t["flow_sub"])
        + "\n".join(cards) + "\n" + track + "\n</svg>\n"
    )


# --------------------------------------------------------------------------- security gates
def gates(lang, theme):
    t, c = TEXTS[lang], THEMES[theme]
    w, h = 1200, 330
    loop = 9.0
    gate_x = [360, 560, 760, 960]
    g_top, lane_ok, lane_bad = 142, 190, 258
    g_h = lane_bad + 24 - g_top
    start, target_x, target_w = 40, 1030, 140
    ok_w, bad_w = 120, 160
    ok_dist = target_x + (target_w - ok_w) / 2 - start
    bad_dist = gate_x[1] - 12 - bad_w - start
    ok_end = 50  # % of the loop the valid commit takes to reach main

    css = [
        header_css(c),
        f".gtitle {{ font-size: 14px; font-weight: 700; fill: {c['text']}; }}",
        f".gdetail {{ font-family: {MONO}; font-size: 12px; fill: {c['muted']}; }}",
        f".packet {{ font-family: {MONO}; font-size: 13px; font-weight: 700; }}",
        f".ok {{ transform: translateX({ok_dist:.1f}px); animation: ok {loop}s cubic-bezier(.45,0,.55,1) infinite; }}",
        f"@keyframes ok {{ 0% {{ transform: translateX(0); opacity: 1; }} {ok_end}% {{ transform: translateX({ok_dist:.1f}px); }} "
        f"94% {{ opacity: 1; }} 100% {{ transform: translateX({ok_dist:.1f}px); opacity: 0; }} }}",
        f".bad {{ transform: translateX({bad_dist:.1f}px); animation: bad {loop}s ease-in-out infinite; }}",
        f"@keyframes bad {{ 0%, 52% {{ transform: translateX(0); opacity: 0; }} 54% {{ opacity: 1; }} "
        f"74% {{ transform: translateX({bad_dist:.1f}px); }} 75.5% {{ transform: translateX({bad_dist - 10:.1f}px); }} "
        f"77% {{ transform: translateX({bad_dist:.1f}px); }} 78.5% {{ transform: translateX({bad_dist - 6:.1f}px); }} "
        f"80%, 94% {{ transform: translateX({bad_dist:.1f}px); opacity: 1; }} 100% {{ transform: translateX({bad_dist:.1f}px); opacity: 0; }} }}",
        f".flash {{ opacity: 0; animation: flash {loop}s linear infinite; }}",
        "@keyframes flash { 0%, 73% { opacity: 0; } 75% { opacity: 1; } 78% { opacity: 0.3; } 81% { opacity: 1; } 86%, 100% { opacity: 0; } }",
        f".blocked {{ animation: blocked {loop}s linear infinite; }} " + fade_keyframes("blocked", 80),
        f".target {{ animation: target {loop}s linear infinite; }} " + fade_keyframes("target", ok_end - 2),
    ]

    parts = []
    for y in (lane_ok, lane_bad):
        parts.append(f'<path d="M{start} {y} H{target_x}" stroke="{c["border"]}" stroke-dasharray="4 7"/>')
    for i, (cx, (title, detail)) in enumerate(zip(gate_x, t["gates"])):
        appear = (cx - start - ok_w / 2) / ok_dist * ok_end
        css.append(f".g{i} {{ animation: g{i} {loop}s linear infinite; }} " + fade_keyframes(f"g{i}", appear))
        parts.append(
            f'<text x="{cx}" y="{g_top - 26}" text-anchor="middle" class="gtitle">{escape(title)}</text>'
            f'<text x="{cx}" y="{g_top - 8}" text-anchor="middle" class="gdetail">{escape(detail)}</text>'
            f'<rect x="{cx - 6}" y="{g_top}" width="12" height="{g_h}" rx="6" fill="{c["border"]}"/>'
            f'<rect class="g{i}" x="{cx - 6}" y="{g_top}" width="12" height="{g_h}" rx="6" fill="{c["green"]}"/>'
        )
        if i == 1:
            parts.append(f'<rect class="flash" x="{cx - 6}" y="{g_top}" width="12" height="{g_h}" rx="6" fill="{c["red"]}"/>')

    tcx = target_x + target_w / 2
    parts.append(
        f'<rect x="{target_x}" y="{g_top}" width="{target_w}" height="{g_h}" rx="14" fill="{c["panel"]}" stroke="{c["border"]}"/>'
        f'<rect class="target" x="{target_x}" y="{g_top}" width="{target_w}" height="{g_h}" rx="14" fill="none" '
        f'stroke="{c["green"]}" stroke-width="2"/>'
        f'<text x="{tcx}" y="{g_top + 28}" text-anchor="middle" class="mono" font-size="18" font-weight="700" fill="{c["text"]}">main</text>'
        f'<text x="{tcx}" y="{g_top + g_h - 18}" text-anchor="middle" class="gdetail">{escape(t["gates_target"])}</text>'
    )

    def packet(cls, y, width, color, label):
        return (
            f'<g class="{cls}"><rect x="{start}" y="{y - 15}" width="{width}" height="30" rx="15" fill="{color}" '
            f'fill-opacity="0.14" stroke="{color}"/>'
            f'<text x="{start + width / 2}" y="{y + 5}" text-anchor="middle" class="packet" fill="{color}">{escape(label)}</text></g>'
        )

    parts.append(packet("ok", lane_ok, ok_w, c["green"], t["gates_ok"]))
    parts.append(packet("bad", lane_bad, bad_w, c["red"], t["gates_bad"]))
    parts.append(
        f'<text class="blocked mono" x="{start + bad_dist + bad_w / 2:.1f}" y="{lane_bad + 50}" text-anchor="middle" '
        f'font-size="12" fill="{c["red"]}">{escape(t["gates_blocked"])}</text>'
    )
    return (
        svg_open(w, h, t["gates_title"], t["gates_desc"])
        + f"<style>{' '.join(css)} {REDUCED_MOTION}</style>\n"
        + frame(w, h, c, t["gates_title"], t["gates_sub"])
        + "\n".join(parts) + "\n</svg>\n"
    )


# --------------------------------------------------------------------------- roadmap
def roadmap(lang, theme):
    t, c = TEXTS[lang], THEMES[theme]
    w, h = 1200, 300
    items = t["road_items"]
    n = len(items)
    done = sum(1 for _, finished in items if finished)
    upcoming = items[done][0] if done < n else "—"
    x0, x1, y = 90, 1110, 188
    step = (x1 - x0) / (n - 1)
    fill_w = (done - 1) * step
    sub = t["road_sub"].format(done=done, total=n, next=upcoming)

    css = [
        header_css(c),
        f".label {{ font-size: 14px; fill: {c['muted']}; }}",
        f".label.done {{ fill: {c['text']}; }} .label.next {{ fill: {c['accent']}; font-weight: 700; }}",
        ".check { font-size: 15px; font-weight: 800; fill: #ffffff; }",
        ".rfill { transform-box: fill-box; transform-origin: left center; animation: grow 1.4s 0.3s linear both; }",
        "@keyframes grow { from { transform: scaleX(0); } to { transform: scaleX(1); } }",
        ".pop { transform-box: fill-box; transform-origin: center; animation: pop 0.45s cubic-bezier(.3,1.6,.5,1) both; }",
        "@keyframes pop { from { opacity: 0; transform: scale(0.4); } to { opacity: 1; transform: scale(1); } }",
        ".fade { animation: fade 0.5s ease-out both; } @keyframes fade { from { opacity: 0; } to { opacity: 1; } }",
        f".ring {{ fill: none; stroke: {c['accent']}; stroke-width: 2; opacity: 0; transform-box: fill-box; "
        f"transform-origin: center; animation: ring 2s 2.2s ease-out infinite; }}",
        "@keyframes ring { 0% { transform: scale(0.9); opacity: 0.7; } 100% { transform: scale(2); opacity: 0; } }",
    ]
    parts = [
        f'<rect x="{x0}" y="{y - 3}" width="{x1 - x0}" height="6" rx="3" fill="{c["border"]}"/>',
        f'<rect class="rfill" x="{x0}" y="{y - 3}" width="{fill_w:.1f}" height="6" rx="3" fill="{c["green"]}"/>',
    ]
    for i, (label, finished) in enumerate(items):
        cx = x0 + i * step
        if finished:
            delay = 0.3 + (i / max(done - 1, 1)) * 1.4
            node = (f'<circle cx="{cx:.1f}" cy="{y}" r="15" fill="{c["green"]}"/>'
                    f'<text x="{cx:.1f}" y="{y + 5}" text-anchor="middle" class="check">✓</text>')
            kind = "done"
        elif i == done:
            delay = 1.9
            node = (f'<circle class="ring" cx="{cx:.1f}" cy="{y}" r="15"/>'
                    f'<circle cx="{cx:.1f}" cy="{y}" r="15" fill="{c["bg"]}" stroke="{c["accent"]}" stroke-width="2"/>'
                    f'<circle cx="{cx:.1f}" cy="{y}" r="5" fill="{c["accent"]}"/>')
            kind = "next"
        else:
            delay = 1.9 + (i - done) * 0.12
            node = f'<circle cx="{cx:.1f}" cy="{y}" r="15" fill="{c["bg"]}" stroke="{c["border"]}" stroke-width="2" stroke-dasharray="4 4"/>'
            kind = "todo"
        ly = y - 32 if i % 2 == 0 else y + 44
        parts.append(f'<g class="pop" style="animation-delay:{delay:.2f}s">{node}</g>')
        parts.append(f'<text x="{cx:.1f}" y="{ly}" text-anchor="middle" class="label {kind} fade" '
                     f'style="animation-delay:{delay:.2f}s">{escape(label)}</text>')

    desc = f"{sub}. " + "; ".join(f"{label}: {'done' if f else 'planned'}" for label, f in items)
    return (
        svg_open(w, h, "Roadmap", desc)
        + f"<style>{' '.join(css)} {REDUCED_MOTION}</style>\n"
        + frame(w, h, c, "Roadmap", sub)
        + "\n".join(parts) + "\n</svg>\n"
    )


def main():
    files = {"terminal-demo.svg": terminal()}
    for lang in TEXTS:
        for theme in THEMES:
            files[f"banner-{lang}-{theme}.svg"] = banner(lang, theme)
            files[f"impact-{lang}-{theme}.svg"] = impact(lang, theme)
            files[f"flow-{lang}-{theme}.svg"] = flow(lang, theme)
            files[f"gates-{lang}-{theme}.svg"] = gates(lang, theme)
            files[f"roadmap-{lang}-{theme}.svg"] = roadmap(lang, theme)
    for name, content in files.items():
        (OUT / name).write_text(content, encoding="utf-8")
        print(f"generated assets/{name}")


if __name__ == "__main__":
    main()
