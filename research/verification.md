# Rewrite verification — 6 September 2026

This record covers the newly written eleven guides and the companion talk,
not the earlier edition's audit. It is evidence of review and testing, not a
guarantee that every sentence is error-free.

## Scope

The core path is mathematics → cryptography → Halo 2 → ledger rules →
shielded payments → wallet construction → synchronisation and recovery.
FlyClient, ZSA, Crosslink and FROST remain independent optional endpoints.
Core volumes do not depend on them.

The talk has 27 slides, including its title. It follows one payment and keeps
the checked four-row proof example. Cryptographic constants, byte layouts,
detailed seed derivations, transaction-version surveys, frontier protocols and
implementation instructions are excluded from the talk. Complete necessary
constructions remain in the books.

The first-use rule is explicit in CONVENTIONS.org and CLAUDE.md: a technical
term needs an earlier explanation, not a later glossary or forward reference.
Math now constructs the binary polynomial field, its inclusion of F₂, and
the meaning of extension and degree before Crypto uses it for AES.

## Three review passes

1. **Construction and primary-source pass.** Each author rewrote the entire
   assigned body against its actual consumers and pinned protocol sources.
   Identities, reductions, assumptions, imported theorems and unresolved
   interfaces were distinguished rather than conflated.
2. **Independent full-text pass.** A second reader reviewed every guide:
   Math by the frontier reviewer; Crypto, core and frontier by the root
   reviewer; Halo by the core reviewer. Crypto's wallet constructions also
   received a separate source/vector review. The talk received independent
   scope and prerequisite review. Findings were corrected and reread.
3. **Post-fix consistency and executable pass.** The integrated edition was
   checked for prerequisite order, concrete arithmetic, source constants,
   document integrity, PDF rendering and generated-site behaviour.
   All 161 explicit named cross-volume section references resolve to exact
   titles in earlier volumes. Two semantically misplaced ZSA citations and
   unexplained Poseidon “width/rate” wording were corrected. The final
   opening-text review also removed unexplained previews from the Math and
   Crypto abstracts and made Math's first notation introductions explicit.

These are three different review lenses, not three formal proofs or three
claims of exhaustive machine verification. Concrete corrections included the
BLAKE2b round-three permutation transcription, finite-field cyclicity and
probability hypotheses, signature-game first use, and the distinction between
binding, extraction and joint simulation.

## Runnable checks

From the repository root, without Python's `-O` option:

```sh
python3 -B research/check_foundations.py
python3 -B research/check_mathcrypto.py
python3 -B research/check_halo2.py
python3 -B research/check_wallet_crypto.py
python3 -B research/check_deployed.py
python3 -B research/check_frontier.py
python3 -B site/tools/test_sitegen.py
python3 -B site/tools/check_build.py
```

All six numerical checkers and the site-tool regression pass. Coverage includes:

- The identical F₉₇ circuit, interpolated columns, quotient and deliberately
  broken row in the Halo guide and talk; 2,016 exact extractor cases.
- Finite-field, mask, transform, curve, decoding and AES byte-field examples.
  All 192 Poseidon round constants and nine matrix entries; both Pasta
  isogeny identities and primary hash-to-curve vectors. An independent
  comparison also checked all 26 printed isogeny coefficients and eleven
  primary Poseidon hash vectors.
- Explicit SHA-256/BLAKE2b computations against standard-library outputs at
  block/padding boundaries; RFC ChaCha20, Poly1305 and composed tag vectors.
- AES-256, the pinned Orchard FF1 vector, short and maximum-length F4Jumble
  vectors, all seven valid/fourteen invalid generic BIP350 vectors, padding
  failures, and two complete Unified Address vectors.
- Eighteen formal-generator asymmetric masked IPA traces; 6,016 honest and
  altered multi-opening cases; lookup arithmetic, degree/chunk counts and
  row-mask rank.
- Payment arithmetic, key derivation vectors, byte lengths, compact
  integers, target/difficulty calculations, the stated confirmation model,
  history-tree positions, and every append/root/path transition of a
  32-leaf toy tree with rollback.
- Twelve frontier checks covering sampling, threshold signing and sharing,
  asset accounting, checkpoint transitions and conditional prefix safety.

The toy trees and circuit do not generate a production Zcash transaction.
The readable Python cryptographic routines are verification aids, not
constant-time production implementations.

## PDF and website gates

`python3 -B site/tools/check_build.py --update-pdfs` passed all thirteen
documents. Only after that complete success were the PDFs copied beside
their sources. The gate rejects compilation failures, overfull boxes,
unresolved references, duplicate labels/destinations and missing glyphs.
The complete edition has 170 pages; the talk has 27.

An unused `bm` package caused a combined-document Unicode mathematics
conflict and was removed. The omnibus header height and short framed
statements were corrected without changing their mathematical content.
Inherited Unicode-math/STIX font-substitution notices are not described as
warning-free builds.

The final site has 176 HTML pages, including 88 in the complete edition.
All pass the local link, asset, anchor, duplicate-ID and conversion-error
checks. Pagefind indexes the 86 standalone guide pages without duplicating
the complete edition. All twelve site PDF downloads match the final root
PDFs byte-for-byte.

Web preparation now removes the PDF-only nonbreaking-frame settings.
The complete edition uses volume-prefixed native LaTeXML section IDs,
preserving printed numbering while preventing collisions in section,
theorem, equation and list links. The change was first checked on a
two-part fixture, then on the complete site. The obsolete empty
protocol-section concordance was removed; the generated ZIP index remains.

The first exhaustive browser run found a missing dynamically loaded
MathJax asset in Halo's bold-vector notation. The existing vendored
MathJax 4.1.1 installation now includes its matching
[boldsymbol extension](https://docs.mathjax.org/en/latest/input/tex/extensions/boldsymbol.html),
copied from the
[pinned distribution](https://cdn.jsdelivr.net/npm/mathjax@4.1.1/input/tex/extensions/boldsymbol.js).
A regression checks its version and inclusion in generated assets.

The final fresh Chromium run passed **352 of 352 page/width checks**:
all 176 pages at widths 390 and 1440. It awaited mathematics and fonts,
checked all five theme choices, and found no page overflow, unrendered
mathematics, mathematics error nodes, broken images or runtime/network
errors. It rendered 15,972 mathematical instances across those checks.
Selected dense mathematics and the newly explained field-extension
paragraph also received visual inspection at both widths.

LaTeXML retains fifteen math-parser warnings across five standalone books,
mirrored in the complete edition. The original TeX is retained for MathJax;
the final browser run rendered these regions without errors. The local
converter used isolated process-teardown workarounds for its installed
ImageMagick integration; these are diagnostic-environment workarounds,
not additions to the published site or CI workflow. No system packages
were changed.

### Search scrolling

The old tablet popup extended below the viewport and had no internal
scroll area. Five lines of shared CSS now bound its height using the
viewport, enable native vertical scrolling and contain overscroll.

The final generated site passes `site/tools/check_search.py` in Chromium
and Firefox at 320×568, 390×844, 768×1024, 1024×768, 1440×900, 1920×1080
and 768×450. Every case checks visible bounds, internal scrolling,
background stability, last-control reachability and loading more results.
Chromium additionally checks touch gestures and bottom-edge containment.

Firefox's wheel tests are not certification of real touch containment;
its synthetic boundary-wheel behaviour differed even in an isolated native
overflow fixture. WebKit could not launch because required runtime libraries
were absent. Safari/iPad and every physical device are therefore **not**
claimed tested. The fix is shared, not conditional on a tablet model.

Detailed generated logs and screenshots remain under
`build/clean-rewrite/`; the final browser log is
`browser-final-output.jsonl`. The reusable numerical, PDF, site and search
checks remain in `research/` and `site/tools/`.

## Source baselines and limits

The books cite the primary constructions at their points of use. Important
local pins include `zips` `69610984109078075e7e64989ecf89d63a259b97`,
`halo2` `261faaccd5a30c19bb8468600841a0dac305adf5`,
`frost` `2016e44ba4a4757a996300350063b937a2ad33e8`,
and the Crosslink formal construction at
`fe6e1d6f403f62da46c64e8f5a7db3cb188ffae2`.
Vector provenance is embedded in the checkers. A source revision, package
release or specified upgrade does not establish network activation.

Elementary arguments were reviewed, not mechanically formalised. Hardness
assumptions, elliptic-curve associativity/order facts, and imported complete
proof-system security results remain explicit boundaries. The frontier
books do not claim resolved ZSA wire interfaces, a full concrete FlyClient
integration theorem, equivalence of formal and concrete Crosslink, or a
complete DKG/signing/wallet composition theorem.

This record captures the pre-publication checks. Publication is a separate
user-authorised step, tracked by the repository's deployment workflow.
The referenced upstream protocol repositories were not modified.

## Recovery

The complete pre-rewrite working-tree snapshot is
`/home/m/arboretum-before-rewrite.uRD9Cw/project.tar.gz`.

SHA-256:
`787b2b3a8de43e33de1bc3134f7e0569767a69f5976f03c3b4fa393cb89c8e62`.

The excluded PQ/Tachyon/Voting documents, obsolete research notes and old
figure assets were moved outside the project into the same backup
directory's `retired/` tree. They remain recoverable. Unrelated user files
and existing edits were preserved.
