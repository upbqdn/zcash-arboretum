# Foundation audit, 5–6 September 2026

Scope: `math-guide.tex`, `crypto-guide.tex`, `halo2-guide.tex`, and the new
dependency-free `research/check_foundations.py`. Baseline project HEAD:
`e7349f853a9d70655be811f96eaaeb3874d05a18`. Other agents owned the other
volumes, site, talk, and final project builds. Existing user changes were
preserved. Ponytail guided the implementation towards small corrections and
standard-library checks, without adding dependencies or redesigning the books.

## What the three passes mean

These were three different review lenses, **not three independent line-by-line
formal verifications**. The first pass read every source line. Later passes
combined full-corpus structural/dependency checks with focused mathematical
rereading, primary-source comparison, executable regressions, and independent
review. A successful audit cannot certify that no errors remain.

| Pass | Actual coverage and result |
| --- | --- |
| 1 — mathematical and semantic reading | Read all 10,687 initial Math lines, 4,251 Crypto lines, and 2,361 Halo lines, in chunks, filling truncated-output gaps: 17,299 source lines in total. Reviewed definitions, assumptions, proof steps, examples, and explanatory claims. Recomputed examples with the 24 retained Math/Crypto drafting scripts and the new checker. Corrected substantiated mathematical and implementation-description errors. |
| 2 — coherence and source alignment | Ran whole-file label/reference and document-structure inventories; traced changed assumptions through the dependent proof text and corresponding lower/higher-volume explanations. Reread the affected sections, checked normative Sinsemilla and concrete Halo/Pasta source, and coordinated the Halo zero-knowledge caveats with Ironwood and the talk. Distinguished the released Orchard 0.15.3 source from the older local Orchard checkout. |
| 3 — adversarial regression | Rechecked all source documents for one document environment, no trailing document content, unique labels, and resolved local references. Reran numerical regressions and `git diff --check`. Independent agents reviewed the Math diff, new checker, extractor analysis, and selected Crypto security proofs. Their final three proof-coherence findings were corrected. The coordinator owns the final PDF/HTML/omnibus build gate; its results are recorded in the project audit. |

The final pre-build inventory included 458 Math labels, 383 Crypto labels, and
60 Halo labels. Math alone contains 141 proof environments; Crypto contains
70. This is an inventory, not a claim that each external theorem received a
new proof. Source line numbers change with final typesetting fixes.

## Substantive corrections

- **Mathematics:** nonempty integer ideals; nonzero-ring and zero-divisor
  qualifications; zero-polynomial/PID and polynomial-division edge cases;
  complete multiplicity lists; finite-field cardinality versus bit-width;
  the `n=1` vanishing-polynomial derivative case; known-value premises for
  barycentric evaluation; polynomial degree premises for convolution;
  complete versus incomplete curve addition; unrestricted classical-DL
  conjectures versus the proved generic-group lower bound; finite versus
  unbounded algorithm sample spaces; event families on uncountable spaces;
  the `p=2` inversion case; variable-time Tonelli–Shanks; and GLV's reduction
  in doubling count rather than an asserted halving of total cost.
- **Security models and reductions:** corrected binary-length formulas,
  finite-key/perfect-secrecy claims, PRG-existence premises, the reduction
  definition's non-negligibility requirement, and reduction factors versus
  bits. Shoup's proof now couples an independent symbolic execution to the
  real oracle instead of claiming uniformity after conditioning on no
  collision. Shor is outside the *classical* generic model, not necessarily
  outside a quantum generic model.
- **Hashing and symmetric crypto:** exact birthday threshold; no blanket
  transfer from ROM security to concrete black-box hashes; removed an invalid
  purported CGH construction in favour of a clearly external theorem;
  corrected SWU exceptional-branch scope, rational isogenies, effective
  cofactors, AES initial/final rounds and S-box, HMAC key normalisation,
  BLAKE2 final-state wording, Poly1305 injective framing/clamping, ChaCha
  counter exhaustion, conditional entropy with side information, and AEAD
  advantage conventions. Adaptive forgery analysis uses an identical-until-
  first-forgery comparison, not unjustified posterior-uniformity claims.
- **Commitments, signatures, and ZK:** KZG commitment hiding is distinguished
  from hiding evaluation proofs; IPA commitment binding alone does not prove
  evaluation binding. The forking lemma uses conditional probabilities rather
  than treating averaged success as a set. Schnorr now has an explicit
  simulation-error bound and includes the final verifier hash query. The
  single-challenge extractor now proves the stated knowledge error `1/N`,
  replacing a proof that only established `2/N`. Auxiliary-input ZK is not
  arbitrary concurrent composition; short proofs do not automatically imply
  computational soundness. Value balance requires compatible knowledge
  extraction and bounds excluding integer wraparound. RSA-FDH and EtM now
  state their unit-group and injective-framing premises explicitly.
- **Merkle trees:** verifier checks fixed depth and index range; path circuits
  constrain direction-bit booleanity; the frontier retains the full-tree
  root; update cost is `O(d)` at fixed capacity `2^d`; historical-root
  eligibility is protocol policy, not a hash property; binding prevents
  efficient equivocation but does not validate an adversarially supplied
  state. Extractor cost distinguishes building a tree from walking one path.
- **Halo2:** the deployed equality permutation covers **15 columns** (10
  advice, 1 instance, 4 fixed), hence **3** products with degree 9 and chunk
  length 7. The extended `8n`-point domain accommodates the quotient, not
  necessarily the degree-approximately-`9n` constraint numerator. Quotient
  chunks have fixed proof shape. Added explicit symmetric-IPA round and
  aggregate blinders, and explained why its exposed final scalar still
  requires the deployed initial polynomial mask. ZK claims retain joint-
  transcript and composition hypotheses. A curve cycle makes coordinates
  native, not every scalar-field calculation. The toy quotient is an
  illustrative Euclidean quotient, not an optimal cheat; gate satisfaction
  is distinguished from copy-constraint satisfaction and the full relation.

The Sinsemilla incomplete-addition discussion was not flattened into a blanket
"reject every exceptional input" rule. The normative specification explicitly
discusses unconstrained exceptional circuit intermediates and bounds finding
the corresponding exceptional inputs by discrete-log assumptions.

## Firsthand source evidence

Upstream files were read-only, after reading the repository instructions.

| Source | Pin / relevant locations |
| --- | --- |
| `/home/m/zcash/halo2` | `261faaccd5a30c19bb8468600841a0dac305adf5`; `halo2_proofs` 0.3.2, `halo2_gadgets` 0.5.0. `poly/domain.rs` constructs the extended domain and quotient degree; `plonk/permutation/prover.rs` splits columns at `cs_degree - 2`; `poly/commitment/prover.rs` constructs the initial vanishing mask, transcript challenges, round commitments, and synthetic blinder. |
| `/home/m/zcash/zips` | `69610984109078075e7e64989ecf89d63a259b97`; `protocol/protocol.tex` around 8145–8190, 9700–9895, and 11270–11305: exceptional note/address constraints, Sinsemilla definitions and collision/exception theorems, and Merkle encoding/sentinel rules. |
| `/home/m/zcash/orchard` | `bef8a27e89e395414b7a8fc72d5eff8d6ec871f1` is version 0.14.0, not the 0.15.3 implementation cited by Halo. It was not relabelled as the newer release. |
| Cargo registry `orchard-0.15.3` | `src/circuit_data/circuit_description_post_nu6_3`, including the complete permutation column list around 27425–27490. Manifest SHA-256 `397ec6785ace5af8a51a4f698f5fcca51a40d69fa6d34c7fe9c00e7946cba6f9`; circuit description `8d325ee6753c8effb7d5184bdd729255d2697dd1730c0278084cd91192020e90`. |
| Cargo registry `pasta_curves-0.5.2` | `src/curves.rs:663–690`: canonical field decoding, identity encoding, curve square-root check; unchecked compressed decoding delegates to checked decoding. SHA-256 `2d86c30347e71f7f961b355acc8cc99d0bc51963a09ff58ec358d921a784899e`. Field source confirms the square-root implementation paths. |

The Cargo registry root is
`/home/m/.cargo/registry/src/index.crates.io-1949cf8c6b5b557f/`.
The 0.15.3 source directory has no `.cargo-checksum.json`; the hashes above
pin the inspected content rather than asserting a registry-package checksum.

Primary web checks included [RFC 9380](https://www.rfc-editor.org/rfc/rfc9380.html),
[RFC 8439](https://www.rfc-editor.org/rfc/rfc8439.html),
[FIPS 197](https://csrc.nist.gov/pubs/fips/197/final),
[NIST's current SP 800-38G Revision 1 draft record](https://csrc.nist.gov/pubs/sp/800/38/g/r1/2pd),
[Canetti–Goldreich–Halevi](https://arxiv.org/abs/cs/0010019),
[Shoup](https://www.shoup.net/papers/dlbounds1.pdf),
[SafeCurves' twist criteria](https://safecurves.cr.yp.to/twist.html), and
[the author's publication record for Ghoshal–Tessaro](https://homes.cs.washington.edu/~tessaro/publications.html).
Some ePrint PDF fetches failed; these were not counted as full-paper readings.
The Ghoshal–Tessaro result is cited and scoped, not independently reproved or
certified as an exact deployed-Halo instantiation theorem.

## Executed numerical and structural checks

`python3 -B research/check_foundations.py` passes:

- F97 interpolation over `H=(1,22,96,75)` for the guide's trace and the talk's
  alternate final-row layout. Their Euclidean quotient coefficient vectors
  are `(61,70,43,47,81,46)` and `(15,91,7,1,43,34)` respectively.
- Changing the first output from 9 to 10 gives remainder
  `24*(1+X+X²+X³)` in both layouts, with exactly the roots `{22,75,96}`.
  The guide's four displayed evaluations at 20 are checked exactly.
- 1,872 exact rational row-distribution tests of the sharp extractor bound,
  including zero rows and one-accepting-challenge rows.
- 121 two-round symmetric IPA identities, comparing each coefficient of
  formal independent generators, including the aggregate blinding term.

All **24** scripts under `.wip/rewrite/{math-guide,crypto-guide}/compute/`
completed successfully with Python. These cover Euclid, rings, fields,
polynomials, Pasta parameters and twists, toy curves, probability, security
estimates, Poly1305, and the existing frontier example. Among them, the FFT
script exhausts all 28,561 length-four vectors over F13; the twist check
verifies the printed factorizations and recomputes the approximately 88-bit
and 108-bit generic twist costs. Some historical scripts use installed SymPy;
the new retained checker needs only the standard library.

`git diff --check` and the whole-source local-reference/unique-label checks
pass. An intermediate editing error duplicated Halo's tail because a JavaScript
replacement interpreted TeX `$'` as a replacement metasequence. The coordinator
caught it before final builds; the file was rebuilt from the original plus
literal callback replacements and checked for exact intended content, unique
labels, one document ending, and no trailing content. This incident was fixed,
not silently treated as a pre-existing source defect.

Independent review found the extractor derivation and checker sound, and
confirmed the generic-DL coupling, AEAD factor two, vector-Pedersen embedding,
forking calculation, and joint-extraction/range qualifications. Three remaining
proof-coherence issues were corrected after that review: adaptive hash-hiding
uses an independent ideal transcript; signing simulation uses identical-until-
bad coupling; hybrid-encryption games use one consistent advantage convention.

## Limits and build handoff

Final PDF, HTML, and omnibus checks are delegated to the coordinator; see
`research/audit-2026-09-05.md` for the final build outcome. This report does not
claim that an earlier successful PDF proves the subsequently edited text built.

This work is not a formal proof-assistant verification, a complete audit of the
upstream implementation repositories, or an execution of deployed proving and
verification test suites. It does not re-establish the security of AES, BLAKE2,
Poseidon, discrete logarithms, or the full PIOP–PCS–Fiat–Shamir composition.
Deep results such as Hasse's theorem, elliptic-curve associativity, PRG
existence implications, CGH separation, and full Halo simulation/extraction
remain external theorems or explicitly stated model assumptions. The retained
numeric tests check selected printed mathematics, not every possible circuit,
adversary, or runtime implementation. No claim of universal error absence is
made.
