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
        "green": "#3fb950", "shine": "#ffffff",
    },
    "light": {
        "bg": "#ffffff", "panel": "#f6f8fa", "border": "#d0d7de", "grid": "#eef1f4",
        "text": "#1f2328", "muted": "#59636e", "accent": "#0e7490", "accent2": "#7c3aed",
        "green": "#1a7f37", "shine": "#22d3ee",
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


def main():
    files = {"terminal-demo.svg": terminal()}
    for lang in TEXTS:
        for theme in THEMES:
            files[f"banner-{lang}-{theme}.svg"] = banner(lang, theme)
            files[f"impact-{lang}-{theme}.svg"] = impact(lang, theme)
    for name, content in files.items():
        (OUT / name).write_text(content, encoding="utf-8")
        print(f"generated assets/{name}")


if __name__ == "__main__":
    main()
