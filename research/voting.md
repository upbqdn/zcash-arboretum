# Shielded voting ("Zally"): identification and mechanism inventory

Ground truth (local clones, hashes recorded): valargroup/voting-circuits `4c39abd5` (2026-06-03,
`/home/m/zcash/voting-circuits`), valargroup/zcash_voting `624cf198` (2026-06-07),
valargroup/vote-sdk `cb915f51` (2026-06-05), valargroup/vote-nullifier-pir `603e4e3b`,
valargroup/spendability-pir `a924008d`, zashi-android `b4edd6f6`, zashi-ios `8ab0e6ed`,
zcash-android-wallet-sdk `f386369e`, zcash/orchard (feature commit `c0b6b917`), prior art
hhanh00/zcash-vote `f05f5f25`. Web sources and `gh` PR statuses checked 2026-07-08. Method per
`CONVENTIONS.org`: firsthand verification, three-bin classification (specified /
designed-but-unspecified / open problem). Every formula and constant below was read from source,
not from designer prose. This is a historical May--July 2026 inventory,
not a statement about the current deployment. Corrections below were
checked against the same source objects on 2026-09-05.

## 1. What the protocol is

**Name.** Internally "Zally" (the "Zally governance protocol", per the zcash_voting README);
publicly the **Shielded Voting Protocol** (draft ZIP `draft-valargroup-shielded-voting.md`,
"Shielded Vote" docs); shipped as the product feature **Coinholder Polling**.

**Designers.** Valar Group, led by Dev Ojha (GitHub ValarDragon; Osmosis co-founder, now on Zcash
scaling/PQ). Draft ZIP authored by GitHub user p0mvn (Valar Group, ex-Osmosis Labs). The upstream
orchard `unstable-voting-circuits` feature was contributed by Adam Tucker
(zcash/orchard `c0b6b917`, 2026-04-23). Architecture reviewed — not designed — in Q1 2026 by ZODL
engineers str4d (Jack Grigg), Daira-Emma Hopwood, and Kris Nuttycombe (ZODL retroactive grant
application, ZcashCoinholderGrantsProgram issue #33). Wallet integration by ZODL (ex-Zashi/ECC).

**Shipped.** Zodl (the wallet formerly Zashi; team left ECC January 2026, package id unchanged)
version 3.5.0, Android and iOS, 2026-05-28 (`/home/m/zcash/zashi-android/CHANGELOG.md`); hardening
in 3.5.2 (2026-06-04). Keystone hardware-wallet signing supported. The intended
NU7 sentiment poll was paused on 2026-06-07 before opening; no completed
production poll is established in this snapshot. See the dated announcement
and pause evidence in `parked/voting-guide.tex`, “What shipped”.

**What it does.** Coin-weighted private polling over the Orchard shielded pool without moving
funds. A round pins a Zcash snapshot (note-commitment root + nullifier-set root); holders prove
control of unspent-at-snapshot notes and delegate quantized weight (1 ballot = 0.125 ZEC) to a
governance hotkey; the hotkey casts votes as ElGamal-encrypted split shares on a dedicated
permissioned Cosmos SDK chain (`svoted`); relayers reveal shares with timing decorrelation; a
per-round threshold Election Authority (validator DKG) publishes aggregate
decryptions. A threshold coalition can also decrypt individual ciphertexts.

**Lineage.** Independent of hhanh00/zcash-vote (the 2024 dev-fund poll and the Apr–May 2025
lockbox poll; ZIP PR #853, open since 2024-05-28) — zero cross-references in either codebase. Both
share the snapshot + per-election-nullifier idea; Zally adds hotkey delegation (Vote Authority
Notes), split ElGamal shares, a DKG threshold authority, relayers, PIR-private eligibility
queries, a dedicated chain, and hardware signing, and is wallet-native rather than a separate app.
Distinct from ZCAP (identified panel, Helios, no coin weighting; the intended
June 2026 poll through both mechanisms was paused) and from Hopwood's
`draft-ecc-onchain-accountable-voting.md` (accountable on-chain
voting by identified key-holders — the accountability-focused complement, no design lineage).

## 2. Sources

### Primary (code — the de facto specification)

- **valargroup/voting-circuits @ `4c39abd5`** — the three Halo2/IPA circuits over Pallas, reusing
  Orchard chips: delegation (`src/delegation/circuit.rs`, K=14, 14 public inputs, 14 conditions),
  vote proof (`src/vote_proof/circuit.rs`, K=13, 11 public inputs, 12 conditions), share reveal
  (`src/share_reveal/circuit.rs`, K=11, 9 public inputs, 5 conditions). Domain-tag registry
  `src/domain_tags.rs`; constants `src/params.rs`; IMT non-membership `src/delegation/imt.rs`;
  soundness caveats `src/delegation/README.md` §8. The same crate proves (wallet) and verifies
  (chain FFI). Matching versions share a relation implementation; this does
  not rule out version/configuration drift or provide independent validation.
- **valargroup/vote-sdk @ `cb915f51`** — the Shielded Vote Chain: tx surface
  `proto/svote/v1/tx.proto`; ZKP+RedPallas validation `x/vote/ante/validate.go`; nullifier sets
  and Poseidon tree `x/vote/keeper/keeper_voting.go`; DKG `keeper_ceremony.go`,
  `crypto/shamir/*`, `crypto/elgamal/*`; tally `keeper_tally.go`, `msg_server_tally_decrypt.go`;
  embedded helper (relayer) `internal/helper/*`; snapshot derivation `api/snapshot.go`,
  `circuits/src/nc_root.rs`.
- **valargroup/zcash_voting @ `624cf198`** — client library: lifecycle, note bundling, hotkey
  derivation (`hotkey.rs`), share scheduling (`share_policy.rs`), secrecy-annotated payload types
  (`types.rs`), SQLite persistence and crash recovery.
- **valargroup/{vote-nullifier-pir @ `603e4e3b`, spendability-pir @ `a924008d`}** — single-server
  PIR (SimplePIR/YPIR) for private nullifier non-membership and spendability/witness queries.
- **Wallet integration** — zashi-android `b4edd6f6` (`.../provider/VotingApiProvider.kt`,
  `model/voting/{StaticVotingConfig,RoundAuthenticator,TallyResults}.kt`); zashi-ios `8ab0e6ed`;
  zcash-android-wallet-sdk `f386369e` (JNI over `zcash_voting =0.11.0`, orchard `=0.14.0` with
  `unstable-voting-circuits`).
- **Prior art** — hhanh00/zcash-vote @ `f05f5f25` (`src/election.rs`; depends on hhanh00/orchard
  fork rev `75448e67`, feature `vote`).

### Design-stage documents (none normative)

- **zcash/zips PR #1200** "[ZIP TBD] Shielded Voting Protocol" (p0mvn, opened 2026-03-05) —
  OPEN/unmerged as of 2026-07-08, last update 2026-06-02; reviewer-flagged "Underspecified"
  sections; absent from the merged zips tree.
- **zcash/zips PR #1198** (PIR for nullifier exclusion) — OPEN. **PR #853** (hhanh00 coin voting,
  prior art) — OPEN since 2024-05-28.
- **valargroup.gitbook.io/shielded-vote-docs** (fetched 2026-07-08) — prose; ZKP1/ZKP2/ZKP3 pages
  list public/private inputs and some Poseidon preimages, but omit the governance-nullifier, VAN-
  nullifier, and share-nullifier formulas, the nullifier-domain derivation, the bitmask width, and
  the IMT leaf model; misstates the ballot rule (§4, open problem).
- **valargroup/shielded-vote-book** and mirror z-cale/shielded-vote-book — design book, PRIVATE
  (404 to anonymous access, verified 2026-07-08).
- **Deployment config** — valargroup/token-holder-voting-config @ `2785311d`, SHA-256-pinned in
  the wallet (`StaticVotingConfig.kt`).

## 3. Mechanism

Poseidon throughout is P128Pow5T3 (width 3, rate 2); domain tags are zero-padded ASCII Pallas
field elements pinned by unit tests (`voting-circuits/src/domain_tags.rs`).

### 3.1 On-chain objects

A round exposes five messages (`vote-sdk/proto/svote/v1/tx.proto:32-120`): `MsgDelegateVote` {rk,
spend_auth_sig, signed_note_nullifier, cmx_new, van_cmx, gov_nullifiers[≤5], proof, vote_round_id,
sighash}; `MsgCastVote` {van_nullifier, vote_authority_note_new, vote_commitment, proposal_id,
proof, vote_round_id, anchor_height, vote_auth_sig, r_vpk}; `MsgRevealShare` {share_nullifier,
enc_share (64-byte ElGamal C1‖C2), proposal_id, vote_decision, proof, vote_round_id,
anchor_height}; coordinator `MsgCreateVotingSession`; proposer-only `MsgSubmitTally`. Vote
transactions bypass the Cosmos Tx envelope; authentication is ZKP + RedPallas
(`x/vote/ante/validate.go`).

### 3.2 Weight and snapshot (ZKP1, delegation)

The delegation circuit takes bundles of up to 5 Orchard notes and proves, per note: NoteCommit
integrity; Sinsemilla Merkle membership of cmx under the public `nc_root` (value-0 padding notes
skip via gate v·(root−anchor)=0); address ownership pk_d = [ivk]g_d with an in-circuit
external/internal-scope mux; in-circuit derivation of the real Orchard nullifier (never
published); and non-membership of that nullifier in a Poseidon indexed Merkle tree (depth 29,
punctured-range leaves Poseidon(nf_lo, nf_mid, nf_hi)) under the public `nf_imt_root` — existed
and unspent at snapshot (`voting-circuits/src/delegation/circuit.rs:1497-1805`,
`src/delegation/imt.rs`). The Orchard primitives are reused via orchard's
`unstable-voting-circuits` feature, which widens circuit internals (note_commit, derive_nullifier,
CommitIvk chips).

Weight quantizes at 12,500,000 zatoshi per ballot (`src/params.rs`). Condition 8 constrains
num_ballots·12,500,000 + remainder = v_total with remainder < 2²⁴ and 1 ≤ num_ballots ≤ 2³⁰ —
strictly weaker than floor division; see §4 (open problem).

Snapshot anchors (`nc_root` recomputed from a lightwalletd Orchard frontier;
`nullifier_imt_root` from the valargroup PIR service) are posted in `MsgCreateVotingSession` by a
threshold-gated coordinator; the chain performs no verification that they match real Zcash state
(no light client). Honest wallets' proofs fail against wrong roots and anyone can audit post hoc,
but a coordinator quorum could pin a fabricated snapshot (`vote-sdk/api/snapshot.go:24-60`,
`x/vote/keeper/msg_server.go:30-100`).

### 3.3 Delegation output: the Vote Authority Note

The VAN is a two-layer Poseidon commitment van_comm = Poseidon(Poseidon(DOMAIN_VAN=0, g_d_x,
pk_d_x, num_ballots, vote_round_id, proposal_authority), van_comm_rand) over the hotkey's
diversified-address x-coordinates, ballot count, round id, a 16-bit proposal-authority bitmask
(65535 at mint), and a blinding factor; one gadget is shared by ZKP1 (create) and ZKP2 (open)
(`voting-circuits/src/gadgets/van_integrity.rs`). The x-only encoding
identifies neither point's sign. Delegation separately binds the full points
via NoteCommit into cmx_new, as the module docs note; this observation alone
is not a proof that every consumer of the VAN preserves the intended binding.

Authorization: a spend-auth signature over a synthetic 1-zatoshi Orchard action that never touches
Zcash. The keystone note's rho is forced to Poseidon(cmx_1..5, van_comm, vote_round_id)
(condition 3); its nullifier and rk = [α]G + ak are public inputs; a Keystone hardware wallet or
the software wallet signs the ZIP-244 sighash from a Governance PCZT. The chain verifies the
RedPallas signature over the *client-provided* 32-byte sighash without
recomputing it. Contrary to this note's earlier assurance, the proof's rho
chain does not establish that this digest commits to the delegation: the
chain receives no wrapping transaction, and the fourteen proof inputs have
no sighash. `circuits/tests/generate_fixtures.rs` explicitly signs arbitrary
32 bytes. The message-binding argument is unestablished at these pins; this
review has not demonstrated a live exploit. Governance-nullifier uniqueness
guards replay, a separate property (`src/delegation/circuit.rs:1129-1173`;
`vote-sdk/x/vote/ante/validate.go`, `verifyDelegation`).

The hotkey is app-generated, not seed-derived: a random 64-byte secret in platform secure storage
derives an Orchard SpendingKey (ZIP-32 account 0, index 0). Hotkey compromise loses vote authority
for the round, never funds (`zcash_voting/src/hotkey.rs`).

### 3.4 Double-vote prevention (layered)

1. **Per-round governance nullifiers.** Each delegated note exposes gov_null = Poseidon(nk, dom,
   real_nf) with dom = Poseidon("governance authorization", vote_round_id) enforced in-circuit
   from the public round id; the chain rejects duplicates in a (Gov, round)-scoped set. Keyed by
   nk, the value stays unlinkable to the real Orchard nullifier even after a later mainnet spend
   (`src/delegation/circuit.rs:1024-1055,1703-1729`;
   `vote-sdk/x/vote/keeper/keeper_voting.go:14-63`).
2. **VAN nullifier.** Spending a VAN publishes van_nullifier = Poseidon(vsk_nk, "vote authority
   spend", voting_round_id, VAN_old), round-scoped (`src/vote_proof/circuit.rs:123-143`).
3. **Bitmask decrement.** Each vote consumes one bit: ZKP2 condition 6 proves authority_new =
   authority_old − 2^proposal_id via a lookup table, proposal_id ∈ [1,15] (bit 0 is a permanent
   sentinel); the successor VAN re-enters the tree. One delegation → at most one vote per
   proposal, ≤15 proposals per round (`src/vote_proof/circuit.rs:199-222`).
4. **Share nullifiers.** Revealing a share publishes Poseidon("share spend", vote_commitment,
   share_index, blind); the blind keeps it underivable from public data
   (`src/share_reveal/circuit.rs:156-187`).

### 3.5 Vote encoding and casting (ZKP2)

The vote splits into 16 lifted-ElGamal ciphertexts over Pallas (Orchard SpendAuthG generator):
C1_i = [r_i]G, C2_i = [v_i]G + [r_i]·ea_pk, with sum(shares) = the VAN's ballot count
(condition 8) and each share ∈ [0, 2³⁰) (condition 9) (`src/gadgets/elgamal.rs`,
`src/vote_proof/circuit.rs:416-457`). The commitment is vote_commitment = Poseidon(DOMAIN_VC=1,
voting_round_id, shares_hash, proposal_id, vote_decision) with shares_hash =
Poseidon(share_comm_0..15) and share_comm_i = Poseidon(blind_i, c1_x, c2_x, c1_y, c2_y) —
y-coordinates included to block ciphertext sign-malleability (`src/gadgets/vote_commitment.rs`,
`src/shares_hash.rs`). ZKP2 proves hotkey control via the CommitIvk chain and a randomized key
r_vpk = ak + [α_v]G that signs a Blake2b-256 sighash the chain *recomputes*
(`vote-sdk/x/vote/ante/validate.go:188-201`).

The vote-chain tree is one shared per-round Poseidon Merkle tree, depth 24: delegation appends
van_cmx; casting appends the successor VAN then the vote commitment. Anchor-height→root binding
lives in the chain lookup, not the circuits (`vote-sdk/x/vote/keeper/msg_server.go:149-210`).

### 3.6 Share reveal and relayers (ZKP3)

The wallet POSTs a SharePayload {shares_hash, proposal_id, vote_decision, enc_share,
tree_position, all_enc_shares, share_comms, primary_blind, submit_at} to
`/shielded-vote/v1/shares` on ⌈n/2⌉ of the configured vote servers, each with an independently
random future submit_at (last-moment buffer = min(2/5 of round remainder, 6 h)). The helper —
embedded in the svoted node — stores it, waits, builds the Merkle path and the ZKP3 proof
*server-side*, and submits `MsgRevealShare` (`zcash_voting/src/types.rs:375-498`,
`src/share_policy.rs`; `vote-sdk/internal/helper/*`). Consequence: helpers are trusted with
decision privacy and the share→vote-commitment linkage (they receive tree_position and the primary
blind), but never with weight — plaintext values and ElGamal randomness are marked SECRET and
withheld. Timing decorrelation is client policy, not a protocol guarantee; a censoring helper
causes partial weight loss, mitigated by multi-server submission and a single-share last-moment
mode (share 0 carries all weight).

### 3.7 Election Authority and tally

Each round runs a Joint-Feldman DKG among bonded validators with registered Pallas keys:
reconstruction threshold t = max(2, ⌊(2n+2)/3⌋), ECIES/ChaCha20-Poly1305-encrypted shares,
Feldman commitments on-chain, finalization quorum ⌈4n/5⌉, jailing for non-participation
(`vote-sdk/x/vote/keeper/keeper_ceremony.go`, `crypto/shamir/*`, `crypto/ecies/ecies.go`).
Ciphertexts accumulate homomorphically per (round, proposal, decision); in TALLYING each validator
auto-injects partial decryptions D_i = share_i·C1 with Chaum–Pedersen DLEQ proofs checked against
Feldman-derived verification keys; the proposer's `MsgSubmitTally` totals are verified on-chain by
Lagrange combination plus a completeness check before finalization. Aggregate discrete logs are
recovered by BSGS with exclusive bound 2²⁸ ballots (`crypto/elgamal/bsgs.go`;
`keeper/msg_server_tally_decrypt.go:76-298`). A 6-hour tally timeout finalizes the round *without*
results. Totals are denominated in **ballots**; the proto comment saying "zatoshi" is wrong — the
wallet multiplies by 12,500,000 (`proto/svote/v1/tx.proto:111-116` vs
`zashi-android/.../TallyResults.kt:44-56`).

### 3.8 What an observer learns; trust assumptions

Per phase: delegation reveals van_cmx, ≤5 gov nullifiers (always 5 slots, padded), rk, nf_signed,
cmx_new — ballot count hidden in the blinded VAN. A cast vote reveals van_nullifier, the successor
VAN, the vote commitment, and proposal_id — not the decision; note that `MsgCastVote` publicly
links vote_commitment ↔ van_nullifier, so per-vote weight privacy rests on the ElGamal encryption,
not unlinkability. A share reveal shows decision, one ciphertext, and a share nullifier, on-chain
unlinkable to any vote commitment (ZKP3 membership without leaf identification). Only aggregate
(proposal, decision) ballot totals become public.

**Threshold-collusion limit.** Any t colluding validators can reconstruct the round key and
decrypt individual on-chain enc_shares offline. If they additionally obtain
the share-to-vote grouping, for example from a helper, summing the 16 shares yields that vote's
exact per-decision weight, already publicly linked to a van_nullifier. Linkage still stops at the
VAN layer — Zcash notes and addresses stay behind the gov-nullifier PRF. Neither gitbook nor code
claims per-vote weight privacy against an EA threshold; the property is absent from published
analysis (adversarial inference from `crypto/elgamal/bsgs.go`, `tx.proto:88-99`, ZKP2
condition 9).

**Other assumptions.** The chain is permissioned end-to-end: bank transfers disabled, validators
join only via a whitelisted Pallas-key path, round lifecycle is threshold coordinator action,
tally is proposer-only (`vote-sdk/app/ante_whitelist.go`, `proto/svote/v1/tx.proto:199-246`).
Wallet-side round authentication rests on a SHA-256-pinned static config whose ed25519 keys sign
the dynamic config (vote servers, PIR endpoints, per-round ea_pk; mismatch → EA_PK_MISMATCH) plus
an on-chain endorsement registry — trust root = config-signing keys + app distribution
(`zashi-android/.../StaticVotingConfig.kt:50-62`, `RoundAuthenticator.kt`). Client eligibility
checks use single-server PIR so the wallet never reveals which notes/nullifiers it holds
(`vote-nullifier-pir/README.md`; zips PR #1198).

## 4. Claim inventory (three bins)

**Specified.** Only inherited primitives: NoteCommit, DeriveNullifier, CommitIvk, the Sinsemilla
Merkle instance, RedPallas, ZIP-244 sighash, ZIP-32 derivation — specified in protocol.tex/ZIPs
and reused via orchard `unstable-voting-circuits` (`c0b6b917`). No governance-specific object has
ZIP-rigor specification.

**Designed-but-unspecified** (implementation concrete and open-source; would-be spec zips PR #1200
OPEN; design book private): the five-message ballot structure (§3.1); ZKP1 note-bundle eligibility
and IMT non-membership (§3.2); coordinator-posted, chain-unverified snapshot roots (§3.2); the VAN
construction and synthetic-keystone authorization with client-provided sighash (§3.3); all four
double-vote layers (§3.4); 16-share lifted ElGamal, vote commitment, bitmask decrement (§3.5);
helper-mediated share reveal and its trust grant (§3.6); per-round Joint-Feldman DKG,
chain-verified tally, BSGS bound, tally timeout, ballots-vs-zatoshi proto-comment error (§3.7);
observer model, threshold-collusion limit, permissioned-chain and wallet-config trust roots, PIR
subsystem (§3.8); circuit sizing (K=14/13/11, Halo2/IPA over Pallas, single shared
prover/verifier crate). Prior art hhanh00/zcash-vote also bins here (PR #853 OPEN).

**Open problems.** First, the ballot-quantization soundness gap. The circuit relation
(remainder < 2²⁴ > 12,500,000) admits a one-ballot *under*-claim witness for ~34% of v_total
values (over-claim impossible), while the public gitbook states exact floor division —
a concrete spec-versus-code disagreement, conservative in direction; tightening approaches are
listed but unimplemented (`voting-circuits/src/delegation/circuit.rs:1290-1427`,
`src/delegation/README.md` §8, gitbook ZKP1 page). Second, the unestablished
binding between the signed delegation digest and accepted proof fields (§3.3).

## 5. Verdict for a formal voting guide

**Statable at spec rigor today: nothing protocol-specific.** Every governance object — VAN,
governance nullifier, vote commitment, share nullifier, DKG parameters, tally rules — is
implementation-defined; the citable artifacts are the commit-pinned sources above, and any
formal write-up must present the formulas of §3 as *from code*, with the caveat that the single
voting-circuits crate is both prover and verifier (internally consistent, no independent
implementation, no merged ZIP: PRs #1200, #1198, #853 all OPEN as of 2026-07-08).

**Statable as deployed fact:** the feature shipped (Zodl 3.5.0, 2026-05-28),
but its intended NU7 poll was paused; the inherited Orchard primitives it composes are individually
specified.

**Must be flagged:** the delegation digest/proof binding (§3.3); the
ballot-rule gitbook/code disagreement (§4); the proto tally-units
comment error (§3.7); the unanalyzed threshold-collusion weight-privacy limit (§3.8); the
coordinator-trusted snapshot with no chain-side verification (§3.2); helpers trusted with vote
decisions and linkage, beyond what "timing hiding" suggests (§3.6); the permissioned validator
set, wallet-vendor config trust root, and the tally-timeout no-result path.

**Not verified in this pass:** no proofs generated or verified locally; production
validator/coordinator identities not established from public data (would need the deployed chain's
genesis or valargroup announcements). Residual leads: `vote-sdk/audit/`, the `wallet-example`
crate (end-to-end flow), `keeper_pallas_registry.go` (validator key rotation).
