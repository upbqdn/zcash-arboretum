#!/usr/bin/env python3
"""Small regression check for shared generated-site controls."""

import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent))
import sitegen  # noqa: E402
from check_build import log_errors, source_errors  # noqa: E402
from check_site import check  # noqa: E402

with tempfile.TemporaryDirectory() as tmp:
    out = Path(tmp)
    assert check(out)[1] == ["no HTML pages"]
    (out / "index.html").write_text('<a href="other/?v=1#ok">next</a>')
    (out / "other").mkdir()
    (out / "other" / "index.html").write_text('<p id="ok">OK</p>')
    assert check(out) == (2, [])
    (out / "other" / "index.html").write_text(
        '<p id="wrong"></p><p id="wrong"></p><img src="missing.png">')
    errors = check(out)[1]
    assert len(errors) == 3, errors
    assert any("missing anchor" in error for error in errors)
    assert any("duplicate ID" in error for error in errors)
    assert any("missing missing.png" in error for error in errors)
    (out / "other" / "index.html").write_text(
        '<p id="ok"></p><img src=""><span class="ltx_ERROR">bad</span>')
    errors = check(out)[1]
    assert len(errors) == 2, errors
    assert any("image has no source" in error for error in errors)
    assert any("LaTeXML error markup" in error for error in errors)

assert not log_errors("Underfull \\hbox (badness 1000)\nOutput written.")
document = "\\begin{document}\nText.\n\\end{document}\n"
assert not source_errors(document + "% A trailing comment is fine.\n")
assert source_errors(document + "discarded text")
assert source_errors(document + document)
assert source_errors("")
for warning in (r"Overfull \hbox (2.0pt too wide)",
                r"Overfull \vbox (2.0pt too high)",
                "LaTeX Warning: There were undefined references.",
                "LaTeX Warning: Label `sec:x' multiply defined.",
                "Missing character: There is no x in font nullfont!",
                "! Undefined control sequence."):
    assert log_errors(warning), warning

PARKED = ("pq-guide", "tachyon-guide", "voting-guide")
MERGED = "halo2-intuition-guide"
assert all((sitegen.ROOT / "parked" / f"{vol}.tex").is_file()
           for vol in PARKED)
assert set(PARKED).isdisjoint(sitegen.VOLUMES)
assert MERGED not in sitegen.VOLUMES
assert not (sitegen.ROOT / f"{MERGED}.tex").exists()
assert not (sitegen.ROOT / f"{MERGED}.pdf").exists()
assert next((group, chip) for vol, group, chip in sitegen.VOLUME_META
            if vol == "flyclient-guide") == ("Frontier", "design-stage")

# Existing section and heading links survive; new IDs cannot collide with any
# existing element, including one that appears later in the document.
headings = (
    '<section id="SS1"><h2 class="ltx_title">First</h2></section>'
    '<section id="SS2"><h3 id="custom">Existing</h3></section>'
    "<section id='SS3'><h4 id = 'single-quoted'>Existing too</h4></section>"
    '<section><h1>Page introduction</h1></section>'
    '<section id="SS4"><h2>Collision</h2></section>'
    '<span id="SS4-heading"></span><span id="SS4-heading-2"></span>'
    '<section id="A&amp;B"><h2>Escaped</h2></section>'
    '<span id="A&#38;B-heading"></span>')
anchored = sitegen.heading_anchors(headings)
assert '<section id="SS1"><h2 class="ltx_title" id="SS1-heading">' in anchored
assert '<h3 id="custom">' in anchored
assert "<h4 id = 'single-quoted'>" in anchored
assert '<section><h1>Page introduction</h1></section>' in anchored
assert '<section id="SS4"><h2 id="SS4-heading-3">' in anchored
assert '<section id="A&amp;B"><h2 id="A&amp;B-heading-2">' in anchored
assert sitegen.heading_anchors(anchored) == anchored

for expression, expected in (
        ('<msup><mi>x</mi><mn>2</mn></msup>', 'x^(2)'),
        ('<msup><mrow><mi>x</mi><mo>+</mo><mi>y</mi></mrow><mn>2</mn></msup>',
         '(x+y)^(2)'),
        ('<msub><mi>𝔽</mi><mi>r</mi></msub>', '𝔽_(r)'),
        ('<msubsup><mi>ψ</mi><mi>nf</mi><mn>2</mn></msubsup>', 'ψ_(nf)^(2)'),
        ('<mrow><mi>α</mi><mo>+</mo><mi>β</mi></mrow>', 'α+β'),
        ('<mrow><mn>𝟶</mn><mo>⁢</mo><mi>𝚡</mi><mo>⁢</mo><mn>𝟶𝟹</mn></mrow>',
         '𝟶⁢𝚡⁢𝟶𝟹'),
        ('<mrow><mtext>A</mtext><mspace/><mtext>B</mtext></mrow>', 'A B')):
    assert sitegen.math_search_text(f'<math>{expression}</math>') == expected
assert sitegen.math_search_text(
    r'<math alttext="\frac{x}{y}"><mfrac><mi>x</mi><mi>y</mi></mfrac></math>'
) == r'\frac{x}{y}'
math_heading = (
    '<section id="SS1"><h2 id="SS1-heading">A &amp; B: '
    '<math alttext="x^2"><msup><mi>x</mi><mn>2</mn></msup></math>'
    ' &lt; "limit"</h2></section>')
titled = sitegen.heading_search_titles(math_heading)
assert ('data-pagefind-meta="heading-SS1-heading:A &amp; B: x^(2) '
        '&lt; &quot;limit&quot;"') in titled
assert sitegen.heading_search_titles(titled) == titled
assert titled[titled.index('<math'):titled.index('</math>') + 7] in math_heading


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
    assert landing.count("showImages: false") == 1
    assert landing.count(sitegen.SEARCH_OPTIONS) == 1
    assert "details.arb-search" not in landing
    assert "ZIP 316" in concordance
    assert "<table></table>" not in concordance
    assert "<h2>Protocol specification</h2>" in concordance
    assert "&sect; 4.2.3" in concordance
    for vol in PARKED:
        assert f'href="{vol}/"' not in landing
        assert f'href="{vol}/"' not in concordance
    assert f'href="{MERGED}/"' not in landing
    assert f'href="{MERGED}/"' not in concordance
    assert landing.count('href="complete/"') == 2
    assert landing.count('href="pdf/arboretum-complete.pdf"') == 1
    assert "Foundations, deployed protocol, and frontier designs" in landing
    assert landing.index('<h3 class="grp">Frontier</h3>') < landing.index(
        '<h3 class="grp">Complete edition</h3>')
    assert (out / "pdf" / "arboretum-complete.pdf").is_file()

    omnibus = out / "arboretum-complete.tex"
    sitegen.omnibus(out=omnibus)
    complete_tex = omnibus.read_text()
    native_section_id = (
        r"\def\thesection@ID{V\arabic{arbvolume}.S\@section@ID}")
    assert native_section_id not in complete_tex
    assert sitegen.OMNIBUS_INTRO in complete_tex
    assert r"\setlength{\headheight}{20pt}" in complete_tex
    assert complete_tex.count("\\stepcounter{arbvolume}") == len(
        sitegen.VOLUMES)
    assert "\\part*{How Halo 2 Proves:" not in complete_tex
    assert "\\section{Worked example: one computation," in complete_tex
    for title in ("PQ Guide", "Tachyon Guide", "Voting Guide"):
        assert f"\\part{{{title}:" not in complete_tex

    webdir = out / "web"
    webdir.mkdir()
    with patch.object(sitegen, "WEBDIR", webdir):
        sitegen.webprep()
    for volume in ("math-guide", "crypto-guide", "arboretum-complete"):
        assert r"\mdfsetup" not in (webdir / f"{volume}.tex").read_text()
    assert "Statistical distance" in (webdir / "math-guide.tex").read_text()
    assert "FF1" in (webdir / "crypto-guide.tex").read_text()
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
    assert web_tex.count(native_section_id) == 1
    assert web_tex.index(native_section_id) < web_tex.index(r"\begin{document}")
    assert "\\begin{abstract}" not in web_tex
    assert web_tex.index("Volume summary.") < web_tex.index(
        "\\section{First section}")

    page = out / "math-guide" / "index.html"
    page.parent.mkdir()
    page.write_text(
        '<html><head><link rel="stylesheet" '
        'href="_site/math-guide/arboretum.css"></head>'
        '<body><main class="ltx_page_content">'
        '<section id="SS1"><h2 class="ltx_title">A subsection</h2></section>'
        '<section id="SS2"><h2>Squared '
        '<math alttext="x^2"><msup><mi>x</mi><mn>2</mn></msup></math>'
        '</h2></section>'
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
    complete_page.parent.mkdir()  # A failed prior build may leave the directory.
    run = sitegen.subprocess.run

    def build_complete(args, **kwargs):
        if args[0] != "latexmlc":
            return run(args, **kwargs)
        assert args[-1] == "build/web/arboretum-complete.tex"
        assert kwargs == {"cwd": sitegen.ROOT, "check": True}
        complete_page.write_text(
            '<html><head><link rel="stylesheet" href="../arboretum.css"></head>'
            '<body><main class="ltx_page_content">'
            '<section id="SS1"><h2>A complete subsection</h2></section></main>'
            '<footer><div></div></footer></body></html>')

    with patch.object(sitegen.subprocess, "run", side_effect=build_complete):
        sitegen.postprocess(out)
    html = page.read_text()
    assert html.index(sitegen.THEME_INIT) < html.index("arboretum.css")
    assert html.count('class="arb-theme"') == 1
    assert html.count("showImages: false") == 1
    assert html.count(sitegen.SEARCH_OPTIONS) == 1
    assert html.count('data-pagefind-meta="volume:Math Guide"') == 1
    assert '<section id="SS1"><h2 class="ltx_title" id="SS1-heading">' in html
    assert 'data-pagefind-meta="heading-SS2-heading:Squared x^(2)"' in html
    assert "if (!search.contains(e.target)) search.open = false" in html
    assert "e.button === 0 && !e.ctrlKey && !e.metaKey && !e.shiftKey && !e.altKey" in html
    assert "e.target.closest('.arb-search a.pagefind-ui__result-link')" in html
    assert "e.key === 'Escape' && search.open" in html
    assert '<body data-arb="vol">' in html
    assert html.count("window.MathJax") == 1
    assert 'href="../arboretum.css?v=' in html
    assert 'href="_site/math-guide/arboretum.css"' not in html
    assert 'font: \'mathjax-stix2\'' in html
    assert "macros: { qed: '\\\\tag*{□}' }" in html
    assert "linebreaks: { inline: true" in html
    assert "replace(/%\\s+/g, '')" in html
    assert 'src="../mathjax/tex-chtml.js"' in html
    assert ('<a class="ltx_ref" href="#Thmtheorem0">prior result</a>).'
            '<a class="arb-permalink" data-pagefind-ignore href="#Thmtheorem1" '
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
    assert '<section id="SS1"><h2 id="SS1-heading">' in complete_html
    assert 'data-pagefind-meta="volume:' not in complete_html
    assert (out / "mathjax" / "tex-chtml.js").is_file()
    boldsymbol = out / "mathjax" / "input" / "tex" / "extensions" / "boldsymbol.js"
    assert 'checkVersion("[tex]/boldsymbol","4.1.1"' in boldsymbol.read_text()
    assert (out / "@mathjax" / "mathjax-stix2-font" / "chtml.js").is_file()

    # A second finishing pass must not duplicate controls, scripts or IDs.
    sitegen.postprocess(out)
    assert page.read_text() == html
    assert complete_page.read_text() == complete_html

    # Previously finished HTML needs heading anchors and metadata too, without
    # duplicating existing controls, theorem links or formatting.
    page.write_text(html.replace(' id="SS1-heading"', '').replace(
        ' data-pagefind-meta="volume:Math Guide"', '').replace(
        'class="arb-permalink" data-pagefind-ignore', 'class="arb-permalink"').replace(
        ' data-pagefind-meta="heading-SS2-heading:Squared x^(2)"', ''))
    complete_page.write_text(complete_html.replace(' id="SS1-heading"', ''))
    sitegen.postprocess(out)
    assert page.read_text() == html
    assert complete_page.read_text() == complete_html

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
search_panel = css.split('.arb-bar .arb-search-panel {', 1)[1].split('}', 1)[0]
assert 'max-height: calc(100dvh - 4rem)' in search_panel
assert 'overflow-y: auto' in search_panel
assert 'overscroll-behavior-y: contain' in search_panel
assert (sitegen.ROOT / "site" / "mathjax" / "tex-chtml.js").is_file()
assert (sitegen.ROOT / "site" / "@mathjax" / "mathjax-stix2-font"
        / "chtml.js").is_file()
print("site generator checks passed")
