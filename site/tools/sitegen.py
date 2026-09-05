#!/usr/bin/env python3
"""Site tooling for the Zcash Arboretum.

Modes:
  volumes  Print the volumes included in the Arboretum.
  render   Pre-render every tikzpicture in each volume to SVG (needs
           tectonic + pdftocairo; run locally, commit the SVGs).
  webprep  Write build/web/<vol>.tex with tikzpictures replaced by
           \\includegraphics of the pre-rendered SVGs and tikz packages
           stripped (run in CI before latexml).
  landing  Write the landing page index.html from the volumes' \\title
           lines into the directory given by --out.
"""

import re
import shutil
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
    ("consensus-guide", "Deployed protocol", "deployed"),
    ("ironwood-guide", "Deployed protocol", "deployed"),
    ("wallet-guide", "Deployed protocol", "deployed"),
    ("sync-guide", "Deployed protocol", "deployed"),
    ("flyclient-guide", "Deployed protocol", "deployed"),
    ("zsa-guide", "Frontier", "frontier"),
    ("crosslink-guide", "Frontier", "design-stage"),
    ("frost-guide", "Frontier", "frontier"),
]
VOLUMES = [v for v, _, _ in VOLUME_META]

OMNIBUS_INTRO = r"""\phantomsection
\section*{Introduction}
\addcontentsline{toc}{section}{Introduction}
\markboth{Introduction}{}
\emph{The Zcash Arboretum} is a non-normative guide to the mathematics,
cryptography, and engineering of the Zcash protocol.  It covers the
foundations of Halo~2 and Orchard, deployed consensus and wallet protocols,
and designs being explored beyond them.  The protocol specification and ZIPs
remain authoritative.

The order is layered.  The \emph{Math}, \emph{Crypto}, and \emph{Halo~2}
Guides construct the foundations.  The \emph{Consensus}, \emph{Ironwood},
\emph{Wallet}, \emph{Sync}, and \emph{FlyClient} Guides explain the deployed
system and its boundaries.  The remaining parts examine shielded assets,
trailing finality, and threshold authorization.

Three reading paths cover most uses.  For prerequisites, begin with the first
three parts and use the Halo~2 companion as the worked example.  For the life
of a shielded payment, read \emph{Ironwood}, then \emph{Wallet}, \emph{Sync},
and \emph{Consensus}.  For proposed changes, read the relevant frontier part
only after its lower-layer dependencies.  Each part restarts its own section
numbering so that citations agree with the separately published volume.
"""

THEME_INIT = """<script>
try {
  const theme = localStorage.getItem('arb-theme');
  if (['light', 'warm', 'dark', 'midnight'].includes(theme))
    document.documentElement.dataset.theme = theme;
} catch (_) {}
</script>"""
THEME_PICKER = """<select class="arb-theme" aria-label="Theme">
<option value="system">System</option>
<option value="light">Light</option>
<option value="warm">Warm light</option>
<option value="dark">Dark</option>
<option value="midnight">Warm dark</option>
</select>
<script>
(function () {
  const select = document.currentScript.previousElementSibling;
  let theme = 'system';
  try { theme = localStorage.getItem('arb-theme') || theme; } catch (_) {}
  if (!['system', 'light', 'warm', 'dark', 'midnight'].includes(theme)) theme = 'system';
  select.value = theme;
  select.addEventListener('change', function () {
    theme = select.value;
    if (theme === 'system') delete document.documentElement.dataset.theme;
    else document.documentElement.dataset.theme = theme;
    try { localStorage.setItem('arb-theme', theme); } catch (_) {}
  });
})();
</script>"""

MATHJAX = r"""<script>
window.MathJax = {
  loader: { paths: { fonts: '[mathjax]/../@mathjax' } },
  options: { enableMenu: false },
  tex: { macros: { qed: '\\tag*{□}' } },
  output: {
    font: 'mathjax-stix2',
    displayOverflow: 'linebreak',
    linebreaks: { inline: true, width: '100%', lineleading: .2 }
  },
  startup: {
    ready() {
      document.querySelectorAll('math[alttext]').forEach(function (math) {
        const tex = math.getAttribute('alttext').replace(/%\s+/g, '');
        math.replaceWith(document.createTextNode(
          math.getAttribute('display') === 'block'
            ? `\\[${tex}\\]` : `\\(${tex}\\)`));
      });
      MathJax.startup.defaultReady();
    }
  }
};
</script>
<script src="../mathjax/tex-chtml.js"></script>
<script>
MathJax.startup.promise.then(function () {
  function constrainMath() {
    document.querySelectorAll('.arb-math-scroll').forEach(function (math) {
      math.classList.remove('arb-math-scroll');
    });
    document.querySelectorAll('mjx-container:not([display="true"])').forEach(function (math) {
      let parent = math.parentElement;
      while (parent && ['inline', 'contents'].includes(getComputedStyle(parent).display))
        parent = parent.parentElement;
      if (!parent) return;
      const box = math.getBoundingClientRect();
      const outer = parent.getBoundingClientRect();
      if (box.left < outer.left - 1 || box.right > outer.right + 1)
        math.classList.add('arb-math-scroll');
    });
  }
  constrainMath();
  let width = innerWidth;
  let timer;
  addEventListener('resize', function () {
    if (innerWidth === width) return;
    clearTimeout(timer);
    timer = setTimeout(function () {
      width = innerWidth;
      MathJax.startup.document.rerender();
      requestAnimationFrame(constrainMath);
    }, 150);
  });
});
</script>"""

TIKZ_RE = re.compile(r"\\begin\{tikzpicture\}.*?\\end\{tikzpicture\}", re.S)
PROOF_MATH_END_RE = re.compile(
    r'(<math\b(?:(?!</math>)[\s\S])*?</math>)([.!?])(?=\s*∎</p>)')
THEOREM_TITLE_RE = re.compile(
    r'(<div\b(?=[^>]*\bid="([^"]+)")'
    r'(?=[^>]*\bclass="[^"]*\bltx_theorem\b[^"]*")[^>]*>\s*'
    r'<h6\b[^>]*>)(.*?)(</h6>)', re.S)
UNEXPANDED_CREF_RE = re.compile(r"\\[Cc]ref[A-Za-z]*")
DROP_IN_STANDALONE = ("\\documentclass", "\\usepackage[margin",
                      "\\renewenvironment{abstract}", "\\title{",
                      "\\author{", "\\date{",
                      "\\small\\begin{center}", "}{\\par\\medskip}")
DROP_IN_WEB = ("\\usepackage{tikz}", "\\usetikzlibrary")

# The PDF design preamble (fontspec + unicode-math + mdframed + fancyhdr)
# is byte-identical across volumes; LaTeXML can't ingest it, and the web
# build styles theorems and fonts in CSS instead. webprep swaps it back to
# the classic package line. Keep these constants in sync with the volumes.
FONT_BLOCK = """\\usepackage{amsmath,amsthm,mathtools}
\\usepackage{fontspec}
\\usepackage{unicode-math}
\\setmainfont{STIX2Text}[Path=fonts/, Extension=.otf,
  UprightFont=*-Regular, ItalicFont=*-Italic,
  BoldFont=*-Bold, BoldItalicFont=*-BoldItalic]
\\setmathfont{STIX2Math}[Path=fonts/, Extension=.otf]
"""
FONT_CLASSIC = "\\usepackage{amsmath,amssymb,amsthm,mathtools}\n"
DESIGN_BLOCK_RE = re.compile(
    r"% kind-coded theorem blocks.*?"
    r"\\renewcommand\{\\sectionmark\}\[1\]\{[^\n]*\}\n",
    re.S)


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
            # the standalone compiles in a temp dir, so the volume's
            # repo-relative font path must become absolute
            doc = doc.replace("Path=fonts/", f"Path={ROOT}/fonts/")
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
        if FONT_BLOCK in text:
            text = text.replace(FONT_BLOCK, FONT_CLASSIC, 1)
        text = DESIGN_BLOCK_RE.sub("", text, count=1)
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
    omnibus(WEBDIR, WEBDIR / "arboretum-complete.tex")


ROMANS = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X",
          "XI", "XII", "XIII", "XIV", "XV"]


def vol_title(vol):
    text = (ROOT / f"{vol}.tex").read_text()
    m = re.search(r"\\title\{\\textbf\{\\Huge ([^}]*)\}\\\\\[6pt\]"
                  r"\\large ([^}]*)\}", text)
    return (m.group(1) if m else vol, m.group(2) if m else "")


def ver():
    return subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                          capture_output=True, text=True,
                          cwd=ROOT).stdout.strip() or "0"


MACRO_RE = re.compile(r"\\(?:re)?newcommand\{(\\[A-Za-z]+)\}(\[\d\])?\{(.*)\}\s*$")


def omnibus(srcdir=ROOT, out=None):
    """Generate arboretum-complete.tex: every volume as a \\part of one
    document. Mechanical: shared preamble (packages etc. deduped, macros
    stripped), per-part counter resets + the volume's own macros as \\def
    (volumes disagree on eight macro bodies), per-volume label prefixing."""
    srcdir = Path(srcdir)
    out = Path(out) if out else ROOT / "arboretum-complete.tex"
    vols = [v for v in VOLUMES if (srcdir / f"{v}.tex").exists()]
    companions = {v for v, _group, chip in VOLUME_META
                  if chip == "companion"}
    seen, macro_free = set(), []
    for vol in vols:
        pre = preamble_of((srcdir / f"{vol}.tex").read_text())
        for ln in pre.splitlines():
            s = ln.strip()
            if (not s or s.startswith(("\\title", "\\author", "\\date"))
                    or MACRO_RE.match(s)):
                continue
            if ln not in seen:
                seen.add(ln)
                macro_free.append(ln)
    parts = ["\n".join(macro_free),
             "\\setcounter{tocdepth}{1}",
             "\\title{\\textbf{\\Huge The Zcash Arboretum}\\\\[6pt]"
             "\\large Foundations, deployed protocol, and frontier designs}",
             ("\\author{}\n\\date{}" if srcdir == WEBDIR
              else "\\author{m@rek.onl}\n\\date{}"),
             "\\newcounter{arbvolume}\n"
             "\\renewcommand*{\\theHsection}{\\arabic{arbvolume}.\\arabic{section}}\n"
             "\\renewcommand*{\\theHsubsection}{\\theHsection.\\arabic{subsection}}\n"
             "\\renewcommand*{\\theHsubsubsection}{\\theHsubsection.\\arabic{subsubsection}}\n"
             "\\renewcommand*{\\theHparagraph}{\\theHsubsubsection.\\arabic{paragraph}}\n"
             "\\renewcommand*{\\theHtheorem}{\\theHsection.\\arabic{theorem}}\n"
             "\\renewcommand*{\\theHequation}{\\theHsection.\\arabic{equation}}\n"
             "\\renewcommand*{\\theHfigure}{\\arabic{arbvolume}.\\arabic{figure}}\n"
             "\\renewcommand*{\\theHtable}{\\arabic{arbvolume}.\\arabic{table}}",
             "\\begin{document}\n\\maketitle\n\\thispagestyle{empty}",
             "\\clearpage\n\\tableofcontents\n\\clearpage",
             OMNIBUS_INTRO]
    for vol in vols:
        text = (srcdir / f"{vol}.tex").read_text()
        title, sub = vol_title(vol)
        short = vol.replace("-guide", "").replace("halo2-intuition", "h2i")
        macros = []
        for ln in preamble_of(text).splitlines():
            m = MACRO_RE.match(ln.strip())
            if m:
                name, nargs, body = m.group(1), m.group(2), m.group(3)
                args = "".join(f"#{i+1}" for i in range(int(nargs[1:-1]))) \
                    if nargs else ""
                macros.append(f"\\def{name}{args}{{{body}}}")
        body = text.split("\\begin{document}", 1)[1].rsplit("\\end{document}", 1)[0]
        for drop in ("\\maketitle", "\\thispagestyle{empty}",
                     "\\tableofcontents"):
            body = body.replace(drop + "\n", "").replace(drop, "")
        body = re.sub(r"(\\clearpage\s*)+", "\n", body, count=2)
        if srcdir == WEBDIR:
            body = body.replace("\\begin{abstract}", "").replace(
                "\\end{abstract}", "")
        body = re.sub(
            r"(\\(?:label|ref|eqref|pageref|autoref|cref|Cref)\{)([^}]+)\}",
            lambda m: m.group(1) + ",".join(
                f"{short}:{x.strip()}" for x in m.group(2).split(",")) + "}",
            body)
        body = re.sub(r"(\\hyperref\[)([^\]]+)\]",
                      lambda m: f"{m.group(1)}{short}:{m.group(2)}]", body)
        heading = (f"\\part*{{{title}: {sub}}}\n"
                   f"\\phantomsection\\addcontentsline{{toc}}{{part}}"
                   f"{{{title}: {sub}}}"
                   if vol in companions else f"\\part{{{title}: {sub}}}")
        parts.append(
            "\\clearpage\n"
            "\\stepcounter{arbvolume}\n"
            "\\setcounter{section}{0}\\setcounter{equation}{0}"
            "\\setcounter{figure}{0}\\setcounter{table}{0}\n"
            f"{heading}\n" + "\n".join(macros) + "\n" + body)
    parts.append("\\end{document}")
    out.write_text("\n".join(parts))
    print(f"wrote {out} ({len(vols)} parts)")


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
<div class="links"><a href="{vol}/">Web</a>
<a href="pdf/{vol}.pdf">PDF</a></div></li>""")
    cards = []
    for group, items in groups.items():
        cards.append(f'<h3 class="grp">{group}</h3><ol class="plates">'
                     + "\n".join(items) + "</ol>")
    complete = """<h3 class="grp">Complete edition</h3><ol class="plates">
<li class="plate">
<div class="label"><span class="acc">all volumes</span>
<span class="plaque">complete</span></div>
<a class="title" href="complete/">The Complete Arboretum</a>
<p class="sub">Foundations, deployed protocol, and frontier designs</p>
<div class="links"><a href="complete/">Web</a>
<a href="pdf/arboretum-complete.pdf">PDF</a></div></li>
</ol>"""
    html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>The Zcash Arboretum</title>
{THEME_INIT}
<link rel="stylesheet" href="arboretum.css?v={ver()}">
<link href="pagefind/pagefind-ui.css" rel="stylesheet">
<script src="pagefind/pagefind-ui.js"></script>
</head><body>
<main class="arb-landing">
<div class="arb-heading"><h1>The Zcash Arboretum</h1>
{THEME_PICKER}</div>
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
{complete}
<footer class="foot">
<p><a href="concordance.html">Concordance</a> &middot; Spotted an error?
<a href="https://github.com/upbqdn/zcash-arboretum/issues/new">Open an issue</a>.</p>
</footer>
</main></body></html>
"""
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    comp = ROOT / "arboretum-complete.pdf"
    if comp.exists():
        import shutil
        (out / "pdf").mkdir(parents=True, exist_ok=True)
        shutil.copy(comp, out / "pdf" / comp.name)
    (out / "index.html").write_text(html)
    print(f"wrote {out / 'index.html'}")


def concordance(outdir):
    """ZIP number -> (volume, section) index, scanned from the sources."""
    import collections
    zips = collections.defaultdict(set)
    specs = collections.defaultdict(set)
    for vol, _g, _c in VOLUME_META:
        p = ROOT / f"{vol}.tex"
        if not p.exists():
            continue
        title, _ = vol_title(vol)
        sec = "front matter"
        prev = ""
        for ln in p.read_text().splitlines():
            if ln.lstrip().startswith("%"):
                continue
            m = re.match(r"\\section\{([^}]*)\}", ln.strip())
            if m:
                sec = m.group(1)
            for z in re.findall(r"ZIP[-~ ]?(\d{2,4})\b", ln):
                zips[int(z)].add((vol, title, sec))
            # protocol-spec sections; skip cross-volume cites ("... Guide"
            # on the same line) and internal \S\ref uses
            if not re.search(r"\\emph\{[^}]*Guide", prev + " " + ln):
                for sp in re.findall(r"\\S[~ ]?(\d+(?:\.\d+)+)", ln):
                    specs[tuple(int(x) for x in sp.split("."))].add(
                        (vol, title, sec))
            prev = ln
    rows = []
    for z in sorted(zips):
        refs = "; ".join(
            f'<a href="{v}/">{t}</a> &mdash; {s}'
            for v, t, s in sorted(zips[z], key=lambda x: (x[1], x[2])))
        rows.append(f'<tr><td class="zk">ZIP {z}</td><td>{refs}</td></tr>')
    srows = []
    for sp in sorted(specs):
        dotted = ".".join(str(x) for x in sp)
        refs = "; ".join(
            f'<a href="{v}/">{t}</a> &mdash; {s}'
            for v, t, s in sorted(specs[sp], key=lambda x: (x[1], x[2])))
        srows.append(f'<tr><td class="zk">&sect; {dotted}</td>'
                     f'<td>{refs}</td></tr>')
    html = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Concordance &mdash; The Zcash Arboretum</title>
{THEME_INIT}
<link rel="stylesheet" href="arboretum.css?v={ver()}">
<style>
.zc table {{ border-collapse: collapse; width: 100%; font-size: .93rem; }}
.zc td {{ border-top: 1px solid var(--edge); padding: .45rem .6rem;
          vertical-align: top; }}
.zc td.zk {{ font-family: var(--mono); font-size: .74rem;
             letter-spacing: .08em; white-space: nowrap; width: 6rem;
             color: var(--plaque-ink); }}
</style></head><body>
<main class="arb-landing zc">
<div class="arb-heading"><h1>Concordance</h1>
{THEME_PICKER}</div>
<hr class="stem">
<p class="tag">Every ZIP and protocol-specification section cited across
the volumes, and where each is treated. Generated from the sources.</p>
<table>{"".join(rows)}</table>
<h2>Protocol specification</h2>
<table>{"".join(srows)}</table>
<p class="foot"><a href="./">The Zcash Arboretum</a></p>
</main></body></html>"""
    out = Path(outdir); out.mkdir(parents=True, exist_ok=True)
    (out / "concordance.html").write_text(html)
    print(f"concordance: {len(zips)} ZIPs, {len(specs)} spec sections")


def postprocess(outdir):
    """Ensure the complete edition exists, then finish every HTML page."""
    out = Path(outdir)
    complete = out / "complete"
    if not complete.is_dir():
        subprocess.run([
            "latexmlc", f"--dest={complete / 'index.html'}",
            "--splitat=section", "--format=html5",
            "--navigationtoc=context", "--css=../arboretum.css",
            "--timeout=1800", "build/web/arboretum-complete.tex",
        ], cwd=ROOT, check=True)
    for asset in ("mathjax", "@mathjax"):
        shutil.copytree(ROOT / "site" / asset, out / asset, dirs_exist_ok=True)
    documents = [(vol, vol_title(vol)[0], vol)
                 for vol, _group, _chip in VOLUME_META]
    documents.append(("complete", "The Complete Arboretum",
                      "arboretum-complete"))
    for vol, title, pdf in documents:
        vdir = out / vol
        if not vdir.is_dir():
            continue
        bar = f"""<header class="arb-bar"><a class="wordmark" href="../"><span
class="wordmark-prefix">The Zcash </span>Arboretum</a><span class="volname">{title}</span>
<a class="arb-pdf" href="../pdf/{pdf}.pdf">PDF</a>
{THEME_PICKER}
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
            if match := UNEXPANDED_CREF_RE.search(t):
                raise RuntimeError(
                    f"{page}: unexpanded cross-reference macro {match.group()}")
            t2 = re.sub(r'(<head[^>]*>)',
                        lambda m: m.group(1) + THEME_INIT, t, count=1)
            t2 = t2.replace('href="../arboretum.css"',
                           f'href="../arboretum.css?v={ver()}"', 1)
            t2 = re.sub(r"<body", '<body data-arb=\"vol\"', t2, count=1)
            if vol == "complete":
                t2 = re.sub(r"<body", '<body data-pagefind-ignore', t2,
                            count=1)
            t2 = re.sub(r"(<body[^>]*>)", r"\1" + bar.replace("\\", "\\\\"),
                        t2, count=1)
            if vol != "complete":
                t2 = t2.replace('class="ltx_page_content"',
                                'class="ltx_page_content" data-pagefind-body',
                                1)
            t2 = THEOREM_TITLE_RE.sub(
                lambda m: (f'{m.group(1)}{m.group(3)}'
                           f'<a class="arb-permalink" href="#{m.group(2)}" '
                           f'aria-label="Permalink to this item" '
                           f'title="Permalink">#</a>'
                           f'{m.group(4)}'), t2)
            t2 = re.sub(
                r'Generated\s+on [^<]+ by '
                r'(<a [^>]*class="ltx_LaTeXML_logo"[\s\S]*?</a>)',
                r'Generated with \1.', t2, count=1)
            t2 = t2.replace(
                '</div></footer>',
                '</div>\n<div class="arb-feedback">Spotted an error? '
                '<a href="https://github.com/upbqdn/zcash-arboretum/issues/new">'
                'Open an issue</a>.</div>\n</footer>', 1)
            t2 = PROOF_MATH_END_RE.sub(
                r'<span class="arb-proof-end">\1\2</span>', t2)
            t2 = re.sub(r'\s*∎(?=</p>)',
                        ' <span class="arb-qed">□</span>', t2)
            t2 = t2.replace('</body>', MATHJAX + '\n</body>', 1)
            if t2 != t:
                page.write_text(t2)
                n += 1
        print(f"postprocessed {vol}: {n} pages")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "volumes":
        print(*VOLUMES)
    elif mode == "render":
        render()
    elif mode == "webprep":
        webprep()
    elif mode == "landing":
        landing(sys.argv[sys.argv.index("--out") + 1])
    elif mode == "concordance":
        concordance(sys.argv[sys.argv.index("--out") + 1])
    elif mode == "omnibus":
        omnibus()
    elif mode == "postprocess":
        postprocess(sys.argv[sys.argv.index("--out") + 1])
    else:
        sys.exit(__doc__)
