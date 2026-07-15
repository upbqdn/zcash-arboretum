#!/usr/bin/env python3
"""Site tooling for the Zcash Arboretum.

Modes:
  render   Pre-render every tikzpicture in each volume to SVG (needs
           tectonic + pdftocairo; run locally, commit the SVGs).
  webprep  Write build/web/<vol>.tex with tikzpictures replaced by
           \\includegraphics of the pre-rendered SVGs and tikz packages
           stripped (run in CI before latexml).
  landing  Write the landing page index.html from the volumes' \\title
           lines into the directory given by --out.
"""

import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIGDIR = ROOT / "site" / "figures"
WEBDIR = ROOT / "build" / "web"

# Reading order, grouping, and status chip for the landing page.
VOLUME_META = [
    ("math-guide", "Foundations", "stable"),
    ("crypto-guide", "Foundations", "stable"),
    ("halo2-guide", "Foundations", "stable"),
    ("halo2-intuition-guide", "Foundations", "companion"),
    ("orchard-guide", "Deployed protocol", "deployed"),
    ("wallet-guide", "Deployed protocol", "deployed"),
    ("sync-guide", "Deployed protocol", "deployed"),
    ("voting-guide", "Frontier", "frontier"),
    ("zsa-guide", "Frontier", "frontier"),
    ("tachyon-guide", "Frontier", "design-stage"),
    ("crosslink-guide", "Frontier", "design-stage"),
]
VOLUMES = [v for v, _, _ in VOLUME_META]

TIKZ_RE = re.compile(r"\\begin\{tikzpicture\}.*?\\end\{tikzpicture\}", re.S)
DROP_IN_STANDALONE = ("\\documentclass", "\\usepackage[margin",
                      "\\renewenvironment{abstract}", "\\title{",
                      "\\author{", "\\date{",
                      "\\small\\begin{center}", "}{\\par\\medskip}")
DROP_IN_WEB = ("\\usepackage{tikz}", "\\usetikzlibrary")


def volumes_present():
    return [v for v in VOLUMES if (ROOT / f"{v}.tex").exists()]


def preamble_of(text):
    return text.split("\\begin{document}")[0]


def render():
    FIGDIR.mkdir(parents=True, exist_ok=True)
    DEF_STARTS = ("\\newlength", "\\settowidth", "\\setlength",
                  "\\newcommand", "\\pgfmath")
    for vol in volumes_present():
        text = (ROOT / f"{vol}.tex").read_text()
        pics = list(TIKZ_RE.finditer(text))
        if not pics:
            continue
        pre_lines = [
            ln for ln in preamble_of(text).splitlines()
            if not any(ln.lstrip().startswith(d) for d in DROP_IN_STANDALONE)
        ]
        for i, m in enumerate(pics, 1):
            # carry along length/macro definitions the enclosing figure
            # environment sets up for this picture
            before = text[:m.start()]
            figpos = before.rfind("\\begin{figure}")
            defs = []
            if figpos != -1 and "\\end{figure}" not in before[figpos:]:
                defs = [ln for ln in before[figpos:].splitlines()
                        if ln.lstrip().startswith(DEF_STARTS)]
            doc = "\n".join(
                ["\\documentclass[tikz,border=2pt]{standalone}"]
                + pre_lines + ["\\begin{document}"] + defs
                + [m.group(0), "\\end{document}"])
            with tempfile.TemporaryDirectory() as td:
                tex = Path(td) / "fig.tex"
                tex.write_text(doc)
                subprocess.run(["tectonic", "-Z", "shell-escape", str(tex)],
                               cwd=td, check=True, capture_output=True)
                out = FIGDIR / f"{vol}-fig{i}.svg"
                subprocess.run(["pdftocairo", "-svg", str(Path(td) / "fig.pdf"),
                                str(out)], check=True)
                # PNG twin: LaTeXML's graphics handler rejects .svg includes
                subprocess.run(["pdftoppm", "-png", "-r", "180", "-singlefile",
                                str(Path(td) / "fig.pdf"),
                                str(FIGDIR / f"{vol}-fig{i}")], check=True)
                print(f"rendered {out.relative_to(ROOT)} (+ .png)")


def webprep():
    WEBDIR.mkdir(parents=True, exist_ok=True)
    for vol in volumes_present():
        text = (ROOT / f"{vol}.tex").read_text()
        n = [0]

        def sub(_m, vol=vol, n=n):
            n[0] += 1
            return (r"\includegraphics[width=0.9\linewidth]"
                    f"{{figures/{vol}-fig{n[0]}.png}}")

        text = TIKZ_RE.sub(sub, text)
        text = text.replace("\\author{m@rek.onl}", "\\author{}")
        lines = []
        for ln in text.splitlines():
            s = ln.lstrip()
            if s.startswith("\\usepackage{tikz}"):
                # tikz transitively provides xcolor, which \definecolor and
                # hyperref's colour options need; keep that half
                lines.append("\\usepackage{xcolor}")
            elif s.startswith("\\usetikzlibrary"):
                continue
            else:
                lines.append(ln)
        text = "\n".join(lines)
        if "\\usepackage{graphicx}" not in text:
            text = text.replace("\\usepackage{booktabs,enumitem}",
                                "\\usepackage{booktabs,enumitem}\n"
                                "\\usepackage{graphicx}", 1)
        (WEBDIR / f"{vol}.tex").write_text(text)
        print(f"prepared {WEBDIR / (vol + '.tex')}")


ROMANS = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X",
          "XI", "XII"]


def vol_title(vol):
    text = (ROOT / f"{vol}.tex").read_text()
    m = re.search(r"\\title\{\\textbf\{\\Huge ([^}]*)\}\\\\\[6pt\]"
                  r"\\large ([^}]*)\}", text)
    return (m.group(1) if m else vol, m.group(2) if m else "")


def ver():
    return subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                          capture_output=True, text=True,
                          cwd=ROOT).stdout.strip() or "0"


def landing(outdir):
    groups, n = {}, 0
    for vol, group, chip in VOLUME_META:
        if not (ROOT / f"{vol}.tex").exists():
            continue
        title, sub = vol_title(vol)
        if chip == "companion":
            acc = f"vol. {ROMANS[n - 1]} · companion"
            plaque = ""
        else:
            n += 1
            acc = f"vol. {ROMANS[n - 1]}"
            plaque = f'<span class="plaque">{chip}</span>'
        groups.setdefault(group, []).append(f"""<li class="plate">
<div class="label"><span class="acc">{acc}</span>
{plaque}</div>
<a class="title" href="{vol}/">{title}</a>
<p class="sub">{sub}</p>
<div class="links"><a href="{vol}/">Read</a>
<a href="pdf/{vol}.pdf">PDF</a></div></li>""")
    cards = []
    for group, items in groups.items():
        cards.append(f'<h3 class="grp">{group}</h3><ol class="plates">'
                     + "\n".join(items) + "</ol>")
    html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>The Zcash Arboretum</title>
<link rel="stylesheet" href="arboretum.css?v={ver()}">
<link href="pagefind/pagefind-ui.css" rel="stylesheet">
<script src="pagefind/pagefind-ui.js"></script>
</head><body>
<main class="arb-landing">
<h1>The Zcash Arboretum</h1>
<hr class="stem">
<p class="tag">Documentation of the Zcash protocol &mdash; the deployed
core and the protocols growing on top of it. Non-normative: where these volumes and the
<a href="https://zips.z.cash/protocol/protocol.pdf">protocol specification</a>
disagree, the specification is correct.</p>
<div id="search"></div>
<script>
window.addEventListener('DOMContentLoaded', () => {{
  new PagefindUI({{ element: '#search', showSubResults: true }});
}});
</script>
{chr(10).join(cards)}
<p class="foot">Sources and compiled PDFs:
<a href="https://github.com/upbqdn/zcash-arboretum">github.com/upbqdn/zcash-arboretum</a></p>
</main></body></html>
"""
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(html)
    print(f"wrote {out / 'index.html'}")


def postprocess(outdir):
    """Inject the site bar + search into every built volume page, scope the
    search index to the document body, and drop LaTeXML's footer logo."""
    out = Path(outdir)
    for vol, _group, _chip in VOLUME_META:
        vdir = out / vol
        if not vdir.is_dir():
            continue
        title, _ = vol_title(vol)
        bar = f"""<header class="arb-bar"><a class="wordmark" href="../">The
Zcash Arboretum</a><span class="volname">{title}</span>
<details class="arb-search"><summary>search</summary>
<div class="arb-search-panel"><div id="arb-search-ui"></div></div></details>
</header>
<link href="../pagefind/pagefind-ui.css" rel="stylesheet">
<script src="../pagefind/pagefind-ui.js"></script>
<script>
document.querySelector('details.arb-search').addEventListener('toggle',
  function (e) {{
    if (e.target.open && !window.__arbSearch) {{
      window.__arbSearch = new PagefindUI({{ element: '#arb-search-ui',
        showSubResults: true }});
    }}
  }});
</script>"""
        n = 0
        for page in vdir.glob("*.html"):
            t = page.read_text()
            t2 = t.replace('href="../arboretum.css"',
                           f'href="../arboretum.css?v={ver()}"', 1)
            t2 = re.sub(r"<body", '<body data-arb=\"vol\"', t2, count=1)
            t2 = re.sub(r"(<body[^>]*>)", r"\1" + bar.replace("\\", "\\\\"),
                        t2, count=1)
            t2 = t2.replace('class="ltx_page_content"',
                            'class="ltx_page_content" data-pagefind-body',
                            1)
            if t2 != t:
                page.write_text(t2)
                n += 1
        print(f"postprocessed {vol}: {n} pages")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "render":
        render()
    elif mode == "webprep":
        webprep()
    elif mode == "landing":
        landing(sys.argv[sys.argv.index("--out") + 1])
    elif mode == "postprocess":
        postprocess(sys.argv[sys.argv.index("--out") + 1])
    else:
        sys.exit(__doc__)
