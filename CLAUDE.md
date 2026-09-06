# Working on the Zcash Arboretum

This repository contains eleven LaTeX volumes and a companion Beamer talk,
plus the static-site and verification tools that publish them. It is
non-normative documentation, not a Zcash validator implementation.

Read `README.org` for the scope and reading order and `CONVENTIONS.org` for
the binding notation, first-use and style rules before changing prose.

## Editorial acceptance

Every technical term is explained before first use. A later glossary,
forward reference or presumed specialist background does not repair a missing
prerequisite. Construct standard mathematics once in its lowest required
volume; cite the exact named section when applying it above.

Retain only the critical path to the selected endpoints. Core payment
volumes do not depend on frontier volumes. Earlier shielded and transparent
formats appear only at necessary compatibility boundaries. Do not add
historical surveys or unused alternatives.

Distinguish a mathematical identity, a proved reduction, a computational
assumption, an imported theorem and an unresolved interface. In particular,
binding is not extraction, marginal hiding is not joint simulation, a hash
of metadata is not validation of its arithmetic, and an implementation pin
is not evidence of network activation.

Verify protocol claims firsthand against the relevant primary sources.
The local source collection is `/home/m/zcash`; upstream repositories there
are reference material, not part of this project's write scope. Record source
revisions and distinguish later published specifications from older local
pins. Independently compute examples, review changed arguments adversarially,
and check their actual consumers before integrating substantive changes.

## Source and design conventions

British prose wraps at 80 columns. Follow the notation and label registry
in `CONVENTIONS.org`. Cross-volume references use the italic guide name and
exact section title, never a cross-document `\ref`. A forward reference within
one volume may navigate already introduced concepts, not introduce an
unexplained prerequisite.

Preserve the shared STIX Two font, theorem bars, colours and running headers.
The web preparation code strips those design blocks by exact pattern; a
preamble change must update the matching logic and regression check together.
Other packages and local macros need not be identical across volumes.

The title shape is parsed by the site:
`\title{\textbf{\Huge Name}\\[6pt]\large Subtitle}`.
The author line is `\author{m@rek.onl}` and is removed from web editions.
Talks use Beamer with `aspectratio=169`.

## Verification

```sh
python3 -B site/tools/test_sitegen.py
python3 -B research/check_foundations.py
python3 -B research/check_mathcrypto.py
python3 -B research/check_halo2.py
python3 -B research/check_wallet_crypto.py
python3 -B research/check_deployed.py
python3 -B research/check_frontier.py
python3 -B site/tools/check_build.py
```

The PDF gate builds the eleven volumes, every retained talk and the generated
complete edition. It rejects overfull boxes, unresolved references, duplicate
labels/destinations, missing glyphs and compilation failures. Logs and PDFs
remain in `build/pdf/`. `--update-pdfs` copies passing PDFs beside their
sources only after every document passes. PDFs are deliberately tracked;
update them with their sources.

To compile one document:
`tectonic -Z shell-escape <source>.tex`.
The flag preserves compatibility with the shared figure tooling.

A clean build is not proof of the prose. A changed mathematical claim needs
an independent argument review; a changed concrete algorithm needs a
runnable example or primary-vector check. Keep the smallest useful check
rather than adding a test framework.

## Site

`site/tools/sitegen.py` owns the roster and reading order in `VOLUME_META`.
Its modes are:

- `volumes`: print the eleven publication names.
- `render`: render any source TikZ figures to SVG and PNG in `site/figures/`.
- `webprep`: prepare `build/web/` for LaTeXML.
- `omnibus`: regenerate `arboretum-complete.tex`; do not hand-edit that file.
- `landing`, `concordance`, `postprocess`: finish the generated website.

When adding or changing a figure, run `render` and retain the generated assets
with its source. No obsolete figure is kept merely because it was once used.
Keep the compatible font/design processing and browser controls shared across
volumes; fix a shared defect at its common implementation.

The website workflow converts sources to per-section HTML, builds Pagefind
search and runs `site/tools/check_site.py` for local links, anchors and error
markup. Check actual rendered mathematics and navigation after structural
changes. Against a locally served generated site:

```sh
uv run --with playwright python -B site/tools/check_search.py BASE_URL
```

The optional second argument selects `firefox` or `webkit`; those engines
need their Playwright binaries and runtime libraries. The check exercises
search reachability at phone, tablet and desktop sizes; emulation does not
certify every physical device or untested input method.

## Workspace boundaries

`research/` contains executable checks and current verification evidence.
Ignored `.wip/` and `build/` hold working drafts, temporary primary-source
material and generated output. Preserve unrelated user changes and backups.
Do not commit, push, publish or edit upstream repositories unless requested.
