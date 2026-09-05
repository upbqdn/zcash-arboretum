#!/usr/bin/env python3
"""Small regression check for shared generated-site controls."""

import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent))
import sitegen  # noqa: E402

PARKED = ("pq-guide", "tachyon-guide", "voting-guide")
assert all((sitegen.ROOT / f"{vol}.tex").is_file() for vol in PARKED)
assert set(PARKED).isdisjoint(sitegen.VOLUMES)


with tempfile.TemporaryDirectory() as tmp:
    out = Path(tmp)
    sitegen.landing(out)
    sitegen.concordance(out)
    for name in ("index.html", "concordance.html"):
        html = (out / name).read_text()
        assert html.index(sitegen.THEME_INIT) < html.index("arboretum.css")
        assert html.count('class="arb-theme"') == 1
        for value in ("system", "light", "warm", "dark", "midnight"):
            assert f'value="{value}"' in html
        assert ">Warm light</option>" in html
        assert ">Warm dark</option>" in html

    landing = (out / "index.html").read_text()
    concordance = (out / "concordance.html").read_text()
    for vol in PARKED:
        assert f'href="{vol}/"' not in landing
        assert f'href="{vol}/"' not in concordance
    assert landing.count('href="complete/"') == 2
    assert landing.count('href="pdf/arboretum-complete.pdf"') == 1
    assert "Foundations, deployed protocol, and frontier designs" in landing
    assert landing.index('<h3 class="grp">Frontier</h3>') < landing.index(
        '<h3 class="grp">Complete edition</h3>')
    assert (out / "pdf" / "arboretum-complete.pdf").is_file()

    omnibus = out / "arboretum-complete.tex"
    sitegen.omnibus(out=omnibus)
    complete_tex = omnibus.read_text()
    assert sitegen.OMNIBUS_INTRO in complete_tex
    assert complete_tex.count("\\stepcounter{arbvolume}") == len(
        sitegen.VOLUMES)
    assert "\\part*{How Halo 2 Proves:" in complete_tex
    for vol in PARKED:
        title, subtitle = sitegen.vol_title(vol)
        assert f"\\part{{{title}: {subtitle}}}" not in complete_tex

    webdir = out / "web"
    webdir.mkdir()
    (webdir / "math-guide.tex").write_text(r"""\documentclass{article}
\begin{document}
\begin{abstract}
Volume summary.
\end{abstract}
\section{First section}
\end{document}
""")
    web_omnibus = out / "web-complete.tex"
    with patch.object(sitegen, "WEBDIR", webdir):
        sitegen.omnibus(webdir, web_omnibus)
    web_tex = web_omnibus.read_text()
    assert "\\begin{abstract}" not in web_tex
    assert web_tex.index("Volume summary.") < web_tex.index(
        "\\section{First section}")

    page = out / "math-guide" / "index.html"
    page.parent.mkdir()
    page.write_text(
        '<html><head><link rel="stylesheet" href="../arboretum.css"></head>'
        '<body><main class="ltx_page_content">'
        '<div id="Thmtheorem1" class="ltx_theorem ltx_theorem_proposition">'
        '<h6 class="ltx_title ltx_runin ltx_title_theorem">'
        '<span class="ltx_tag ltx_tag_theorem">Proposition 1.1</span> '
        '(<a class="ltx_ref" href="#Thmtheorem0">prior result</a>).'
        '</h6><div class="ltx_para"><p>A result.</p></div></div>'
        '<div class="ltx_proof"><p>'
        'Given <math display="inline" alttext="S"><mi>S</mi></math>, thus '
        '<math display="inline" alttext="x=1"><mi>x</mi></math>.\n∎'
        '</p><p>Done.\n∎</p></div></main>'
        '<footer><div>Generated on today by '
        '<a class="ltx_LaTeXML_logo">LaTeXML</a></div></footer></body></html>')
    complete_page = out / "complete" / "index.html"
    run = sitegen.subprocess.run

    def build_complete(args, **kwargs):
        if args[0] != "latexmlc":
            return run(args, **kwargs)
        assert args[-1] == "build/web/arboretum-complete.tex"
        assert kwargs == {"cwd": sitegen.ROOT, "check": True}
        complete_page.parent.mkdir()
        complete_page.write_text(
            '<html><head><link rel="stylesheet" href="../arboretum.css"></head>'
            '<body><main class="ltx_page_content"></main>'
            '<footer><div></div></footer></body></html>')

    with patch.object(sitegen.subprocess, "run", side_effect=build_complete):
        sitegen.postprocess(out)
    html = page.read_text()
    assert html.index(sitegen.THEME_INIT) < html.index("arboretum.css")
    assert html.count('class="arb-theme"') == 1
    assert '<body data-arb="vol">' in html
    assert html.count("window.MathJax") == 1
    assert 'font: \'mathjax-stix2\'' in html
    assert "macros: { qed: '\\\\tag*{□}' }" in html
    assert "linebreaks: { inline: true" in html
    assert "replace(/%\\s+/g, '')" in html
    assert 'src="../mathjax/tex-chtml.js"' in html
    assert ('<a class="ltx_ref" href="#Thmtheorem0">prior result</a>).'
            '<a class="arb-permalink" href="#Thmtheorem1" '
            'aria-label="Permalink to this item" '
            'title="Permalink">#</a></h6>') in html
    assert html.count('class="arb-permalink"') == 1
    assert ('<span class="arb-proof-end"><math display="inline" '
            'alttext="x=1"><mi>x</mi></math>.</span> '
            '<span class="arb-qed">□</span>') in html
    assert html.count('class="arb-proof-end"') == 1
    assert html.count('class="arb-qed"') == 2
    complete_html = complete_page.read_text()
    assert '<body data-pagefind-ignore data-arb="vol">' in complete_html
    assert '../pdf/arboretum-complete.pdf' in complete_html
    assert 'The Complete Arboretum' in complete_html
    assert (out / "mathjax" / "tex-chtml.js").is_file()
    assert (out / "@mathjax" / "mathjax-stix2-font" / "chtml.js").is_file()

    page.write_text(page.read_text().replace(
        "Done.", r"Done \crefpairconjunction."))
    try:
        sitegen.postprocess(out)
    except RuntimeError as error:
        assert r"\crefpairconjunction" in str(error)
    else:
        raise AssertionError("unexpanded cross-reference macro was accepted")

css = (sitegen.ROOT / "site" / "arboretum.css").read_text()
assert ':root[data-theme="warm"]' in css
assert ':root[data-theme="dark"]' in css
assert ':root[data-theme="midnight"]' in css
assert '.ltx_theorem .arb-permalink {' in css
assert 'a[rel="next"] { margin-left: 0; align-self: flex-end; }' in css
assert 'mjx-container.arb-math-scroll' in css
assert (sitegen.ROOT / "site" / "mathjax" / "tex-chtml.js").is_file()
assert (sitegen.ROOT / "site" / "@mathjax" / "mathjax-stix2-font"
        / "chtml.js").is_file()
print("site generator checks passed")
