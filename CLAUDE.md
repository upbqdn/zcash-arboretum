# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

The Zcash Arboretum: a series of standalone LaTeX volumes documenting the Zcash
protocol (non-normative — the protocol spec and ZIPs are authoritative), plus a
static website generated from those sources, plus a research/audit sidecar.
There is no application code; the "build" is LaTeX compilation and site
generation.

`README.org` owns the volume roster and reading order. `CONVENTIONS.org` is the
binding style/notation contract for all volumes — read it before writing volume
prose; deviations from it are bugs.

## Building

Each volume compiles independently. The `-Z shell-escape` flag is required (TikZ
externalisation); without it the build fails.

```sh
tectonic -Z shell-escape <volume>.tex
```

CI (`.github/workflows/build.yml`) compiles every `*-guide.tex` on push and PR.
Compiled PDFs are committed deliberately (`.gitignore` keeps `*.aux`/`*.log`/…
out but not `*.pdf`) — recompile and commit the PDF alongside any source change.

**The pre-commit gate (from CONVENTIONS.org):** a volume must compile with **zero
overfull hboxes and zero unresolved references** before commit. `??` in output or
an "Overfull \hbox" warning is a failure, not a nuisance. Diagnose overfull boxes
with `--keep-logs` and fix with `\allowbreak` on long identifiers/paths, or by
converting inline math to `gather*`/`align*` displays.

Talk decks live in `talks/` (Beamer, `aspectratio=169`); same `tectonic`
invocation.

## The shared-preamble contract

Every volume opens with the same ~86-line preamble (theorem environments, the
`\F`/`\Z`/`\NoteCommit`/key-hierarchy macros, the four `tier*` figure colours,
the redefined `abstract` environment). Copy it byte-for-byte from an existing
volume (e.g. `sync-guide.tex:1-86`) when creating a new one — the notation
registry in `CONVENTIONS.org` is fixed across volumes and must not be
re-derived locally.

Two preamble lines are parsed by tooling and must match exactly:

- `\author{m@rek.onl}` — `sitegen.py` webprep strips this literal string for the
  web build. A different author line silently breaks web rendering.
- The title, which **must** fit the regex in `sitegen.py:vol_title`:
  `\title{\textbf{\Huge <Name>}\\[6pt]\large <subtitle>}`. The landing page and
  per-volume nav bar extract name + subtitle from this shape; a differently
  formatted title falls back to the filename.

## Site generation (`site/tools/sitegen.py`)

The website is built by `sitegen.py` and published by
`.github/workflows/site.yml` (LaTeXML → per-section HTML → Pagefind search →
GitHub Pages). Modes:

- `render` — pre-renders every `tikzpicture` to SVG **and** PNG under
  `site/figures/`. **Run locally and commit the outputs** (needs `tectonic` +
  `pdftocairo`/`pdftoppm`); CI does not render. LaTeXML can't ingest TikZ, so it
  consumes these images.
- `webprep` — CI-side; rewrites each volume into `build/web/` with figures
  swapped for `\includegraphics` and TikZ stripped.
- `landing` / `concordance` / `postprocess` — generate the index page, the
  ZIP↔section concordance (scanned from the sources), and inject the site bar.

`VOLUME_META` in `sitegen.py` is the site registry: `(volume, group, chip)`
tuples in reading order, where group ∈ {Foundations, Deployed protocol,
Frontier} and chip is the status badge. `VOLUMES` and the roman-numeral
accession numbers derive from it.

### Adding a new volume

1. Create `<name>-guide.tex` with the byte-identical shared preamble and a
   title matching the regex above.
2. Append a `(<name>-guide, <group>, <chip>)` tuple to `VOLUME_META` at the
   correct reading position.
3. Extend `ROMANS` in `sitegen.py` if the count now exceeds the list.
4. Add the volume to the `README.org` roster.
5. If it has figures, run `python3 site/tools/sitegen.py render` and commit the
   new `site/figures/*.svg` + `*.png`.
6. Compile clean (zero overfull, zero unresolved refs) and commit the PDF.

Cross-volume citations are by *italic volume name and section title* only —
PDFs are separate documents, so there is **no** cross-document `\ref`. A volume
may forward-reference only its own later sections, never a volume above it in
the layering.

## Conventions that bite

- **Prose wraps at 80 columns** in `.tex` sources (not 100 — that 100-col rule
  is for Rust elsewhere). British spelling ("synchronisation", "colour").
- Never start a sentence with a bare symbol or code identifier; lead with its
  kind ("The trapdoor `\rcv` …", "Function `foo()` …").
- Label prefixes: `sec:`, `def:`, `thm:`, `lem:`, `eq:`, `fig:`, `tab:`, `rem:`.
  Theorem environments number within sections.
- Every relied-upon quantity is constructed in place or cited to the exact
  volume+section that constructs it ("derived from X" with no formula is a
  defect — the "psi rule").
- Deployed-behaviour claims cite the implementation (crate + file) and spec
  section; design-stage claims are classified *specified* /
  *designed-but-unspecified* / *open problem*.

## Verification method

Ground truth lives under `~/zcash`: `protocol/protocol.tex`, the ZIPs, and the
deployed sources (librustzcash, orchard, zebra, wallet SDKs). Verify claims
firsthand against these before writing; record commit hashes for design-stage
sources. Worked-example numbers are computed by script (the script's output is
the source of the numbers in the text), never by hand. Substantial additions
pass an adversarial review — independent recomputation of numbers, a
concept-inversion hunt, and a cross-reference check — before merging.

## Non-source directories

- `research/` — committed audit and design notes (`upstream-defects.md`,
  `correctness-audit.md`, `tachyon.md`, …). Findings about upstream bugs stay in
  draft until confirmed firsthand.
- `.wip/` — gitignored working drafts and staged source papers, grouped per
  volume.
- `build/` — gitignored generated web sources.
