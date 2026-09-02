#!/usr/bin/env python3
"""Small regression check for shared generated-site controls."""

import sys
import tempfile
from pathlib import Path

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
    assert landing.count('href="pdf/arboretum-complete.pdf"') == 2
    assert "Every volume in a single document" in landing
    assert (out / "pdf" / "arboretum-complete.pdf").is_file()

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
