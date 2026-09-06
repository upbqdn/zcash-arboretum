# Frontier review, 2026-09-05

Scope: FlyClient, FROST, ZSA, Crosslink, and the parked PQ, Tachyon and
Voting guides, plus `research/pq.md`, `research/tachyon.md` and
`research/voting.md`. Work crossed local midnight into 2026-09-06;
the final arithmetic check below ran at 2026-09-05 22:04 UTC.

## Coverage and the three passes

1. **Complete source read and correctness review.** Read all seven TeX
   files from beginning to end in chunks, recovering truncated output;
   over 17,000 source lines, not merely search matches. Read the three
   research notes completely. Checked definitions, formulas, algorithms,
   worked quantities, claims about deployed versus proposed mechanisms,
   and the reasons offered for security conclusions. Compared important
   claims directly with pinned implementation/specification objects and
   primary papers. Existing audit findings were evidence leads, not
   accepted as proof.
2. **Coherence and independent checks.** Revisited cross-volume interfaces,
   repeated conclusions, source status and dates, notation changes,
   finality/anchor/expiry claims, and the correspondence between the parked
   guides and their research notes. Recomputed the PQ tables and retained
   independent arithmetic tests. Retrieved Crosslink v13 from the primary
   repository and checked the implementation paths behind the later
   prototype additions, rather than extrapolating from the April fork.
3. **Adversarial final review.** Reread all edits and their relevant
   surrounding arguments, challenged edge cases and quantifiers, checked
   the revised summaries against their derivations, and reran the retained
   tests and whitespace check. This caught additional overstatements about
   Shor breaking every property, present ownership of previously disbursed
   outputs, the QROM comparison in a research note, and finality latency
   for already-old notes. The second and third passes were thematic and
   adversarial reviews across the scope, not claims that every external
   source or every line was reread independently three times.

The Ponytail skill kept implementation changes limited to direct source
corrections and one standard-library test file. No new dependency, document
framework, upstream change, or protocol implementation was introduced.

## Substantive corrections

### FlyClient

- Restored the positive-integer condition on the paper's optimal-sampling
  theorem and the tiling indices `0,...,k-1`.
- Separated the `k=1` edge case from the logarithmic sample-count formula,
  and distinguished a valid non-integer sample bound from the integer
  tiling optimality proof. Density normalisation, equal interval mass,
  and minimal integer sample counts are checked independently.

Evidence: [FlyClient, ePrint 2019/226](https://eprint.iacr.org/2019/226),
Theorem 2, pp. 16–17; [ZIP 221](https://zips.z.cash/zip-0221).
The existing conditional treatment of the paper's other proof gaps was
retained, not converted into a new security proof.

### FROST

- Stated distinct nonzero Shamir identifiers, `1 <= t <= n < q`, and
  independent uniform coefficients. Random polynomials have degree *at
  most* `t-1`, not necessarily exactly that degree.
- Made the source's switch from group-order `q` to query-count `q` and
  group-order `p` explicit in the BCKMTZ bounds.
- Cross-checked PQ discussion against the FROST volume's existing
  unmerged contributory-key-generation draft, rather than claiming that
  no such draft exists.

Evidence: [RFC 9591](https://www.rfc-editor.org/rfc/rfc9591.html),
[the FROST rerandomisation analysis](https://eprint.iacr.org/2024/436),
and `/home/m/zcash/reddsa` at
`3792daa95e588c1af6bd4805105bfb6ea7e9ad49`, including
`src/frost/redpallas.rs`. RFC 9591 remains an Informational RFC, not an
IETF Standards Track assertion.

### ZSA

- Added the required seed entropy, not merely the allowed byte length.
- Corrected the concluding split-nullifier statement: honest
  randomisation avoids the ordinary nullifier except with negligible
  collision probability, not with an absolute guarantee. Distinct
  opposite curve points share their x-coordinate.
- Corrected PCZT v2's status from draft to released while retaining the
  absence of ZSA support at the cited fork pins.
- Checked the split-note gates, field/scalar ordering, issuance and burn
  bounds, and the proof-size arithmetic; no new counterfeiting exploit
  was established.

Evidence: ZIP 32 at `zips` commit
`e753a6a301912cf77202db8f0d840f4796f5cca1`; ZSA sources at
`orchard-zsa cf801a5d6701bc128e21678ba0034564af4a2aca`,
`librustzcash-zsa 3f9b53fceb24443ca52adceb05d8a320c62dcd84`, and
`zips-zsa fd71419a8c5a048a520499c3f8c83ad62337fb47` under
`/home/m/zcash`. Important paths include `src/circuit.rs`,
`src/note/nullifier.rs`, issuance/burn validation, and the vanilla/ZSA
primitive proof-size constants.

### Crosslink

- Compatibility at two times does not imply monotonic extension. The
  no-rollback update rule supplies that separate property; the book's
  claimed equivalence at `construction.md:508` is too strong.
- The mutable best chain, not the monotone local finalized chain, is
  the object that may switch forks in the bounded-availability discussion.
- Made the book's historical meaning of “honest at time t” explicit.
- Corrected the reversed interpretation of disjunctive safety: a failure
  requires both premises to fail, but their failure does not prove a
  successful attack. The NTT threshold labels do not grant safety at
  exactly one third or one half Byzantine participation.
- Corrected the Quint comparison: excluding BFT forks is a restriction
  of the model, not greater coverage of them.
- Verified deepest-first `FindBlockHeaders` ordering. For tip `T`, the
  April supplied range is `T-sigma+1,...,T`; the two accessors choose
  different ends, while the book snapshot is the predecessor `T-sigma`.
- Did not project the old Crosslink-1 `mu+1+sigma` estimate onto
  Crosslink-2 finality. `L` bounds a block gap, not a stall's duration.
- Anchor validity is tested against candidate ancestry, not the
  displayed bounded ledger. Finality safety alone does not guarantee
  anchor availability in every transient best-chain view. A snapshot
  hash must belong to the finalized prefix; height comparison alone is
  insufficient.
- Qualified stall cleanup for custom/no expiry, new transactions, block
  arrival and wallet observation; pending transactions can expire under
  the SL branch too. Already-old notes need not incur a new finality wait.
- Restored the pending-reward multiplier in the repeated payment
  equations and used the same total in the following inequality.
- Verified v13's 150/70/75-block staking rules, five temporary height
  exceptions, 100-member cap, fixed 500,000,000-zatoshi bond compounding,
  placeholder action kinds, hard-fork schedule and 300-block burn index.
  Retargeting does not reset the unbond clock. Same-block delegation
  intervals are dropped; a burned status does not claw back an already
  completed withdrawal.
- Corrected v13 RPC descriptions: exact-final-height queries use the
  stored hash; lower heights use best-chain lookup. Unknown/off-best
  transactions return `None`, not `NotYetFinalized`. The separate block
  wait exits on `None`. Local lookups are not a proof of global agreement.

Evidence: [NTT, arXiv:2009.04987v3](https://arxiv.org/html/2009.04987v3);
`tfl-book fe6e1d6f403f62da46c64e8f5a7db3cb188ffae2`,
`crosslink-spec 8edc3e941fb45b32b7b68e3204e8df8330bcd43a`, and
`zebra-crosslink 6d02a1b80f896d08f923e39b2505f0565efb5787` under
`/home/m/zcash`. Read the construction's updater/ledger definitions and
security-analysis “Not updated for Crosslink 2” boundary directly.

The primary [v13 source](https://github.com/ShieldedLabs/crosslink_monolith/tree/807b995223b6e663cad4cb9890f4ade7dd320295)
was shallow-cloned to ignored `build/frontier-crosslink-v13`; both `main`
and the peeled v13 tag were verified as
`807b995223b6e663cad4cb9890f4ade7dd320295`. Checked paths include
`librustzcash/zcash_primitives/src/{bft.rs,transaction/mod.rs}`,
`librustzcash/components/zcash_protocol/src/consensus.rs`,
`tenderlink/src/lib.rs`, and within `zebra-crosslink/`:
`zebra-crosslink/src/lib.rs`, `zebra-consensus/src/transaction.rs`,
`zebra-rpc/src/methods.rs`, `zebra-chain/src/parameters/hardfork.rs`,
`zebra-state/src/{crosslink.rs,service.rs}`,
`service/non_finalized_state/chain.rs` and
`service/finalized_state/zebra_db/slashing.rs`.
No prototype network was run or subjected to exploit testing.

### Parked PQ and its research note

- Removed unconditional whole-chain privacy without a known address.
  Ideal commitment hiding and statistical proof zero knowledge do not
  defeat finite-entropy exhaustive search or metadata leakage.
- Corrected perfect-versus-statistical Halo 2 wording, ZIP-244's
  BLAKE2b-256 digest, the Poseidon field and nullifier sum/conversion
  order, and the research note's cubic-QROM/quadratic-classical comparison.
- Distinguished DLP-dependent properties from all properties of the same
  object, preimage/key search from collision search, and absence of a
  deployed public-key replacement from absence of all PQ cryptography.
- Made effective mining share an explicitly conditional memoryless
  rate-only illustration. Removed unsupported near-term, graceful
  degradation and negligible-dispersion assurances.
- Labelled signature/KEM byte substitution as a thought experiment,
  not a working protocol: rerandomisation, Pedersen balance binding,
  address distribution, encryption and circuits still need redesign.
- Corrected the claim that no PQ threshold-signature research exists.
  Retained the distinction from an integrated Zcash replacement.
- Scoped negative repository searches to their historical corpus and
  restored the parked volume's status outside the active series.
- Rephrased the single-logarithm claim across separate Groth16 keys and
  removed the unsupported implication that ZIP-271's original
  disbursement outputs remain unspent today.

Evidence: [FIPS 203](https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.203.pdf)
Table 3, [FIPS 204](https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.204.pdf)
Table 2 and the 32-byte seed paragraph, and
[FIPS 205](https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.205.pdf)
Table 2, read directly from the primary PDFs;
[Sattath, quantum mining](https://arxiv.org/abs/1804.08118);
[Tang et al., threshold signatures](https://eprint.iacr.org/2024/1067);
ZIPs 2005, 244 and 271 at the cited `zips` objects. The note retains its
July pins; these corrections do not silently turn it into a fresh
inventory of every repository or every PQ construction.

### Parked Tachyon and its research note

- Distinguished deployed sibling mechanisms from still-Draft ZIP status,
  and explicitly recorded ZIP 248's September 3 merge as a substrate
  update, not a core Tachyon specification.
- Distinguished a logical growing commitment tree from the small
  frontier sufficient to maintain its root.
- Corrected GGM decomposition to D direction chunks; noted the finite
  index horizon rather than literal indefinite spendability.
- A sentinel makes the polynomial nonzero, not its Pedersen commitment
  mathematically nonidentity. Linearity alone does not establish splice
  soundness. Added the separate binding/degree/challenge obligations.
- Added the missing little-endian wide-digest scalar reduction for action
  randomisers; replaced absolute uniqueness with negligible collision
  probability under fresh entropy.
- Corrected the rollover proof obligation: the live two-epoch scan and
  the historical absence-proof lineage jointly prevent double spends;
  far-apart spends need not collide in a single scan window.
- Qualified PIR cost by scheme, corrected exposure of all delegated-span
  nullifiers, and removed the unsupported availability “pick two” theorem.
  Archival replication and imported-key backups must be stated explicitly.
- Removed the unconditional PQ privacy inference and changed
  “unfalsifiable” benchmark claims to “unvalidated”.

Evidence: [Bowe–Miers, ePrint 2025/2031](https://eprint.iacr.org/2025/2031);
`tachyon 26fdc165a5f2f5c1b52f1ea4740c49462c112401`, especially
`book/src/{proof-tree.md,tachygrams.md,nullifiers.md}` and
`crates/tachyon/src/{primitives/seq.rs,digest/blake2b.rs,keys/ggm.rs}`;
`ragu-tachyon 830bbcdab7c993a894bcdbd479dbe5474ebcddb0` and
ZIP 248 merge `e753a6a301912cf77202db8f0d840f4796f5cca1`.
The mock implementation was not benchmarked as a production proof system.

### Parked Voting and its research note

- Removed the false assurance that the delegation proof's rho chain
  binds the client-supplied signed digest. The signature check and proof
  check share `rk`, but no sighash is among the fourteen public inputs;
  the chain receives no wrapping transaction to recompute it from.
  The fixture generator explicitly signs arbitrary 32 bytes.
- This is an unestablished authorisation boundary at historical pins,
  **not a demonstrated live exploit**. No live-round claim or suitability
  certification is made. The cast-vote digest path is different and is
  recomputed on chain.
- Removed claims of a completed first production poll and of only
  aggregates becoming public; the wallet feature shipped, but the
  provisioned poll was paused and reveal decisions are public.
- Sharing a prover/verifier crate does not prevent version/configuration
  drift or provide independent validation.
- Clarified x-only point-sign ambiguity, the canonical snapshot-tree
  assumption, and the sufficient IMT span bound.
- Removed the claim that Joint–Feldman bias permits arbitrary known-key
  selection, and the claim that ElGamal is private under every valid key
  regardless of key generation. The cited DKG composition remains an
  analytical obligation.
- A threshold coalition can decrypt individual share ciphertexts, but
  reconstructing a vote's weight additionally needs share-to-vote
  grouping. Kept the exact one-ballot under-claim analysis and its
  `q >= 2` and remainder-window conditions.

Evidence: `voting-circuits
4c39abd533c2b66a5aec1aa7a11fc7e80ce4bd32` at
`src/delegation/{circuit.rs,imt.rs,README.md}`,
`src/gadgets/van_integrity.rs` and `src/params.rs`; `vote-sdk
cb915f5117926a8ec2c3ee97f346af9b0cd66fac` at
`x/vote/ante/validate.go`, `circuits/tests/generate_fixtures.rs`,
`docs/tss-ceremony.md`, and the keeper/ElGamal tally paths. All are local
read-only source checks under `/home/m/zcash` against the cited commits.

## Retained checks and limits

- `python3 research/check_frontier.py`: **9 tests passed** on the second
  pass and again after final corrections. Tests cover sampling,
  interpolation, curve x ambiguity, proof sizes, exact probability tables
  using an independent binomial-tail identity, byte counts, splice
  identities, GGM parameters, finality/header/reward arithmetic, and
  voting quantisation/tally bounds.
- `python3 .wip/pq-drafts/compute.py`: original worked tables reproduced;
  the retained checker avoids depending solely on this ignored draft.
- `git diff --check` for all owned files and the new checker: passed.
- Final TeX builds and rendered-PDF checks are coordinated by the parent
  review agent in a single batch; see the project-wide audit for their
  final result. This report does not claim an unrun local compile.

Complete text coverage is not a machine-checked proof of every theorem,
a production implementation audit, or a guarantee that no errors remain.
The primary-source comparisons are targeted checks of the mathematical
and factual claims, not an exhaustive audit of the entire external
repositories. Historical source status is retained where intentional;
unmerged designs, source errata, analytical gaps and unavailable live
deployment state remain explicit rather than being labelled solved.
