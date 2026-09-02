#!/usr/bin/env python3
"""Small regression check for shared generated-site controls."""

import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent))
import sitegen  # noqa: E402


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

    page = out / "math-guide" / "index.html"
    page.parent.mkdir()
    page.write_text(
        '<html><head><link rel="stylesheet" href="../arboretum.css"></head>'
        '<body><main class="ltx_page_content"><div class="ltx_proof"><p>'
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

css = (sitegen.ROOT / "site" / "arboretum.css").read_text()
assert ':root[data-theme="warm"]' in css
assert ':root[data-theme="dark"]' in css
assert ':root[data-theme="midnight"]' in css
assert 'a[rel="next"] { margin-left: 0; align-self: flex-end; }' in css
assert 'mjx-container.arb-math-scroll' in css
assert (sitegen.ROOT / "site" / "mathjax" / "tex-chtml.js").is_file()
assert (sitegen.ROOT / "site" / "@mathjax" / "mathjax-stix2-font"
        / "chtml.js").is_file()
print("site generator checks passed")
