#!/usr/bin/env python3
"""Small regression check for shared generated-site controls."""

import re
import shutil
import subprocess
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
    # A linked stylesheet's fonts must ship; an unlinked copy is not checked.
    (out / "other" / "index.html").write_text(
        '<p id="ok"></p><link rel="stylesheet" href="../site.css?v=1">')
    (out / "site.css").write_text('@font-face { src: url("fonts/a.woff2"), url(data:x); }')
    (out / "other" / "site.css").write_text('@font-face { src: url("fonts/b.woff2"); }')
    assert check(out)[1] == ["site.css: missing fonts/a.woff2"], check(out)[1]
    (out / "fonts").mkdir()
    (out / "fonts" / "a.woff2").write_bytes(b"")
    assert check(out) == (2, [])

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

# An inline formula breaks where TeX breaks it: after a relation or binary operator, not inside a
# tuple, not after a unary sign. Each piece is its own <math>; nothing but invisible operators is
# lost, and only the first piece keeps the ID and the TeX.
split = sitegen.mathml_fix(
    '<math id="m" alttext="a=b+c" display="inline"><mrow><mi>a</mi><mo>=</mo>'
    '<mrow><mi>b</mi><mo>+</mo><mrow><mo stretchy="false">(</mo><mi>c</mi><mo>,</mo>'
    '<mrow><mo>−</mo><mi>d</mi></mrow><mo stretchy="false">)</mo></mrow></mrow></mrow></math>')
assert split.count('<wbr>') == 2 and split.count('<math') == 3, split
assert split.count('id="m"') == 1 and split.count('alttext=') == 1, split
assert '<mo>=</mo></math><wbr>' in split and '<mo>+</mo></math><wbr>' in split, split
assert sitegen.mathml_fix(split.split('<wbr>')[0]) == split.split('<wbr>')[0]
assert '<wbr>' not in sitegen.mathml_fix(
    '<math display="inline"><mi>a</mi><mo>=</mo><mi>b</mi></math>', split=False)
assert '<wbr>' not in sitegen.native_math(
    '<table><tr><td><math display="inline"><mi>a</mi><mo>=</mo><mi>b</mi></math></td></tr></table>')
# Search sees a formula's NFKC text; the MathML itself is not indexed.
indexed = sitegen.MATH_RE.sub(sitegen.ascii_copy, '<math><mi>𝗂𝗏𝗄</mi><mo>∈</mo><mi>K</mi></math>')
assert indexed.startswith('<math data-pagefind-ignore="all">')
assert indexed.endswith('<span class="arb-idx" hidden> ivk ∈ K </span>'), indexed
# \, stays a kern in text, but a tag's attributes are never rewritten; text glued to a formula
# stays with it.
kept = sitegen.text_fixes('<a title="§\u20095">§\u20095</a> (<math><mi>x</mi></math>), y')
assert kept == ('<a title="§\u20095"><span class="arb-nobr">§\u20095</span></a> '
                '<span class="arb-nobr">(<math><mi>x</mi></math>),</span> y'), kept
# Glued text holds to the adjacent piece only: a <wbr> in a nowrap span breaks in Chromium alone.
assert sitegen.unglue(
    '<span class="arb-proof-end"><span class="arb-nobr">(<math>a</math><wbr><math>b</math><wbr>'
    '<math>c</math><span class="arb-idx" hidden> a b c </span>).</span></span>') == (
    '<span class="arb-proof-end"><span class="arb-nobr">(<math>a</math></span></span><wbr>'
    '<math>b</math><wbr><span class="arb-proof-end"><span class="arb-nobr"><math>c</math>'
    '<span class="arb-idx" hidden> a b c </span>).</span></span>')
# A prime follows its base at base size, never in the superscript (Garamond-Math's is raised);
# a script's other content stays a script, after the prime.
prime = sitegen.mathml_fix(
    '<math display="inline"><mrow><msup><mi>a</mi><mo>′</mo></msup><mo>=</mo>'
    '<msubsup><mi>b</mi><mi>i</mi><mo>′</mo></msubsup><mo>+</mo>'
    '<msup><mi>y</mi><mrow><mo>′</mo><mn>2</mn></mrow></msup></mrow></math>', split=False)
p = '<mo form="postfix" lspace="0em" rspace="0em">′</mo>'
assert f'<mrow><mi>a</mi>{p}</mrow>' in prime, prime
assert f'<msub><mrow><mi>b</mi>{p}</mrow><mi>i</mi></msub>' in prime, prime
assert f'<msup><mrow><mi>y</mi>{p}</mrow><mrow><mn>2</mn></mrow></msup>' in prime, prime
# A comma keeps TeX's thin space before an operator LaTeXML spaced it against, not in a script.
comma = sitegen.mathml_fix(
    '<math display="inline"><mrow><mo>{</mo><mn>0</mn><mo rspace="0em">,</mo><mo>⊥</mo>'
    '<mo>}</mo><msub><mi>E</mi><mrow><mi>P</mi><mo rspace="0em">,</mo><mo>⋅</mo></mrow></msub>'
    '</mrow></math>', split=False)
assert comma.count('<mo>,</mo>') == 1 and '<mo rspace="0em" lspace="0em">,' in comma, comma
# \, in a \mathtt constant is TeX's 0.167 em, not the mono's U+2009; its pieces take the
# Unicode monospace of the rest of the constant, and keep their size.
hexed = sitegen.mathml_fix('<math display="inline"><mn class="ltx_mathvariant_monospace" '
                           'mathvariant="monospace" mathsize="80%"> 0db5 7d4a</mn>'
                           '</math>', split=False)
assert hexed == (
    '<math display="inline"><mspace width="0.167em"></mspace>'
    '<mn mathsize="80%">𝟶𝚍𝚋𝟻</mn><mspace width="0.167em"></mspace>'
    '<mn mathsize="80%">𝟽𝚍𝟺𝚊</mn></math>'), hexed
# A multi-letter run of a \mathtt constant is text, a letter an identifier.
runs = sitegen.mathml_fix('<math display="inline"><mrow><mi>𝚋</mi><mo>⁢</mo><mi>𝚎𝟼</mi>'
                          '</mrow></math>', split=False)
assert '<mi>𝚋</mi>' in runs and '<mtext>𝚎𝟼</mtext>' in runs, runs

# The inline scripts parse: a stray brace once silently disabled the theme control.
if shutil.which("node"):
    with tempfile.TemporaryDirectory() as tmp:
        for name in ("THEME_INIT", "PAGE_SCRIPT", "TOC_SCRIPT", "TRIM_SCRIPT"):
            js = Path(tmp) / f"{name}.js"
            js.write_text(getattr(sitegen, name).removeprefix("<script>").removesuffix("</script>"))
            run = subprocess.run(["node", "--check", str(js)], capture_output=True, text=True)
            assert run.returncode == 0, (name, run.stderr)

PARKED = ("pq-guide", "tachyon-guide", "voting-guide", "crosslink-guide")
MERGED = ("halo2-intuition-guide", "sync-guide")
assert all((sitegen.ROOT / "parked" / f"{vol}.tex").is_file()
           for vol in PARKED)
assert all((sitegen.ROOT / "parked" / f"{vol}.pdf").is_file()
           for vol in PARKED)
assert all(not (sitegen.ROOT / f"{vol}{suffix}").exists()
           for vol in PARKED for suffix in (".tex", ".pdf"))
assert set(PARKED).isdisjoint(sitegen.VOLUMES)
assert set(MERGED).isdisjoint(sitegen.VOLUMES)
assert all(not (sitegen.ROOT / f"{vol}{suffix}").exists()
           for vol in MERGED for suffix in (".tex", ".pdf"))
assert dict(sitegen.VOLUME_META)["flyclient-guide"] == "Frontier"
for n, (volume, _) in enumerate(sitegen.VOLUME_META):
    source = (sitegen.ROOT / f"{volume}.tex").read_text()
    body = source.split(r"\begin{document}")[1]
    assert body.count(r"\tableofcontents") == 1, volume
    assert body.index(r"\tableofcontents") < body.index(r"\section{"), volume
    assert sitegen.FONT_BLOCK in source, volume
    assert sitegen.DESIGN_BLOCK_RE.search(source), volume
    # the title page and running head carry the landing's numeral
    assert "\\renewcommand{\\accession}{%s}\n\\title{" % sitegen.ROMANS[n] in source, volume
for volume in PARKED:
    source = (sitegen.ROOT / "parked" / f"{volume}.tex").read_text()
    assert sitegen.FONT_BLOCK.replace("Path=fonts/", "Path=../fonts/") in source, volume
    assert sitegen.DESIGN_BLOCK_RE.search(source), volume
    assert "\\renewcommand{\\accession}" not in source, volume

# Table 2 introduces every Greek letter, with both lower-case and capital forms.
greek_table = (sitegen.ROOT / "math-guide.tex").read_text().split(
    r"\label{tab:notation-greek}")[0].rsplit(r"\begin{tabular}", 1)[1]
greek_rows = re.findall(r"\\\((.+?)\\\) & \\\((.+?)\\\) & ([a-z]+) &", greek_table)
assert len(greek_rows) == 24
assert [name for lower, capital, name in greek_rows] == (
    "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu "
    "nu xi omicron pi rho sigma tau upsilon phi chi psi omega").split()

# The Wallet Guide's chapters, synchronisation merged in, in order under one TOC.
WALLET_CHAPTERS = (
    "sec:intro", "sec:keys-zip32", "sec:addresses", "sec:sync-compact",
    "sec:sync-service", "sec:sync-scanning", "sec:sync-tree", "sec:sync-privacy",
    "sec:spendability", "sec:fees", "sec:pipeline", "sec:pczt", "sec:lifecycle",
    "sec:zip321",
)
wallet = (sitegen.ROOT / "wallet-guide.tex").read_text()
positions = [wallet.index(r"\label{" + label + "}") for label in WALLET_CHAPTERS]
assert positions == sorted(positions)
assert all(wallet.count(r"\label{" + label + "}") == 1 for label in WALLET_CHAPTERS)

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

# Whole titles are ordinary links: native keyboard access and copy-link work,
# while existing IDs, mathematical markup and authored citation links survive.
self_link_source = (
    '<h1 class="ltx_title ltx_title_section">'
    '<span class="ltx_tag ltx_tag_section">2 </span>Section title</h1>'
    '<span id="section-heading"></span>'
    '<h2 class="ltx_title ltx_title_subsection" id="kept">A '
    '<math alttext="x"><mi>x</mi></math> subsection</h2>'
    '<h3 class="ltx_title ltx_title_paragraph" id="paragraph">A paragraph</h3>'
    '<h1 class="ltx_title ltx_title_document">Guide title</h1>'
    '<h1 class="ltx_title ltx_title_part">Part title</h1>'
    '<div id="result" class="ltx_theorem"><h6 class="ltx_title">'
    '<span class="ltx_tag">Theorem 1</span> (A result).'
    '<a class="arb-permalink" data-pagefind-ignore href="#result">#</a>'
    '</h6></div>'
    '<div id="citing" class="ltx_theorem"><h6 class="ltx_title">'
    'Theorem 2 (<a href="#result">Theorem 1</a> revisited).</h6></div>')
self_linked = sitegen.heading_self_links(self_link_source)
assert self_linked.count('class="arb-heading-link"') == 5
assert '<h1 class="ltx_title ltx_title_document">Guide title</h1>' in self_linked
for identifier in ('section-heading-2', 'kept', 'paragraph', 'part-heading', 'result'):
    assert f'class="arb-heading-link" href="#{identifier}"' in self_linked
assert '<math alttext="x"><mi>x</mi></math>' in self_linked
assert '<span class="ltx_tag ltx_tag_section">2 </span>Section title</a></h1>' in self_linked
assert 'Theorem 2 (<a href="#result">Theorem 1</a> revisited).' in self_linked
assert self_linked.count('class="arb-permalink"') == 1
assert sitegen.heading_self_links(self_linked) == self_linked
assert 'data-pagefind-ignore' not in re.search(
    r'<a class="arb-heading-link"[^>]*>', self_linked).group()

# A title page shows the volume's name alone.
titled = sitegen.drop_subtitle(
    '<h1 class="ltx_title ltx_title_document" style="font-size:120%;"><span class="ltx_text '
    'ltx_font_bold" style="font-size:248%;">Wallet Guide <br class="ltx_break"></span>The Zcash '
    'wallet layer</h1><p>Body</p>')
assert titled == ('<h1 class="ltx_title ltx_title_document" style="font-size:120%;"><span '
                  'class="ltx_text ltx_font_bold" style="font-size:248%;">Wallet Guide</span>'
                  '</h1><p>Body</p>'), titled

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
    for volume in ('math-guide', 'crypto-guide', 'complete'):
        (out / volume).mkdir()
        (out / volume / 'index.html').write_text('')
    math_sections = (
        '<section><h1 class="ltx_title_section">'
        '<span class="ltx_tag">10 </span>Elliptic curves</h1>'
        '<section id="SS12"><h2 class="ltx_title_subsection">'
        '<span class="ltx_tag">10.12 </span>The '
        '<math alttext="j"><mi>𝑗</mi></math>-invariant</h2></section>'
        '<section id="SS13"><h2 class="ltx_title_subsection">'
        'The discrete logarithm problem</h2></section></section>')
    crypto_sections = (
        '<section><h1 class="ltx_title_section">Hash functions</h1>'
        '<section id="SS4"><h2 class="ltx_title_subsection">'
        '<span class="ltx_tag">3.4 </span>The random oracle model</h2></section>'
        '<section id="SS5"><h2 class="ltx_title_subsection">'
        'The discrete logarithm problem</h2></section>'
        '<section id="SS6"><h2 class="ltx_title_subsection">'
        'Privacy-preserving membership via zero-knowledge paths</h2></section>'
        '<div id="Thmtheorem1" class="ltx_theorem ltx_theorem_remark">'
        '<h6 class="ltx_title_theorem"><span class="ltx_tag">Remark 3.1</span> '
        '(Named remark).</h6></div></section>')
    for volume, number, filename, html in (
            ('math-guide', 1, 'S10.html', math_sections),
            ('crypto-guide', 2, 'S3.html', crypto_sections)):
        (out / volume / filename).write_text(html)
        (out / 'complete' / f'Pt{number}.html').write_text('')
        (out / 'complete' / f'V{number}.{filename}').write_text(html)
    # An earlier page's named definition must not hide a later section with
    # the same name. Explicit section citations take the section target.
    (out / 'crypto-guide' / 'index.html').write_text(
        '<div id="Thmtheorem1" class="ltx_theorem ltx_theorem_definition">'
        '<h6 class="ltx_title_theorem"><span class="ltx_tag">Definition 1</span> '
        '(The random oracle model).</h6></div>')
    index = sitegen.reference_index(out)
    source = (
        '<p><span class="ltx_font_italic">Crypto\nGuide</span>, '
        '§“The random oracle model” and §“The discrete logarithm problem”.</p>'
        '<figcaption>Math Guide, §“The '
        '<math alttext="j"><mi>𝑗</mi></math>-invariant”.</figcaption>'
        '<td>Crypto Guide’s “Named remark”.</td>'
        '<p>Crypto Guide, §Privacy-preserving membership via zero-knowledge paths.</p>'
        '<p>Math Guide: “The discrete logarithm problem”.</p>'
        '<p><a href="kept.html">Crypto Guide</a>, '
        '<a href="kept-section.html">§“The random oracle model”</a>.</p>'
        '<p><code>Crypto Guide, §“The random oracle model”</code>.</p>'
        '<p>Crosslink Guide, §“The discrete logarithm problem”.</p>'
        '<p>Crypto Guide owns this (ZIP 307, §“The random oracle model”).</p>'
        '<p>Math Guide defers to ZIP-32 (§“Elliptic curves”).</p>'
        '<p>Math Guide; the next section develops “The random oracle model”.</p>'
        '<p>See §“The random oracle model”.</p>'
        '<p>Crypto Guide, §“A title that does not exist”.</p>')
    linked = sitegen.link_references(source, 'crypto-guide', index)
    assert '../crypto-guide/S3.html#SS4-heading' in linked
    assert '../crypto-guide/S3.html#SS5-heading' in linked
    assert '../math-guide/S10.html#SS13-heading' in linked
    assert '../math-guide/S10.html#SS12-heading' in linked
    assert '../crypto-guide/S3.html#Thmtheorem1' in linked
    assert '../crypto-guide/S3.html#SS6-heading' in linked
    assert '>§Privacy-preserving membership via zero-knowledge paths</a>.' in linked
    assert '../math-guide/S10.html">§“Elliptic curves”</a>' not in linked
    assert 'href="https://zips.z.cash/zip-0032">ZIP-32</a> (§“Elliptic curves”)' in linked
    assert linked.count('href="../crypto-guide/S3.html#SS4-heading"') == 3
    for untouched in (
            '<a href="kept-section.html">§“The random oracle model”</a>',
            '<code>Crypto Guide, §“The random oracle model”</code>',
            'Crosslink Guide, §“The discrete logarithm problem”',
            '>ZIP 307</a>, §“The random oracle model”)',
            '§“A title that does not exist”'):
        assert untouched in linked, untouched
    assert re.sub(r'<a class="arb-crossref" href="[^"]+">(.*?)</a>',
                  r'\1', linked, flags=re.S) == source
    assert sitegen.link_references(linked, 'crypto-guide', index) == linked
    # A formula's hidden search copy is no citation, on any pass.
    hidden = '<p>ZIP 32 <math></math><span class="arb-idx" hidden> ZIP 2005 </span>.</p>'
    assert sitegen.link_references(hidden, 'crypto-guide', index).count('arb-crossref') == 1
    for tag in ('td', 'figcaption'):
        paragraphs = f'<{tag}><p>Math Guide.</p><p>“Elliptic curves” is a label.</p></{tag}>'
        result = sitegen.link_references(paragraphs, 'crypto-guide', index)
        assert result.count('class="arb-crossref"') == 1
        assert '<p>“Elliptic curves” is a label.</p>' in result
    entities = '<p>Math&#32;Guide, &#167;&ldquo;Elliptic curves&rdquo;.</p>'
    result = sitegen.link_references(entities, 'crypto-guide', index)
    assert result.count('class="arb-crossref"') == 2
    assert re.sub(r'<a class="arb-crossref" href="[^"]+">(.*?)</a>',
                  r'\1', result, flags=re.S) == entities
    complete = sitegen.link_references(source, 'complete', index, 'crypto-guide')
    assert '../complete/Pt2.html' in complete
    assert '../complete/V2.S3.html#SS4-heading' in complete
    assert '../complete/V1.S10.html#SS12-heading' in complete
    assert '../crypto-guide/' not in complete

    external = (
        '<p>protocol\nspecification, §“Shielded Pools and Notes” and '
        '§“Mainnet and Testnet”.</p>'
        '<p>Protocol specification, §“Computing '
        '<math alttext="\\rho"><mi>ρ</mi></math> values and Nullifiers”.</p>'
        '<p>protocol specification, §“Pseudo Random Functions” and '
        '§“Unknown section”.</p>'
        '<p>ZIP 229, Abstract and “Transaction Format”; '
        'protocol specification, §“Action Descriptions”.</p>'
        '<p>ZIP 244, “TxId Digest” and “txid_digest”.</p>'
        '<p>ZIP 229, §“Shielded Pools and Notes”.</p>'
        '<p>“Mainnet and Testnet” is just a title here.</p>'
        '<p><a href="kept">protocol specification</a>, '
        '<a href="kept-title">§“Mainnet and Testnet”</a>.</p>'
        '<p><code>protocol specification, §“Mainnet and Testnet”</code>.</p>')
    for edition, current in (('crypto-guide', None), ('complete', 'crypto-guide')):
        result = sitegen.link_references(external, edition, index, current)
        for destination in ('protocol/protocol.pdf#notes', 'protocol/protocol.pdf#networks',
                            'protocol/protocol.pdf#rhoandnullifiers',
                            'protocol/protocol.pdf#actiondesc', 'zip-0229#abstract',
                            'zip-0229#transactionformat', 'zip-0244#txid-digest',
                            'zip-0244#txid-digest-1'):
            assert f'href="https://zips.z.cash/{destination}"' in result, destination
        assert result.count('href="https://zips.z.cash/protocol/protocol.pdf#notes"') == 1
        assert result.count('href="https://zips.z.cash/protocol/protocol.pdf#networks"') == 1
        assert '>§“Pseudo Random Functions”</a>' not in result
        assert '>§“Unknown section”</a>' not in result
        assert '<a href="kept-title">§“Mainnet and Testnet”</a>' in result
        assert re.sub(r'<a class="arb-crossref" href="[^"]+">(.*?)</a>',
                      r'\1', result, flags=re.S) == external
        assert sitegen.link_references(result, edition, index, current) == result

        # Tokens inside an unquoted title must not become overlapping links
        # or change the context, including when that title is already linked.
        for number, title, anchor in (
                (229, 'Abstract', 'abstract'),
                (2005, 'Changes to the Protocol Specification',
                 'changestotheprotocolspecification'),
                (258, 'ZIP 2005 activation', 'zip2005activation')):
            unquoted = f'<p>ZIP {number}, §{title}; Abstract.</p>'
            url = f'https://zips.z.cash/zip-{number:04}'
            expected = (f'<p><a class="arb-crossref" href="{url}">ZIP {number}</a>, '
                        f'<a class="arb-crossref" href="{url}#{anchor}">§{title}</a>; '
                        f'<a class="arb-crossref" href="{url}#abstract">Abstract</a>.</p>')
            result = sitegen.link_references(unquoted, edition, index, current)
            assert result == expected, result
            assert sitegen.link_references(result, edition, index, current) == result

    assert sitegen.reference_key('Fiat–Shamir: \u00a0𝑗') == sitegen.reference_key('Fiat--Shamir: j')
    for name in ('S4.html', 'S5.html'):
        (out / 'crypto-guide' / name).write_text(
            '<h1 class="ltx_title_section">Repeated title</h1>')
    ambiguous = sitegen.reference_index(out)
    assert ambiguous[1]['standalone', 'cryptoguide']['repeatedtitle'] is None
    assert 'href="../crypto-guide/S4.html"' not in sitegen.link_references(
        '<p>Crypto Guide, §“Repeated title”.</p>', 'math-guide', ambiguous)


with tempfile.TemporaryDirectory() as tmp:
    out = Path(tmp)
    sitegen.landing(out)
    sitegen.concordance(out)
    for name in ("index.html", "concordance.html"):
        html = (out / name).read_text()
        assert html.index(sitegen.THEME_INIT) < html.index("arboretum.css")
        assert html.count('class="arb-theme"') == 1
        assert html.count(sitegen.PAGE_SCRIPT) == 1
        assert '<html lang="en-GB">' in html
        assert '<link rel="icon" href="favicon.svg"' in html
    assert "warm: 'light'" in sitegen.THEME_INIT and "midnight: 'dark'" in sitegen.THEME_INIT

    landing = (out / "index.html").read_text()
    concordance = (out / "concordance.html").read_text()
    assert landing.count("showImages: false") == 1
    assert landing.count(sitegen.SEARCH_OPTIONS) == 1
    assert "sort: { 'reading-order': 'asc' }" in landing
    assert "details.arb-search" not in landing
    assert "ZIP 316" in concordance
    assert "<table></table>" not in concordance
    assert "<h2>Protocol specification</h2>" in concordance
    assert "&sect; 4.2.3" in concordance
    for vol in PARKED + MERGED:
        assert f'href="{vol}/"' not in landing
        assert f'href="{vol}/"' not in concordance
    assert landing.count('href="complete/"') == 1  # the title; no separate Web link
    assert '>Web</a>' not in landing
    assert '<span class="acc">I</span>' in landing
    assert f'<span class="acc">I–{sitegen.ROMANS[len(sitegen.VOLUMES) - 1]}</span>' in landing
    assert 'arb-colophon' not in landing
    assert landing.count('href="pdf/arboretum-complete.pdf"') == 1
    assert "frontier designs" not in landing
    assert landing.index('<h2 class="grp">Frontier</h2>') < landing.index(
        '<h2 class="grp whole">Complete edition</h2>')
    assert landing.count('<p class="gloss">') == 3
    assert 'aria-label="Math Guide, PDF"' in landing
    assert (out / "pdf" / "arboretum-complete.pdf").is_file()

    omnibus = out / "arboretum-complete.tex"
    sitegen.omnibus(out=omnibus)
    complete_tex = omnibus.read_text()
    assert complete_tex.split(r"\begin{document}")[1].count(r"\tableofcontents") == 1
    native_section_id = (
        r"\def\thesection@ID{V\arabic{arbvolume}.S\@section@ID}")
    assert native_section_id not in complete_tex
    assert sitegen.OMNIBUS_INTRO in complete_tex
    # the design block, head rule and section marks included, precedes the contents
    assert ("\\renewcommand{\\headrulewidth}{0pt}"
            in complete_tex.split(r"\begin{document}")[0])
    assert r"\headheight}{" not in complete_tex
    # deduplication keeps the design block whole, its repeated lines included
    first = (sitegen.ROOT / f"{sitegen.VOLUMES[0]}.tex").read_text()
    assert sitegen.DESIGN_BLOCK_RE.search(first).group(0) in complete_tex
    assert complete_tex.count("\\stepcounter{arbvolume}") == len(
        sitegen.VOLUMES)
    assert "\\part*{How Halo 2 Proves:" not in complete_tex
    assert "\\section{The verifier's decision and its implication chain}" in complete_tex
    for title in ("PQ Guide", "Tachyon Guide", "Voting Guide", "Crosslink Guide",
                  "Sync Guide"):
        assert f"\\part{{{title}:" not in complete_tex
    assert complete_tex.count(r"\part{Wallet Guide:") == 1
    for label in WALLET_CHAPTERS:
        assert complete_tex.count(r"\label{wallet:" + label + "}") == 1
    # each part sets its own numeral and running-head name; the edition has none
    ironwood = complete_tex.split(r"\part{Ironwood Guide:")[1].split(r"\part{")[0]
    assert "\\def\\accession{V}" in ironwood
    assert "\\def\\arbvolname{Ironwood Guide}" in ironwood
    edition = complete_tex.split(r"\begin{document}")[0]
    assert "\\renewcommand{\\accession}" not in edition
    assert edition.count("\\makeatletter") == edition.count("\\makeatother")

    webdir = out / "web"
    webdir.mkdir()
    with patch.object(sitegen, "WEBDIR", webdir):
        sitegen.webprep()
    for volume in (*sitegen.VOLUMES, "arboretum-complete"):
        prepared = (webdir / f"{volume}.tex").read_text()
        assert r"\mdfsetup" not in prepared, volume
        # LaTeXML has neither fontspec nor the PDF design packages
        for pdf_only in (r"\setmainfont", r"\setmathfont", "polyglossia",
                         "unicode-math", "framed", "titlesec", r"\patchcmd"):
            assert pdf_only not in prepared.split(r"\begin{document}")[0], (volume, pdf_only)
        assert r"\providecommand{\accession}{}" in prepared, volume
    assert "Statistical distance" in (webdir / "math-guide.tex").read_text()
    assert "FF1" in (webdir / "crypto-guide.tex").read_text()
    web_wallet = (webdir / "wallet-guide.tex").read_text()
    assert not (webdir / "sync-guide.tex").exists()
    assert web_wallet.count(r"\tableofcontents") == 1
    for label in WALLET_CHAPTERS:
        assert web_wallet.count(r"\label{" + label + "}") == 1
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
        '<html lang="en"><head><title>1 Notation ‣ Math Guide Foundations</title>'
        '<link rel="stylesheet" href="_site/math-guide/arboretum.css"></head>'
        '<body><nav class="ltx_page_navbar"><a href="./" title="" class="ltx_ref" rel="start">'
        '<span class="ltx_text ltx_ref_title"><span class="ltx_text ltx_font_bold">Math Guide'
        '<span class="ltx_text"> </span></span>Foundations</span></a></nav>'
        '<main class="ltx_page_content">'
        '<nav class="ltx_TOC ltx_list_toc ltx_toc_toc">Contents</nav>'
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
        '</p><p>Done.\n∎</p></div>'
        '<p>Then <math display="inline" alttext="a=b"><mi>a</mi><mo>=</mo><mi>b</mi></math> '
        'and <img src="build/web/figures/math-guide-fig1.png"></p></main>'
        '<footer class="ltx_page_footer"><div class="ltx_page_logo">Generated on today by '
        '<a class="ltx_LaTeXML_logo">LaTeXML</a></div></footer></body></html>')
    reading_order = [page, page.parent / "S1.html", page.parent / "S2.html",
                     page.parent / "S10.html", out / "crypto-guide" / "index.html",
                     out / "crypto-guide" / "S1.html",
                     out / "frost-guide" / "S1.html"]
    for sibling in reversed(reading_order[1:]):
        sibling.parent.mkdir(exist_ok=True)
        sibling.write_text(page.read_text())
    for sibling in reading_order:  # LaTeXML copies a volume's figures there
        (sibling.parent / "build/web/figures").mkdir(parents=True, exist_ok=True)
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
            '<nav class="ltx_TOC ltx_list_toc ltx_toc_toc">Contents</nav>'
            '<section id="SS1"><h2>A complete subsection</h2></section></main>'
            '<footer><div></div></footer></body></html>')

    with patch.object(sitegen.subprocess, "run", side_effect=build_complete):
        sitegen.postprocess(out)
    html = page.read_text()
    assert html.index(sitegen.THEME_INIT) < html.index("arboretum.css")
    assert html.count('class="arb-theme"') == 1  # the bar's
    assert html.count("showImages: false") == 1
    assert html.count(sitegen.SEARCH_OPTIONS) == 1
    assert "search.querySelector('summary').addEventListener('click'" in html
    assert "search.open = !search.open" in html
    assert "search.querySelector('.pagefind-ui__search-input').focus()" in html
    assert html.count('data-pagefind-meta="volume:I Math Guide"') == 1
    assert '<a class="volname" href="./#arb-contents"' in html
    assert html.count('id="arb-contents"') == 1
    for index, sibling in enumerate(reading_order, 1):
        assert sibling.read_text().count(
            f'data-pagefind-sort="reading-order:{index}"') == 1, sibling
    assert '<section id="SS1"><h2 class="ltx_title" id="SS1-heading">' in html
    assert 'data-pagefind-meta="heading-SS2-heading:Squared x^(2)"' in html
    assert "if (!e.composedPath().includes(search)) search.open = false" in html
    assert "e.button === 0 && !e.ctrlKey && !e.metaKey && !e.shiftKey && !e.altKey" in html
    assert "e.target.closest('.arb-search a.pagefind-ui__result-link')" in html
    assert "e.key === 'Escape' && search.open" in html
    assert '<body data-arb="vol">' in html
    assert "MathJax" not in html
    for script in (sitegen.TOC_SCRIPT, sitegen.PAGE_SCRIPT, sitegen.TRIM_SCRIPT):
        assert html.count(script) == 1
    assert 'href="../arboretum.css?v=' in html
    assert 'href="_site/math-guide/arboretum.css"' not in html
    assert '<html lang="en-GB">' in html
    assert '<title>1 Notation — I Math Guide</title>' in html
    assert '<link rel="icon" href="../favicon.svg"' in html
    assert '<p class="arb-nav-tools"><a href="../pdf/math-guide.pdf">PDF</a></p>' in html
    assert ('<a href="./" class="ltx_ref arb-start" rel="start"><span class="arb-acc">I</span> '
            'Math Guide<span class="arb-start-sub">Foundations</span></a>') in html
    assert "Generated" not in html
    assert 'arb-colophon' not in html and html.count('class="arb-feedback"') == 1
    assert '<mo>=</mo></math><wbr><math' in html
    assert '<span class="arb-idx" hidden> a = b </span>' in html
    assert 'src="build/web/figures/math-guide-fig1.svg"' in html
    assert (page.parent / "build/web/figures/math-guide-fig1.svg").is_file()
    assert ('<a class="ltx_ref" href="#Thmtheorem0">prior result</a>).'
            '<a class="arb-permalink" data-pagefind-ignore href="#Thmtheorem1" '
            'aria-label="Permalink to this item" '
            'title="Permalink">#</a></h6>') in html
    assert html.count('class="arb-permalink"') == 1
    assert re.search(r'<span class="arb-proof-end"><span class="arb-nobr"><math [^>]*'
                     r'alttext="x=1"[^>]*><mi>x</mi></math><span class="arb-idx" hidden> x '
                     r'</span>\.</span></span> <span class="arb-qed">□</span>', html)
    assert html.count('class="arb-proof-end"') == 1
    assert html.count('class="arb-qed"') == 2
    complete_html = complete_page.read_text()
    assert '<body data-pagefind-ignore data-arb="vol">' in complete_html
    assert '../pdf/arboretum-complete.pdf' in complete_html
    assert 'The Complete Arboretum' in complete_html
    assert '<section id="SS1"><h2 id="SS1-heading">' in complete_html
    assert 'data-pagefind-meta="volume:' not in complete_html
    assert 'data-pagefind-sort=' not in complete_html
    assert complete_html.count(sitegen.TOC_SCRIPT) == 1
    assert complete_html.count('id="arb-contents"') == 1
    assert (f'<span class="arb-acc">I–{sitegen.ROMANS[len(sitegen.VOLUMES) - 1]}</span><span'
            '\nclass="arb-volname"> The Complete Arboretum</span>') in complete_html

    # A second finishing pass must not duplicate controls, scripts or IDs.
    sitegen.postprocess(out)
    assert page.read_text() == html
    assert complete_page.read_text() == complete_html
    # Adding an earlier page updates existing sort keys without duplicates.
    earlier = page.parent / "S0.html"
    earlier.write_text(html)
    sitegen.postprocess(out)
    for index, sibling in enumerate(reading_order[1:], 3):
        assert sibling.read_text().count(
            f'data-pagefind-sort="reading-order:{index}"') == 1, sibling
    earlier.unlink()
    sitegen.postprocess(out)

    # Previously finished HTML needs heading anchors and metadata too, without
    # duplicating existing controls, theorem links or formatting.
    page.write_text(html.replace(' id="SS1-heading"', '').replace(
        ' data-pagefind-meta="volume:I Math Guide"', '').replace(
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
# Every face the stylesheet names ships with its licence; the MathJax assets are gone.
fonts = sitegen.ROOT / "site" / "fonts"
faces = re.findall(r'url\("fonts/([^"]+)"\)', css)
assert {"eb-garamond-regular.woff2", "garamond-math.woff2", "iosevka.woff2"} <= set(faces)
assert all((fonts / face).is_file() for face in faces)
assert {path.name for path in fonts.glob("*.woff2")} == set(faces)
for licence in ("EBGaramond-OFL.txt", "Garamond-Math-OFL.txt", "Iosevka-OFL.txt"):
    assert (fonts / licence).is_file()
assert (sitegen.ROOT / "site" / "favicon.svg").is_file()
assert not (sitegen.ROOT / "site" / "mathjax-4.1.3").exists()
assert '--text: "EB Garamond"' in css
assert 'math { font-family: var(--math); font-feature-settings: "ss03"; }' in css
assert ':root[data-theme="dark"]' in css and 'warm' not in css and 'midnight' not in css
assert '.ltx_theorem .arb-permalink {' in css
search_panel = css.split('.arb-bar .arb-search-panel {', 1)[1].split('}', 1)[0]
assert 'max-height: calc(100dvh' in search_panel
assert 'overflow-y: auto' in search_panel
assert 'overscroll-behavior-y: contain' in search_panel
print("site generator checks passed")
