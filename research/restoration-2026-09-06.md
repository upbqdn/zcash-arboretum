# Restore the full-depth edition and repair search

The user rejected the replacement rewrite and authorised restoration if a
better complete replacement could not be established. We took that fallback;
this is not a second wholesale rewrite.

## Restored baseline

The source is the audited pre-rewrite working-tree archive, not merely Git
commit `e7349f8`. The archive preserves the earlier uncommitted corrections:

`/home/m/arboretum-before-rewrite.uRD9Cw/project.tar.gz`

SHA-256: `787b2b3a8de43e33de1bc3134f7e0569767a69f5976f03c3b4fa393cb89c8e62`.

The eleven volumes, original talk, research notes, figures and project
instructions are restored. The three parked guides remain outside the
published roster. The original numerical checks and their matching build
workflow are restored too. The omnibus introduction and specification
concordance again match the original edition.

The rejected rewrite remains recoverable in Git and in
`/home/m/arboretum-rejected-rewrite.I0dUbk/project.tar.gz`. Its three additional
numerical checkers and verification report are archived in that directory's
`research/` subdirectory; they are not evidence for the restored corpus.

## Deliberate differences

- Math defines subfields, extension fields and embeddings before their first
  use, with an explained example. The original symbol and Greek pronunciation
  tables are retained. The new definition received independent review.
- Conventions explicitly retain those reading aids, require explanations
  before first use, and prohibit length targets that remove needed teaching.
- Two pre-existing trailing spaces were removed from Crypto and one from
  the upstream-defects notes; their prose is otherwise unchanged.
- Search no longer displays automatically selected image thumbnails, which
  had been LaTeXML's footer mascot. An outside click or tap closes the popup;
  Escape closes it and returns focus when appropriate. Internal controls and
  the inline landing-page search retain their behaviour.
- Shared search scrolling, volume-qualified HTML IDs, PDF header sizing and
  compatible site/build fixes remain. No dependency was added.

## Verification

The restored three numerical checks, generator regression and final strict
PDF gate passed. The gate built all 16 documents. Independent extracted-text
comparison found no changes in the 14 unaffected individual PDFs; the
complete edition's original introduction and reading paths are restored.

All twelve local HTML conversions completed successfully with the normal
maths parser, using the existing isolated local LaTeXML compatibility shims.
The generated site has 198 HTML pages and 97 indexed standalone pages. Its
link/ID/asset gate passes, and all twelve downloadable PDFs match the final
root PDFs. Rendered notation and the extension-field introduction were
checked at phone and desktop widths. Logs remain in
`build/restoration-2026-09-06/`.

The fresh site passed search interaction checks in Chromium and Firefox at
seven viewport sizes, from 320 × 568 to 1920 × 1080, including a short tablet
viewport. Checks cover thumbnail removal, internal controls, scrolling,
load-more, outside mouse/touch dismissal, Escape focus return, reopening,
inline landing search and result navigation. Chromium used native touch
swipes; Firefox used wheel scrolling. Safari/WebKit was not available.

These checks do not certify every mathematical statement or physical device.
The restoration preserves the original exposition; it is not a new claim of
whole-protocol correctness or a guarantee that no editorial gaps remain.

## Subsequent removal

At the user's request, the added subfields/extensions definition, example
and embedding explanation were removed, and the original wording "finite
extensions" restored. The Math source now matches the pre-rewrite archive
exactly. The addition's mathematical review had not established coherent
editorial integration with the surrounding and later passages. UI fixes
and the other differences recorded above remain.
