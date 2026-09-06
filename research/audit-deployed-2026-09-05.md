# Deployed-volume audit — 2026-09-05

Scope: `consensus-guide.tex`, `ironwood-guide.tex`, `wallet-guide.tex`, and
`sync-guide.tex`. This report records three review passes, not a proof that
every possible error has been eliminated. The review preserves the guides'
detail and historical snapshots rather than replacing them with shorter,
less specific summaries. Ponytail was used to keep the verification helper
standard-library-only and avoid adding audit infrastructure.

## Coverage and passes

1. **Correctness pass:** read all four original sources sequentially in
   chunks, including mathematical displays, examples, tables, captions,
   footnotes, and source annotations: 1,543 consensus lines, 4,623 Ironwood
   lines, 5,724 wallet lines, and 3,687 sync lines (15,577 total). Re-read
   truncated output before continuing. Compared potentially problematic
   claims with protocol/ZIP text and the named implementations; inspected
   the relevant older findings in `research/correctness-audit.md` without
   treating that report as authoritative.
2. **Coherence/evidence pass:** revisited the corpus by topic: identities
   and viewing capabilities; note creation versus spendability; circuit
   versus signature versus chain-state checks; deployed versus draft and
   release versus checkout; anchor policy; privacy and quantum assumptions;
   transport versus chain trust. Verified newer source pins using local Git
   objects, checked primary web sources, and independently recomputed the
   displayed tables and selected vectors. Cross-volume issues were sent to
   the agents reviewing foundations, frontier proposals, and the talk.
3. **Adversarial final pass:** reviewed the final changes and their surrounding
   arguments for counterexamples: disclosed keys, publicly decryptable
   coinbase, dummy/zero-valued notes, checkpoint gaps, finite attacker
   stopping rules, reorg-invalidated scanning watermarks, variable batch
   sizes, malformed nullifier-only compact blocks, and historical consensus
   revalidation. Re-ran the numeric checker and whitespace checks. Built
   each owned volume independently into `build/audit-deployed/`; final
   production build/site checks are performed by the coordinating agent.

These are three different review lenses, not a claim of three identical
line-by-line reads or three independent formal verifications. The final
sources contain 15,698 lines before any later layout-only changes.

## Main corrections

| Area | Correction and reason |
| --- | --- |
| Consensus race model | The Rosenfeld catch-up probability is not a lower bound for Zebra's entire bounded-reorg process. Its tie comparison is scoped to the constant-difficulty, unlimited-rollback model. |
| Attack economics | A finite abandonment policy cannot silently use an eventual-success probability. The subsidy table is explicitly a stipulated-payoff heuristic, not a derived optimum or exact finite-policy expectation. |
| Public information | Transparent locking conditions do not establish real-world identity. Shielded proofs conceal witnesses, not transaction existence, Action counts, pool transfers, or publicly decryptable coinbase outputs. |
| Viewing capabilities | Full viewing keys recover outgoing outputs only when encrypted to the corresponding outgoing key; custom/discarded recovery keys are exceptions. Incoming viewing alone does not detect spentness or authorise spending. |
| Note privacy | Membership proves creation under an anchor, not unspentness. Candidate-tree size is not automatically the effective anonymity set. Authentic decryption still needs the commitment/ephemeral-key checks. |
| Anchor policy | Default target-height minus three is independent of whether the chosen note is trusted; untrusted notes separately need ten confirmations. Shared checkpoint gaps can deepen the anchor. ZIP-315's stated rationale is distinguished from anonymity-set inference. |
| Nullifiers | PRF/DDH alternatives are conditional component guarantees, not an unconditional whole-protocol theorem. Pool-local uniqueness does not imply cross-pool uniqueness for fabricated zero notes. |
| RedPallas | `GenRandom` hashes 80 input bytes but reduces a 512-bit hash output. The bias estimate now uses 512, not 640, bits. A circuit checks `rk = ak + [alpha]G`; `ask` is not an Action witness. Spend-authorisation signatures supply the separate authorisation check. |
| Action constraints | Nonidentity point types, zero-value qualifications, binding assumptions, and the separation from signatures/chain-state checks are explicit. The integer balance argument now states the Action-count/value limits that prevent modular wraparound. |
| Halo zero knowledge | Removed a naive simulator recipe that did not account for correlated transcript openings and the deployed masked IPA. The account is conditional on a full-composition simulation theorem, including entropy and random-oracle programming conditions. |
| Verification cost | Fixed-Action-count amortised verification is `O(log n + n/b)` for `b` proofs and `n` rows; the logarithmic slogan requires a sufficiently growing batch. Public-input/Action processing is not constant in Action count. |
| Protocol lineage | Original Sprout BCTV14 and later Sprout Groth16 are distinguished. Sapling's lack of a native Pasta-style recursion cycle is not impossibility of nonnative recursion. |
| Quantum boundary | One recovered IVK exposes all diversified addresses in that key scope, not just the known address; external IVK does not derive internal IVK. Generator logarithms do not by themselves give an efficient chosen Merkle path. Broken assumptions are not automatically constructed proof forgeries. Historical rules may be revalidated after an upgrade. |
| Invalid-key bound | Replaced an unjustified conditional-uniformity step with an unconditional complete-law accumulator and a union bound over the exceptional incomplete additions. The bound is explicitly over random-oracle-derived generators, not a measured invalid-key frequency for the fixed deployed constants. |
| Key/address descriptions | Fixed MKG/CKD labels, hardened purpose notation, domain-separation wording, receiver-type versus pool distinction, and the claim that F4Jumble supplies authentication. Added the Ironwood `0x0b` derivation with its direct `orchard` source attribution. |
| Fees and transaction construction | Corrected strict dust comparison, mempool penalty units, zero-change exceptions, cross-address-dependent padding, the distinction between shielded/transparent signers, and the gap between ZIP-374 requirements and a reference API's own checks. |
| Compact sync | Zero-sized empty trees are valid. Nullifier-only blocks may fail parsing before tree checks and cannot generally substitute for scan blocks. Pinned and newer Ironwood-serving protocol versions are distinguished. |
| Trust and metadata | Local payment detection is not independence from chain-data trust. An unminedness response is not a cryptographic proof. Peer IP may be a proxy; circuit isolation does not guarantee unlinkability against timing/content analysis. |
| Scan retirement | A zero Orchard watermark applies to the observed total balance at a particular post-activation block and its descendants; a reorg removing that block invalidates it. Zero-valued notes need not disappear. |

## Evidence and source pins

All upstream repositories were read-only. Repository instructions were read
before inspection. Baseline local HEADs:

| Repository under `/home/m/zcash/` | Commit |
| --- | --- |
| `zips` | `69610984109078075e7e64989ecf89d63a259b97` |
| `librustzcash` | `e30517e4335b4d850d35549f8366ba8bf817b17d` |
| `zebra` | `ef6325c0191d34148265a98a7281566f77a503e7` |
| `zaino` | `0e057e22b75a21d5cd093f20feb1ece3e23e94a1` |
| `lightwalletd` | `61fee32e4d96b3f62290f813eead965d78161ae5` |
| `orchard` | `bef8a27e89e395414b7a8fc72d5eff8d6ec871f1` |

Also inspected the newer Git objects cited by the guides, without confusing
them with those working-tree baselines: Zebra
`d1fd7adfd366bddfb8f38ce70b417a5e3408799b` (2026-09-04), lightwalletd
`09593edbee4ee68d47e5a53f8ce1c83514c4e8e6` (2026-08-27), and Zaino
`78eec7261ceed748a6eeb9132375d98200321a79` (2026-09-02). The new Zebra
configuration confirms disabled-by-default experimental plaintext gRPC;
the new Zaino source confirms its JSON-RPC/optional ReadState composition;
the lightwalletd changelog confirms the 0.5.4 release and reported-version
string discrepancy. Old pinned behavior is not relabelled as latest.

The separate released crate used for Ironwood claims is
`/home/m/.cargo/registry/src/index.crates.io-1949cf8c6b5b557f/orchard-0.15.0/`.
It must not be confused with the older `orchard` checkout. Content hashes:

| File relative to that crate | SHA-256 |
| --- | --- |
| `Cargo.toml` | `f79aa0fb52544c6a0fc60413406ef8baf6e445e838cf40fc5a2b938a8e9b9cf9` |
| `src/note.rs` | `856ede5c299f65e8d7d7a79880578b1782ec8c8c48392a6740b371e09d00720a` |
| `src/circuit.rs` | `96e269b06160dca34e9271341b233e2828efc826dabf85a1adb3a36ee119365a` |

Especially relevant firsthand checks:

- `zips/protocol/protocol.tex`, RedDSA hash/random generation definitions
  around lines 10730–10785; transaction count/value consensus rules.
- `orchard-0.15.0/src/circuit.rs`, witness structure around line 179;
  nonidentity gadgets at 546–554 and 774–785; randomized key check at 688.
  `src/note.rs:179–240` supplies `rcm_v3` and its 137-byte input layout.
- `librustzcash/zcash_client_backend/src/data_api/wallet.rs:436,568–575`,
  default confirmations and anchor bound;
  `zcash_client_sqlite/src/wallet.rs:3072–3099`, shared-anchor selection.
  The latter really selects the minimum Sapling/Orchard checkpoint in this
  pin: an initially suspected missing Ironwood term was **not** inserted
  into the guide's implementation formula.
- `zcash_client_backend/src/fees/common.rs:684–706`, strict dust comparison,
  zero-change allowance and `AddDustToFee` omission;
  `zebra/zebra-chain/src/transaction/unmined.rs:71,426`, fee-penalty units.
- `zaino/packages/zaino-fetch/src/chain/block.rs:177,186`, public conversion
  helper returning compact proto version 1 and its sole in-repository
  caller in diagnostic error formatting. Serving builders in
  `zaino-state` instead write 0. The literal is in the helper, not literally
  embedded inside the Debug string; no gRPC route to version 1 was found.
- `zcash_client_backend/src/scanning/compact.rs:174`, malformed Orchard
  compact outputs fail encoding checks before later tree-size checks.
- `zips/zips/zip-0326.md:180` and surrounding scanning requirements,
  zero balance at a block and descendants; `zip-0316.rst` around line 1010,
  external/internal viewing scope.

Primary web checks covered the original race paper's version history
([Rosenfeld](https://arxiv.org/abs/1402.2009)), the block-time model
([ZIP-208](https://zips.z.cash/zip-0208)), separate Ironwood transaction
rules and document status ([ZIP-229](https://zips.z.cash/zip-0229)), the
post-quantum boundary ([ZIP-2005](https://zips.z.cash/zip-2005)), the anchor
policy's stated rationale ([ZIP-315](https://zips.z.cash/zip-0315)), and
unified receiver/viewing-key scopes ([ZIP-316](https://zips.z.cash/zip-0316)).

The prior audit's G1 coinbase-gating concern is already correctly scoped.
Its release/checkout concerns G2/G4/G5/G7/G8 are resolved by the explicit
0.15.0 versus `bef8a27e` attributions in the present guides; the released
crate genuinely has the Ironwood derivations and circuit versions. G9's
wire-version concern is resolved by tracing the helper's actual caller,
not by assuming the old report's reachability claim is true.

## Executed checks and limits

`python3 research/check_deployed.py` passes, repeatedly:

- 90 printed probability cells, with exact rational rounding/bound checks;
- 33 strict minimum-confirmation thresholds, including preceding values;
- 30 exact integer floors in the explicitly heuristic profit table;
- 100 independent negative-binomial/binomial-tail identity comparisons;
- all four printed F4Jumble rounds and inverse using `hashlib.blake2b`;
- field, reduction-width, invalid-key numerical bounds, ciphertext/input
  sizes, proof size, payment cap, subtree counts, and framing arithmetic.

The helper reads the actual printed tables rather than merely repeating a
drafting script's output. It adds no dependency, network access, or generated
data. It supersedes the old 640-bit reduction-width calculation in the
historical `.wip` drafting script; that scratch file was not modified.

All four isolated Tectonic builds exited successfully. The logs have no
undefined references or overfull-box warnings. They do contain package
`unicode-math` notices and `mdframed` bad-break warnings: one near wallet
line 1858/pages 23–24, two near consensus line 494/pages 6–7. These were sent
to the coordinator for final layout inspection; no claim is made that they
pre-date this audit. The small final wording changes after the isolated
builds are covered by the coordinator's final build, not silently counted
as having already been compiled. `git diff --check` passes for owned files.

Limits: this is not machine verification of the mathematical exposition,
an exhaustive audit of the upstream workspaces, or a consensus-node test
campaign. No production wallets, live captures, reorg networks, deployment
settings, or full protocol proofs were tested. Historical July measurements
remain dated observations rather than freshly repeated measurements. The
complete HD/FF1 hexadecimal key derivation was not independently rerun;
the F4Jumble trace and selected arithmetic were. Full Halo zero-knowledge
and privacy claims are conditional composition arguments, not newly proved
theorems. Review and successful compilation cannot certify absence of all
remaining errors.
