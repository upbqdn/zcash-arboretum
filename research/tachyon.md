# Project Tachyon: rigor inventory

Ground truth: zcash/zips `c6b70358` (2026-07-05, verified equal to origin/main 2026-07-08);
tachyon-zcash/tachyon `26fdc165` (2026-07-07, local `/home/m/zcash/tachyon`); tachyon-zcash/ragu
`830bbcda` (2026-07-05, local `/home/m/zcash/ragu-tachyon`); tachyon-zcash/zips fork `a2a71f2b`
(local `/home/m/zcash/tachyon-zips`). Web sources fetched 2026-07-08. Method per
`CONVENTIONS.org`: three-bin classification (specified / designed-unspecified / open-problem),
firsthand verification, recorded hashes. Synthesized and deduplicated from four finder passes
(project survey, ZIP landscape, Ragu source survey, nullifier/OSS/payments deep dive).

## 1. Sources

### Primary

- **eprint 2025/2031** — Bowe & Miers, "A Note on Notes: Towards Scalable Anonymous Payments via
  Evolving Nullifiers and Oblivious Synchronization"; received 2025-11-02, revised 2025-11-03.
  The canonical publication for evolving nullifiers + oblivious sync: 8 pages, self-described
  "short note", zero theorems, no formal security definitions. Direct PDF Cloudflare-gated; full
  text via Wayback `web.archive.org/web/20251103200800/https://eprint.iacr.org/2025/2031.pdf`.
- **tachyon-zcash/tachyon @ `26fdc165`** (2026-07-07) — `zcash_tachyon` crate + mdBook; the most
  concrete design material (`book/src/{nullifiers,tachygrams,anchor,proof-tree,aggregation,keys,
  notes}.md`, `book/src/zips/`). Sole committer Tal Derei; crate stubs the load-bearing crypto.
- **tachyon-zcash/ragu @ `830bbcda`** (2026-07-05) — canonical Ragu PCD framework (formerly
  ebfull/ragu), ~43.8k LOC Rust + Ragu book, rendered at tachyon.z.cash/ragu/.
- **tachyon-zcash/zips fork, PRs #1–#4** (opened 2026-06-02, all OPEN as of 2026-07-08) — four
  ZIP-0-conformant amendment drafts (ZIP 317 fees, ZIP 209 turnstile, ZIP 221 MMR, ZIP 248 bundle
  registration). Local clone `/home/m/zcash/tachyon-zips @ a2a71f2b`.
- **zcash/zips @ `c6b70358`** (2026-07-05) — ZIP-status ground truth. Plus gh queries 2026-07-08:
  PR #1156 (ZIP 248, OPEN, idle since 2026-05-26), PR #1319 (NU6.3 batch, OPEN), PR #1317
  (Ironwood migration), issue #1302 (ZIP 2007 scoping).
- **Sean Bowe blog** — "Tachyon: Scaling Zcash with Oblivious Synchronization" (2025-04-02,
  founding post); "Ragu for Orchard, part 1" (2025-04-17); "Tachyaction at a Distance"
  (2025-05-15); "Zcash and Quantum Computers" (2025-10-16). Index ends 2025-10-16; the promised
  deep-dive posts never appeared.
- **tachyon.z.cash** — homepage / overview / roadmap / team (roadmap dateless); project blog
  "Folding Tachyon with Ragu" (Bowe & Derei, 2026-05-07); Ironwood-turnstile posts (2026-06-06,
  2026-07-07).
- **Forum megathread t/50789** ("Scaling Zcash: Tachyon. Ragu") — 28 posts, 2025-04-02 to
  2026-01-31, enumerated via Discourse JSON API. Substantive designer posts: #22 (2025-11-04),
  #25 (2025-11-16), #28 (2025-11-21).
- **ZK Podcast 388 transcript** (2026-01-21) — Bowe on per-epoch nullifier unlinkability,
  wallet-side proof re-randomization, recoverability ("can of worms").
- **GitHub issues, tachyon-zcash/tachyon** — #121 (PIR pivot, 2026-05-26), #79 (epoch tuning),
  #103–#107 + #114 (ZIP stubs / tracker), #161/#137/#135 (soundness and malleability churn),
  #139/#86/#87/#97/#98 (derivation alternatives).
- **Governance** — ZF "NU7 Polling Results" (2026-02-23); Zcash Engineering Office Hours #5
  (2026-03-17, forum t/54923 + recording).
- **API snapshots (2026-07-08)** — GitHub Actions/releases/org listings; crates.io (no `ragu`
  crate); Codecov (93.8 % line coverage, snapshot 2026-03-08).

### Secondary

- CoinDesk Research, "Building the Zcash Machine" (2026-06-30, commissioned by GenZcash): carries
  no primary TPS/size figures; "thousands of shielded TPS" is analyst characterization.
- Messari, "Zcash: Building Encrypted Money at Planetary Scale" — unfetchable this session
  (HTTP 403/429); the circulating ≈2,200 TPS / ≈660 TPS at ~1.5 kB / 9.3 kB→450 B figures trace
  here via search summaries only. Analyst estimates, not project specifications.
- ZecHub Shielded News Vol. 22 (misdates the Ragu post as June 7); CoinDesk press (2026-05-08) on
  the Bowe/Ojha PQ-roadmap whiteboard session.

### Provenance caveats

- The fetched eprint HTML contained embedded prompt-injection strings (fake "SYSTEM INSTRUCTION"
  abort message, word-replacement directives); ignored as untrusted page content. Extracted
  metadata cross-checks against the BibTeX record and the Wayback PDF.
- Local `/home/m/zcash/ragu` is stale ground truth: an ebfull/ragu snapshot at `276a093e`
  (2026-02-06), ~370 PRs behind canonical main; the intervening rewrite reorganized modules
  (circuits/→internal/, s/→wiring/, structured/unstructured→sparse) and added the mock feature,
  Lean FV, and fuzzing. Cite `830bbcda` at `/home/m/zcash/ragu-tachyon`.

## 2. Claim inventory

### 2.1 Specified

Tachyon standing:

- Governance: Tachyon drew "universal or near-universal support across every group … the most
  unambiguous signal from the entire poll" in the February 2026 NU7 sentiment poll; the stated
  next step is only to "assess technical readiness and scope for inclusion in NU7". It is not
  scheduled into any upgrade: draft-arya-deploy-nu7 (Status: Draft, branch `0x77190AD8`, heights
  TBD) lists no Tachyon ZIPs. [zfnd.org NU7 post 2026-02-23; zips `draft-arya-deploy-nu7.md`
  @ `c6b70358`]
- ZIP-process standing: Sean Bowe and Tal Derei serve as ZIP editors "associated with Project
  Tachyon", and the protocol spec's author block carries the affiliation. Institutional fact
  only. [zips `zip-0000.rst:196`, `protocol/protocol.tex:2953` @ `c6b70358`]
- Out-of-band substrate at spec rigor: ZIP 321 (payment request URIs, Status: Active) and ZIP 324
  (URI-Encapsulated Payments, Status: Draft, created 2019). ZIP 324 predates Tachyon, mentions it
  zero times, and declares the transport channel out of scope ("It is outside the scope of this
  proposal to establish a secure communication channel"). The Tachyon book defers unlinkability
  to exactly these. [zips `zip-0321.rst`, `zip-0324.rst` @ `c6b70358`; tachyon `book/src/keys.md`
  @ `26fdc165`]

Adjacent ZIP environment:

- Transaction version 6 is defined at ZIP rigor by ZIP 229 (Draft, created 2026-06-13, NU6.3
  Ironwood pool), not by withdrawn ZIP 230: full field table, all sixteen v5→v6 BLAKE2b
  personalization changes, anchors moved from effecting to authorizing data, ZIP 221 history-tree
  changes; non-requirements explicitly drop ZSA, explicit fee, zip233Amount, sighashInfo. [zips
  `zip-0229.md` lines 7, 161–167, 174–241, 327–412, 421–484 @ `c6b70358`]
- ZIP 231 memo bundles (Status: Draft): the crypto core is at full ZIP rigor — 272-byte chunks,
  16 KiB limit, reserved K^memo values, ChaCha20-Poly1305 STREAM variant, order-preserving
  shuffle with a MUST privacy property, two-pass decryption, ZIP 317 Revision 2 fee treatment.
  (Gaps binned below.) [zips `zip-0231.md` lines 9, 201–445; `zip-0317.rst` lines 11, 199–221
  @ `c6b70358`]
- ZIP 2005 "Ironwood Quantum Recoverability" (Status: Proposed): the recoverable-note
  construction (lead byte 0x03, rcm/psi derivation, qsk/qk, FROST/hardware paths) is specified,
  no TODO/TBD markers in 115 KB, activation bound to NU6.3. Caveat in its own words: the Recovery
  Protocol is described "in outline but not in detail: many of its design decisions are
  intentionally left open" — that part is designed-unspecified. [zips `zip-2005.md` lines 9,
  61–65, 1988 @ `c6b70358`]
- NU6.2 is the settled upgrade: ZIP 257 (Status: Final, set 2026-07-05) retrospectively specifies
  the 2026-05-29 Orchard Action circuit soundness vulnerability (GHSA-ww9q-8r59-xv46), the
  temporary Orchard shutdown (Mainnet 3363426), NU6.2 activation (branch `0x5437F330`, Mainnet
  3364600 on 2026-06-03), the corrected verifying key, and the canonical proof-length rule
  (2720 + 2272·nActionsOrchard bytes). [zips `zip-0257.md`, `README.rst:49–52` @ `c6b70358`]
- NU6.3 deployment constants are pinned in ZIP 258 (Status: Draft): CONSENSUS_BRANCH_ID
  `0x37A5165B`, Testnet activation 4134000, Mainnet activation 3428143,
  MIN_NETWORK_PROTOCOL_VERSION 170160 on both networks, v6 TX_VERSION_GROUP_ID
  `0xD884B698`, Orchard pool spend-only, and ZIP 2005 activation. The Mainnet
  height and protocol versions landed after this memo's original snapshot;
  the Action-circuit-update draft remains separate. [zips `zip-0258.md` lines 5,
  56–98 @ `c6b70358`, current constants @ `ad30e59`; zcash/zips#1319]

Ragu code facts (all verified in source at `830bbcda`):

- Ragu is a Rust PCD framework implementing a modified Halo [BGH19] recursive SNARK with no
  trusted setup; workspace version 0.0.0, zero GitHub releases, not on crates.io. [`Cargo.toml`,
  `README.md`; GitHub releases API, crates.io API 2026-07-08]
- Pasta is the only implemented curve cycle (`impl Cycle for Pasta`, CircuitField = Fp, baked
  Poseidon parameters over both fields); secp256k1/secq256k1 named only as a possible future
  direction. [`crates/ragu_pasta/src/lib.rs:44–80`, `crates/ragu_arithmetic/src/lib.rs:1–60`]
- A working PCD pipeline exists: ApplicationBuilder::register/finalize, seed (leaf), fuse (binary
  merge via an 11-stage prover pipeline), rerandomize, verify, over native (Pallas-field) plus
  nested (Vesta-field, CycleFold-style) registries; integration tests build and verify multi-node
  PCD trees. [`crates/ragu_pcd/src/{lib.rs,fuse/mod.rs,verify.rs}`, `tests/nontrivial.rs`]
- Proofs are not succinct and verification is linear-time: the `Proof` struct carries ~20 full
  sparse polynomials; verify() computes revdot claims and evaluates full polynomials directly; no
  Bulletproofs/IPA opening argument exists anywhere in the code. [`crates/ragu_pcd/src/proof/
  mod.rs:129–165`, `verify.rs:74–127`]
- The verifier is knowingly incomplete: an in-code TODO records missing checks for
  registry_wx0_poly, registry_wx1_poly, registry_wy_poly. [`crates/ragu_pcd/src/verify.rs:122`]
- Two security placeholders remain on main: the Fiat–Shamir domain tag is literally `b"FIXME"`
  ("choose a permanent domain separation tag before release"), and registry binding uses 6 hash
  iterations flagged "FIXME(security): … insufficient to fully bind the registry polynomial"
  (issues #78, #316), seeded from placeholder challenges w=2, x=3, y=5.
  [`crates/ragu_pcd/src/lib.rs:50–51`, `crates/ragu_circuits/src/registry.rs:673–692`]
- Zero-knowledge is not automatic: fuse() output is not ZK unless Application::rerandomize is
  called, and rerandomization rests on an in-code "temporary hack" (cached seeded-trivial proof).
  [`crates/ragu_pcd/src/fuse/mod.rs:55–61`, `lib.rs:262`]
- QA machinery is heavy and green: 445 `#[test]` functions + 12 proptest suites, 93.8 % line
  coverage (Codecov snapshot 2026-03-08), 20 libFuzzer targets on twice-weekly cron, Lean 4
  formal verification of ~28 gadget circuits with a Rust-extraction fingerprint-equivalence check
  in CI, cargo-vet, zizmor; all 7 workflows green at `830bbcda`. [`qa/{fuzz,lean}/`,
  `.github/workflows/`; GitHub Actions API 2026-07-08]
- No security audit has been published as of 2026-07-08: README warns "Ragu is under heavy
  development and has not undergone auditing. Do not use this software in production"; the
  roadmap lists "several rounds of optimization and auditing" as future work. [`README.md`
  @ `830bbcda`; tachyon.z.cash/roadmap/]

### 2.2 Designed but unspecified

Core protocol:

- Wallet state as proof-carrying data: the founding post's concept is elaborated into a concrete
  19-step proof tree (NfMasterSeed → StampLift, typed headers, per-role assignments) in the book,
  but no protocol spec or ZIP exists — the core "Tachyon Shielded Protocol" ZIP is an empty stub
  (issue #103) and the crate's proof creation/merge/verification is "Stubbed (pending Ragu PCD
  and Poseidon integration)". [blog 2025-04-02; tachyon `book/src/proof-tree.md`, `README.md`
  @ `26fdc165`]
- Proof-tree soundness is prose-only: the book's Soundness section argues splice identities
  (C(X)=L(X)+X^s(p−1)+X^{s+1}R(X)), GGM-leaf binding, and cm threading, with no formal
  definitions, theorems, or machine-checked proofs; the eprint note has zero theorems; Bowe's own
  founding post flags PCD recursive-soundness bounds as "largely ignored in practice". [tachyon
  `book/src/proof-tree.md` @ `26fdc165`; eprint 2025/2031]
- Evolving nullifiers: the eprint gives only a sketch ("As a concrete example",
  η_e = PRF(k_note, ρ‖e)); the concrete derivation — GGM tree of depth D/arity A over Poseidon,
  mk = Poseidon_{Tachyon-NfPrefix}(ψ, nk), leaf under Tachyon-NfDerive, with
  cm = Poseidon_{Tachyon-CmDerive}(rcm, pk, v, ψ) freezing the sequence — exists only in the
  book; the crate stubs nullifier derivation and calls the commitment scheme "TBD". No ZIP.
  [eprint 2025/2031 §1.3; tachyon `book/src/nullifiers.md`, `crates/tachyon/src/note.rs`
  @ `26fdc165`]
- Dual-nullifier spends and the pruning consensus rule: a spend publishes two nullifiers (anchor
  epoch e and e+1); consensus checks every tachygram for duplicates over exactly the current and
  immediately preceding epoch and may permanently prune older ones. Book-only; the eprint has
  only the looser "validators must still check for duplicates"; no consensus ZIP drafts the rule.
  [tachyon `book/src/tachygrams.md`, `nullifiers.md` @ `26fdc165`; forum t/50789 #22]
- Note expiry was considered and rejected as the pruning mechanism ("users must move their funds
  into a new note, once per window, or lose their funds"); evolving nullifiers supersede it, and
  notes stay spendable indefinitely via delegated absence proofs (SpendableInit/SpendableLift/
  VerifyUnspent). Any expiry-based framing of Tachyon is obsolete. [eprint 2025/2031 §1.1 + fn.3;
  tachyon `book/src/proof-tree.md` @ `26fdc165`]
- Nullifier-derivation reversal ("not determined by the note commitment but rather the other way
  around", founding post): the intent — nullifiers carry no accumulator-position information —
  survives in the GGM design, but the 2026 book has cm pin the entire nullifier sequence (both
  derive from shared secrets), so the literal claim is dated. Nothing at ZIP rigor. [blog
  2025-04-02; tachyon `book/src/nullifiers.md` @ `26fdc165`]
- Trustless delegation of absence proving: a wallet hands a delegate a bounded window of future
  nullifiers under a Pedersen window commitment with sentinel (δ = Σ[Δ_{e+i}]G_i + G_d), re-based
  so any window stands alone; realized as Unspent/VerifyUnspent steps. Design-book construction
  only; crate stubbed. [tachyon `book/src/nullifiers.md` (Delegation), `proof-tree.md`
  @ `26fdc165`]
- Validator pruning / "removes runaway state growth": a Poseidon hash-chain anchor (stamp /
  empty-block / epoch-step domains) replaces the nullifier set and note commitment tree;
  validators keep "the leading edge of revealed nullifiers … but can otherwise permanently
  prune". Described in eprint + book, in no spec; users/OSS still need the pruned history (see
  DA, §2.3). [tachyon.z.cash; tachyon `book/src/anchor.md` @ `26fdc165`; forum t/50789 #22]
- Aggregation: autonome → aggregate → adjunct lifecycle, cActionsTachyon fast-fail indicator,
  miner stripping, re-aggregatable aggregates; open in-file TODOs ("Explain tachygram set union
  validation algorithm", "Define aggregation limits"); Bundle and Aggregator ZIP stubs empty;
  depends on unmerged ZIP 248. [tachyon `book/src/aggregation.md`, `book/src/zips/` @ `26fdc165`]
- Pool decision: a new shielded pool independent of Orchard with signed valueBalanceTachyon and a
  ZIP-209-style turnstile (the 2025-05-15 post's Orchard-upgrade alternative has been dropped).
  The draft exists only as fork PR #2 (Status: Draft, owner Derei, 2026-06-02, OPEN), not
  upstreamed, and defers to a core protocol reference that does not exist.
  [tachyon.z.cash/roadmap/; tachyon-zcash/zips#2]
- ZIP program: an 11-ZIP dependency map (5 additive, 5 update, 1 deployment). The five core
  additive ZIPs (Shielded Protocol #103, Bundle #104, Accumulator #105, Aggregator #106,
  OSS #107) are empty stubs; the four peripheral amendment drafts sit as OPEN PRs #1–#4 on the
  project's own fork since 2026-06-02; upstream zcash/zips has zero Tachyon ZIPs or PRs.
  [tachyon `book/src/zips/tachyon-zips.md` @ `26fdc165`; issue #114; gh searches 2026-07-08]

Oblivious synchronization:

- OSS trust model: services are "fully oblivious to their clients' transaction details", never
  see note/cm/ψ/mk, keep "ephemeral state per client", and clients switch freely — eprint
  abstract plus book role tables. No formal threat model, no security definition of "oblivious",
  no service or handoff protocol; obliviousness rests on epoch unlinkability plus proof
  re-randomization "generally addressed by re-randomizing the proof" — asserted, not constructed.
  [eprint 2025/2031; tachyon `book/src/proof-tree.md`, `book/src/zips/oss.md` @ `26fdc165`]
- OSS amortization: services shard the nullifier space via PCD precomputation; total effort
  claimed "asymptotically similar" to today's validators — a forum "I believe" with no published
  complexity analysis or benchmark. [forum t/50789 #28, 2025-11-21]
- No new DA layer: "Tachyon will not involve a new DA layer; the blockchain will continue to be
  used to post nullifiers and note commitments, but not much else" — forum statement; the eprint
  treats a DA layer only as a hypothetical extension. [forum t/50789 #25, 2025-11-16]

Payments:

- Pre-pivot out-of-band design: "out-of-band payments for the first time in a Zcash shielded
  protocol"; removes key diversification, viewing keys, payment addresses; notes drop diversifier
  and ρ; RedPallas re-randomization and homomorphic value commitments retained. No payment-
  protocol spec; the roadmap still lists two unreconciled approaches. Statements from this era
  (blog posts, book `keys.md`) predate the May-2026 pivot and must be dated. [blog 2025-05-15;
  tachyon.z.cash/roadmap/]
- May-2026 PIR pivot (issue #121, 2026-05-26, verbatim): "Since we're using PIR to make repeated
  payments flows without OOB, there are stale parts of the book that will need to change. We're
  retaining in-band secret distribution for recover from seed flows." The PIR + post-quantum
  key-exchange payment protocol is "developed independently in collaboration with" the team and
  has no published specification — roadmap-paragraph and podcast/whiteboard rigor only.
  [tachyon-zcash/tachyon#121; tachyon.z.cash/roadmap/]
- Post-quantum privacy ("full post-quantum privacy" as a side effect): Bowe's 2025-10-16 post
  scopes this to privacy (harvest-now-decrypt-later), conceding ECC-based soundness remains
  quantum-vulnerable (mitigated by turnstiles/recoverability, not Tachyon). No PQ privacy
  analysis published; the PIR channel's PQ key exchange is undesigned; statistical hiding of the
  Pedersen/Poseidon commitments is asserted, not proven. [tachyon.z.cash; blog 2025-10-16]

Marketing figures and timeline:

- "Shrinks transactions by two orders of magnitude": homepage headline with no published
  benchmark or size specification; the ~100× refers to marginal on-chain size after aggregation/
  stripping and no primary document derives it. "Thousands of shielded TPS" is office-hours
  promotion; the concrete circulating numbers (≈2,200 TPS, ≈660 TPS at ~1.5 kB, 9.3 kB→450 B)
  are Messari/CoinDesk analyst estimates, not project figures — Bowe's posts contain no TPS
  numbers and his April-2025 promise of PCD-toolkit benchmarks is unfulfilled. [tachyon.z.cash;
  forum t/54923; CoinDesk Research 2026-06-30]
- Timeline: the founding post's "many of the major scalability improvements should be able to hit
  mainnet within a year" (2025-04-02) is falsified — as of 2026-07-08 nothing is on testnet or
  mainnet, no ZIP is upstreamed, Ragu is unaudited, the proof layer is stubbed. The current
  roadmap contains no dates. [blog 2025-04-02; tachyon.z.cash/roadmap/]

Ragu design and integration:

- Performance estimates: ~100 ms aggregated verification at K=11 and ~50-transaction break-even
  vs Orchard batch verification, self-labelled "rough estimates that should be validated with
  empirical benchmarks"; a criterion/gungraun bench harness runs in CI but publishes no numbers.
  [ragu `book/src/protocol/analysis.md` @ `830bbcda`]
- Protocol specification absent: every protocol-design chapter of the Ragu book (arithmetization,
  NARK, split accumulation, PCS batched evaluation, wiring, revdot, registry polynomial,
  endoscalars, staging, recursion, assumptions, analysis) is marked `<!-- todo -->`; the design
  composite (BCCGP16-lineage arithmetization, split accumulation [BCLMS20], CycleFold nesting,
  SHPLONK multi-point queries, Halo post-processing without verification keys, Poseidon
  Fiat–Shamir, application-facing polynomial queries for dynamic memory checking) is designer
  prose without proofs. [ragu `book/src/SUMMARY.md`, `book/src/protocol/index.md` @ `830bbcda`]
- Tachyon-on-Ragu integration is mock-only: the `zcash_tachyon` crate registers 19 Steps
  (delegation, pool, spendable, stamp, spend families) with polynomial-query claims, but compiles
  only against ragu's `mock` feature (a no-crypto API mock, pinned to a contributor fork,
  rev `98a15d32`); note commitments, nullifier derivation, proof creation/merge/verify, and stamp
  compression are stubbed. [tachyon `crates/tachyon/{Cargo.toml,src/stamp/proof/mod.rs,README.md}`
  @ `26fdc165`; ragu `src/mock/mod.rs` @ `830bbcda`]

Meta:

- The GGM/delegation/pruning machinery is a post-paper, single-committer engineering elaboration
  with no independent publication: none of it (GGM trees, dual nullifiers, two-epoch window,
  Pedersen sequence commitments, spendable/lift lineage) appears in the eprint, and the design is
  churning — derivation alternatives open (#139, #86, #87/#97/#98) and live soundness/
  malleability issues (#161/#137/#135: bundle commitment order-free over actions ⇒ malleable to
  action reordering). [tachyon issues, fetched 2026-07-08; `git shortlog` @ `26fdc165`]
- Crosslink/ZSA compatibility is asserted without interaction analysis; Shielded Labs calls them
  "separate efforts"; forum discussion disputes the roadmapping independence. [blog 2025-04-02;
  forum t/50789 #10–#12]

Adjacent ZIP landscape:

- ZIP 230 (Status: Withdrawn, 2026-05-18): the byte-precise OrchardZSA v6 format (Action Groups,
  issuance bundle, memo-bundle fields, explicit fee, zip233Amount, sighashInfo) has no deployment
  path; its warning "Transaction version number 6 is now defined by ZIP 248" is stale relative to
  ZIP 229, which tolerates the collision. [zips `zip-0230.rst` @ `c6b70358`]
- ZIP 246 (Status: Withdrawn, 2026-06-24): v6 digests now belong to ZIP 229; the
  sighash-algorithm-versioning concept (sighashVersion ‖ associatedData) survives only in
  withdrawn text and the unmerged ZIP 248 PR — ZIP 229 uses plain ZIP-244-style hashing. [zips
  `zip-0246.rst` @ `c6b70358`]
- ZIP 248 (extensible transaction format) — the designated home for everything ZIP 230/231/246
  defer to — is not in the repository at all; it exists only as open PR zcash/zips#1156 (idle
  since 2026-05-26). The entire NU7 ZSA/memo-bundle format stack has no merged specification.
  [zcash/zips#1156]
- ZIP 231 gaps: the memo-bundle sighash commitment is an explicit "TODO: finish this as a
  modification to ZIP 248"; lead byte {{MBLEADBYTE}} unassigned; ZIP 302 interaction TBD; memo
  retention an open issue; the carrier format is orphaned by ZIP 230's withdrawal (ZIP 229's v6
  has no memo-bundle fields). [zips `zip-0231.md` lines 417–420, 571–589, 734–739 @ `c6b70358`]
- ZIP 324 core unpinned: the rseed domain separator is the literal `[0xFIXME]` (with a TODO
  proposing a different derivation entirely); the note-identification section is marked "out of
  date … To be revised"; the draft ends with "Publication Blockers"; Sapling-only. [zips
  `zip-0324.rst` lines 148–158, 257, 384, 458–463 @ `c6b70358`]
- ZIP 2004 (remove consensus dependency on note encryption — groundwork any out-of-band or
  oblivious-sync design needs): Status Draft, NullSym written, but "TODO: specify the handling of
  the ephemeralKey field" and a stale deployment hook citing withdrawn ZIP 230; the actual v6
  (ZIP 229) omits it. [zips `zip-2004.rst` lines 6, 83–128 @ `c6b70358`]
- Tachyon-motivated transparent-value-disable draft: one precise rule (transparent output value
  ≤ transparent input value), unnumbered (ZIP: XXX), Status Draft, no NU assignment; its
  motivation cites the Tachyon founding post ("The transparent scripting system is too
  complicated to implement in a zk-SNARK circuit, which precludes likely approaches to scaling
  Zcash"). [zips `draft-arya-dairaemma-disable-addition-of-transparent-chain-value.md`
  @ `c6b70358`]
- NU7 has regressed in rigor: ZIP 254 (Deployment of NU7) withdrawn, replaced by
  draft-arya-deploy-nu7 (heights TBD, empty ZIP list); the README's candidate list (218, 230,
  231, 233, 234, 235, 2002, 2003) is non-decisional and stale (names withdrawn ZIP 230); ZSA
  ZIPs 226/227 no longer listed; ZIP 228 was a Reserved stub at the cited
  snapshot and became Draft on 2026-08-04. [zips `README.rst:74–92`,
  `zip-0254.md` @ `c6b70358`]
- Other adjacent groundwork sits below spec rigor: draft-ecc-authenticated-reply-addrs is
  skeletal (Abstract/Motivation literally "TODO", blocked on ZIP 231 multi-part memos); ZIP 325
  (account metadata keys), ZIP 374 (PCZT), and ZIP 307 (light client) are all Draft. [zips
  @ `c6b70358`]

### 2.3 Open problems

- Consensus-grade specification of the Tachyon core does not exist: zero ZIPs or PRs upstream (a
  repo-wide grep finds only the ZIP-0 editor list, a protocol.tex affiliation, and one footnote
  citation); the five core ZIP stubs that would carry the shielded protocol, bundle, accumulator,
  aggregator, and OSS are empty. [zips @ `c6b70358`; gh searches 2026-07-08; tachyon
  `book/src/zips/` @ `26fdc165`]
- Wallet UX and recoverability after removing in-band secret distribution: Bowe — "Getting this
  right will be challenging, but we simply have no choice" (#22); "the user cannot rely on the
  blockchain as a storage mechanism for recovering their funds from a seed phrase" (2025-04-02);
  still non-committal on ZK388 (2026-01-21: infrastructure is "a can of worms like who runs
  it? … How do I get my funds?"). The entire current written resolution is one sentence in issue
  #121 (retain in-band for recover-from-seed), against which the book is flagged stale; the
  roadmap's alternative delivery path warns of "backup/recoverability trade-offs"; a forum
  seed-phrase question (2025-10-15) went unanswered. [forum t/50789 #22; ZK388 transcript;
  tachyon-zcash/tachyon#121]
- Correlation attacks by syncing services: the eprint states that timing-correlated unspent-proof
  updates linking transactions "is not a small problem; in fact, it would be fatal to the entire
  approach", and offers proof re-randomization by citation (BCMS, eprint 2020/499) without a
  construction or an argument that Ragu's PCD supports it with the required property; collusion
  of a service with network observers has no published analysis. [eprint 2025/2031 §1.3]
- Transport metadata privacy: no threat model, mixnet selection, or metadata-privacy design
  exists anywhere in the corpus; the sole gesture is "network privacy countermeasures like
  mixnets", once, in the founding post; ZIP 324 explicitly disclaims the channel. [blog
  2025-04-02; zips `zip-0324.rst` @ `c6b70358`]
- Data availability, liveness, and incentives: validators prune what wallets later need;
  "the sudden shutdown of these services could render the funds of all their dependent users
  unspendable, potentially permanently"; the DA-layer remedy is a three-paragraph sketch; Bowe:
  "it's not a concern of mine right now" (#22), a DA layer "would probably exist solely to
  incentivize replication" (#25); hanh's objection that wallets now bear the preservation burden
  stands unrebutted; no incentive design exists. [eprint 2025/2031 §1.4; forum t/50789 #22/#25]
- Epoch parameterization: the period the entire pruning model hinges on is untuned ("requires
  empirical analysis", issue #79); GGM depth D and arity A are nowhere fixed; the eprint ties the
  need for a DA layer directly to epoch length. [tachyon-zcash/tachyon#79; eprint 2025/2031 §1.4]
- Tip-nullifier exposure vs marketing: the site claims "the service never learns your actual
  nullifiers", but the delegation window includes "the nullifier of the epoch in progress at the
  span's tip" — the value a spend in that epoch would publish. A wallet can keep the leading edge
  private (UnspentSeed marked wallet-possible), but no document mandates the flow or analyzes the
  leak if it does not. [tachyon.z.cash/overview/; tachyon `book/src/{nullifiers,proof-tree}.md`
  @ `26fdc165`]
- Update-ZIP integration decisions: ZIP 221 (MMR leaf for a pool with no note commitment tree),
  ZIP 317 (fee contribution split across adjunct and aggregate), and ZIP 248 (bundle
  registration) each carry the designers' own "still under discussion and nothing has been
  decided yet" / "blocked on ZIP-248 reaching editor consensus". [tachyon
  `book/src/zips/zip-{221,317,248}.md` @ `26fdc165`]
- Ragu end-to-end viability: whether the linear-verifier PCD can reach the succinct sizes and
  verification performance Tachyon needs — final IPA/decider, proof compression, secure registry
  binding, permanent transcript, the three missing verifier checks, and any end-to-end soundness
  bound — is unresolved; the components either do not exist in code or are flagged FIXME, and
  deployment is gated on future "optimization and auditing". [ragu `crates/ragu_pcd/src/`
  @ `830bbcda`; tachyon.z.cash/roadmap/]
- Transparent-subset quantum recoverability (ZIP 2007) exists at issue rigor only: scoping in
  zcash/zips#1302 (open, 2026-06-17); the file exists only inside open PR #1319.
  [zcash/zips#1302]

## 3. Ragu status snapshot (tachyon-zcash/ragu @ `830bbcda`, 2026-07-05)

- In code: a no_std workspace (8 library crates, ~43.8k LOC, edition 2024, MSRV 1.90)
  implementing non-uniform PCD over the Pasta cycle — Step/Header application model,
  seed/fuse/rerandomize/verify, split-accumulation revdot claims, registry polynomial
  (verification-key-free non-uniform circuits), CycleFold-style nested circuits, Poseidon
  Fiat–Shamir — with a passing multi-node PCD-tree integration test.
- Not in code: succinct proofs (`Proof` carries full polynomials; no IPA/opening argument,
  decider, or compression anywhere), three verifier checks (TODO), a permanent Fiat–Shamir tag
  (`b"FIXME"`), secure registry binding (FIXME(security), 6 iterations), a protocol spec (all
  book protocol chapters todo), an audit, a benchmark publication, a release (0.0.0, no
  crates.io).
- Bimodal maturity: exceptional engineering hygiene (445 tests, 93.8 % coverage, 20 cron fuzz
  targets, Lean 4 FV of ~28 gadgets with Rust fingerprint-equivalence in CI, cargo-vet, zizmor,
  7/7 workflows green) around an explicitly pre-release cryptographic core.
- Downstream: the `zcash_tachyon` crate consumes ragu only through the `mock` feature (no-crypto
  API mock intended for early integration, pinned to a contributor fork) and registers 19 Steps;
  its proof layer is stubbed pending real ragu_pcd + Poseidon.

## 4. Verdict: what a tachyon-guide can be written from today

A guide is writable now only as a design-stage volume; nothing normative can be stated.

- Citable at full rigor: the environment and standing — NU7 poll result, editor affiliations,
  NU6.2/NU6.3 context (ZIP 257 Final; 229/258 Draft; 2005 Proposed), the ZIP 321/324 out-of-band
  substrate, and Ragu's code state at `830bbcda`. This supports a status-and-context chapter.
- Core-protocol chapters must be written from the book @ `26fdc165` as explicitly non-normative,
  commit-pinned, and dated: GGM nullifiers, dual-nullifier spends, two-epoch window, anchor
  chain, 19-step proof tree, delegation, aggregation. The material is single-committer, churning
  (open soundness/malleability issues), and self-admittedly stale against the PIR pivot; every
  out-of-band-era statement must be dated pre-2026-05-26.
- No performance figure may be stated as a project claim: the 100× and TPS numbers are analyst
  estimates; the only in-project numbers are self-labelled rough estimates. The April-2025
  "mainnet within a year" is falsified; the roadmap is dateless.
- The strongest writable content is the open-problems chapter, anchored on the three
  designer-acknowledged fatal-if-unsolved items — timing correlation ("fatal to the entire
  approach"), DA/liveness ("unspendable, potentially permanently"), recoverability (one sentence
  in issue #121) — plus epoch parameterization, tip-nullifier exposure, and the undecided
  update-ZIP integrations.
- Not writable: byte formats, consensus rules, security theorems, benchmarks, audit posture.
  Revisit triggers: ZIP 248 merge; upstreaming of fork PRs #1–#4; first Ragu benchmark or audit
  publication; a published PIR payment-protocol spec; filling of core ZIP stubs #103–#107.
