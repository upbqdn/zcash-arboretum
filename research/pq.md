# Post-quantum assumption inventory: Orchard

Ground truth: zips `c6b70358` (2026-07-05), orchard `bef8a27e` (v0.14.0 + Ironwood API,
2026-06-16), halo2 `261faacc`, librustzcash `62ee526f`. Method per `CONVENTIONS.org`: firsthand
verification, recorded hashes, classification specified / designed-unspecified / open-problem.
Protocol.tex line numbers are at the zips commit above; section labels are version-stable.

## 1. Per-primitive assumption table

| Primitive | Construction | Assumption | Quantum consequence | Reversibility | Migration path | Refs |
|---|---|---|---|---|---|---|
| Sinsemilla (MerkleCRH, NoteCommit, CommitIvk) | Accumulator over Pallas, 10-bit pieces, incomplete addition, `Extract_P` x-coordinate output; commitments add a Pedersen randomizer term | Collision resistance tightly reduced to Pallas DLP (vector-Pedersen correspondence); not PQ collision-resistant, not collapsing, commitments not PQ-binding (ZIP 2005) | Shor gives dlog relations among bases: non-unique NoteCommit openings (forge second note, break Balance); fake Merkle paths; alternative (ak', nk') for one ivk — Faerie Gold / roadblock Spendability attacks. Pre-switch-off balance violations may go undetected (ZIP 209 turnstile only bound) | prospective | SPECIFIED (ZIP 2005, NU6.3): 0x03 notes derive rcm and rivk_ext through BLAKE2b so a future Recovery Statement makes the composite PQ-binding; tree re-hashed with a collapsing hash. Recovery Statement itself DESIGNED-UNSPECIFIED. Pre-Ironwood (0x02), Sapling, Sprout notes irrecoverable | [P1] |
| Pedersen value commitment + binding sig (bsk/bvk) | `cv = [v]V + [rcv]R`; validators check `bvk = Σcv − ValueCommit_0(v_balance)`; RedPallas bindingSig over ZIP-244 SigHash | Binding = unknown dlog relation V/R (Pallas DLP); sig EUF-CMA = DLP in ROM (BLAKE2b-512). Hiding unconditional | Shor gives `dlog_V(R)`: reopen any cv to any value, compute bsk from bvk, forge binding sigs — silent arbitrary inflation (turnstile-bounded). No retroactive leakage: hiding is unconditional | prospective | OPEN-PROBLEM: ZIP 2005 deliberately leaves cv/bindingSig unchanged; PQ balance rides on a future PQ proof system (unchosen). Mitigation: switch legacy pools off before a CRQC | [P2] |
| RedPallas SpendAuthSig + re-randomization | RedDSA on Pallas, BLAKE2b-512 hash-to-scalar; per Action `rsk = ask + α`, `rk = ak + [α]G`, circuit proves the re-randomization | EUF-CMA under Pallas DLP in ROM; rk unlinkability information-theoretic (α uniform) | Shor computes dlog(rk): spend-auth forgeable at will → with forged proofs, full note theft. NOT retroactive: α perfectly masks ask; recorded sigs leak no key linkage even to a quantum adversary | prospective | SPECIFIED-IN-DRAFT: ZIP 2005 re-anchors spend authority in the hash chain (SoK^sk with BindKeys^sk; qsk/qk path for FROST/hardware). A deployed PQ signature for ongoing spends is OPEN-PROBLEM (zips#1134; no ML-DSA/SLH-DSA text anywhere in zips) | [P3] |
| Halo 2 IPA / Action proof soundness | PLONKish over Vesta; modified Bulletproofs IPA (Pedersen vector commitments, recursive amortization, no trusted setup); Fiat–Shamir via BLAKE2b | Knowledge soundness under Vesta DLP + FS in ROM; not PQ-sound. Zero-knowledge is perfect (unconditional) | Forge proofs of arbitrary false Action statements: mint from nothing, spend any commitment, indistinguishable from honest. The single most concentrated failure point. Recorded proofs never leak witnesses | prospective | OPEN-PROBLEM by design: ZIP 2005 requires assuming no particular PQ proof system; Recovery Statement needs one able to check ~7 BLAKE2b compressions + Sinsemilla + 2 scalar muls + Merkle path. Successor stack (Ragu/Tachyon) is deliberately ECDLP-based | [P4] |
| Note encryption: KA^Orchard DH + KDF + AEAD | `esk` from rseed; `epk = [esk]g_d`; sharedSecret = `[esk]pk_d`; BLAKE2b-256 KDF; ChaCha20-Poly1305; ock path for ovk | DH hardness on Pallas (only DL-dependent link); BLAKE2b as PRF/RO; symmetric layers quantum-resistant up to Grover | RETROACTIVE — canonical HNDL target. With chain + recipient address, Shor gives `ivk = dlog(pk_d)`: decrypt every past and future ciphertext to that address (amounts, memos, full receiving history). No spend authority conferred; without the address, unconditional hiding + ZK keep the chain private | **retroactive** | OPEN-PROBLEM: nothing deployed or specified; ZIP 2005 excludes privacy (Non-requirement). Tracking zips#1133/#1134 only; zero ML-KEM/Kyber/lattice text in zips. Recorded ciphertexts unrepairable by construction; hybrid KEM / Tachyon oblivious sync would help future outputs only | [P5] |
| PRFexpand and other BLAKE2b uses | `BLAKE2b-512("Zcash_ExpandSeed", sk‖t)` with a domain-byte registry ([4] esk … [0x83] internal rivk; ZIP 2005 adds [0x0B], [0x0D]); BLAKE2b-256 KDF/ock; BLAKE2b-512 in RedDSA and ZIP-244 | BLAKE2b keyed PRF + collision resistance; for PQ, compression function modelled as RO, collapsing via HAIFA (Fehr 2018); QROM bound O(q³/r_P) ≈ 2⁻⁷⁴ worst / 2⁻¹³⁴ practical; rivk dual-use caveat needs a joint assumption | No expected break: Grover halves preimage security (~128 bits, acceptable); secrets never on-chain. Residual risk: if the collapsing modelling failed, ZIP 2005's recoverability theorems lose their foundation | prospective | None needed — this is what everything migrates TO. Recovery Statement re-executes the derivations in-circuit; SPECIFIED at ZIP rigor with the QROM lift argued | [P6] |
| Poseidon (PRF^nfOrchard, nullifiers) | Permutation over F_q³ (x⁵, 8 full + 56 partial rounds), CIL sponge; `nf = Extract_P([(PRF_nk(ρ)+ψ) mod q]K + cm)` | Heuristic: Poseidon keyed by first input is a PRF (no standard-problem reduction); outer map leans on DL structure and ψ/ρ uniqueness for Faerie-Gold resistance | Poseidon itself: generic speedups only; nk never on-chain, so recorded nullifiers stay unlinkable. The composite bites under a DL break: grind (ψ, rcm) to make distinct notes share a nullifier/commitment — Spendability attacks in the critical exposure period can permanently block recovery | prospective | SPECIFIED-IN-DRAFT: Recovery Statement recomputes DeriveNullifier with ψ forced to H^ψ(ρ); Ironwood nullifier set disjoint from legacy Orchard. Poseidon carries into PQ only as a PRF — binding rests on BLAKE2b; collapsing for Poseidon not needed, not claimed | [P7] |
| ZIP 32 Orchard key tree | Hardened-only: master from BLAKE2b-512("ZcashIP32Orchard", seed); CKDh via PRFexpand [0x81]; internal rivk via [0x83]. No EC operation anywhere in the path | Purely symmetric: BLAKE2b as PRF keyed by chain code; needs ≥256-bit seed entropy | None from Shor — the tree survives a DL break intact; Grover infeasible vs full-entropy seeds. Deterministic derivations mean a seed holder retains provable ownership post-transition — exactly what BindKeys^sk exploits | prospective | Retained as-is; root of the recovery story (part of why Orchard, not Sapling, was protected). Non-seed keys (FROST DKG, hardware) get the qsk/qk mechanism (BLAKE3, ZIP 312 integration planned) — SPECIFIED-IN-DRAFT | [P8] |

Refs (protocol.tex at zips `c6b70358`; source at orchard `bef8a27e`):

- [P1] {concretesinsemillahash} L9471, {sinsemillasecurity} L9591, {orchardmerklecrh} L9045,
  {concretesinsemillacommit} L11020; ZIP 2005 L101–117, L1109–1155.
  `src/note/commitment.rs:61`, `src/spec.rs:212-225`, `src/tree.rs:231`.
- [P2] {concretehomomorphiccommit} L10922, {orchardbalance} L7084, {concretebindingsig} L10776;
  ZIP 2005 L1870–1913. `src/value.rs:352-371,309,373-376`, `src/primitives/redpallas.rs`.
- [P3] {spendauthsig} L7256, {concretereddsa} L10516, {concretespendauthsig} L10744,
  {orchardkeycomponents} L5639; ZIP 2005 L968–1061. `src/primitives/redpallas.rs`,
  `src/keys.rs:127`, `src/action.rs`.
- [P4] {halo2} L12255, {actionstatement} L7824, {orchardbalance} L7084ff; ZIP 257 (Final);
  ZIP 2005 L1063–1098, L1106–1108, L1986–2028. `halo2_proofs/src/poly/commitment.rs`,
  `src/circuit.rs`.
- [P5] {concreteorchardkeyagreement} L10317, {concreteorchardkdf} L10349, {orchardsend} L6356ff,
  {concretesym} L10129; ZIP 2005 L1947–1952. `src/note.rs:116`, `src/keys.rs:797-830`,
  `src/note_encryption.rs:141-254`.
- [P6] {abstractprfs} L4482 (registry L4543), {concreteprfs} L10010, {orchardkeycomponents}
  pnote; ZIP 2005 L1765–1868. `src/spec.rs:23`, `src/keys.rs:127,244,280,360-373`,
  `src/note.rs:116,134`.
- [P7] {poseidonhash} L9750, {concreteprfs} L10103–10126, {rhoandnullifiers} L7387–7395;
  ZIP 2005 L1959–1984. `src/note/nullifier.rs:72-81`, `src/spec.rs`.
- [P8] zip-0032.rst (Final) L423–467, L472–530, L175–184; ZIP 2005 L126–132. `src/zip32.rs`,
  `src/keys.rs:110`.

## 2. ZIP 2005 "Ironwood Quantum Recoverability"

**Status.** Proposed (`zips/zip-2005.md:9`, verified 2026-07-08 against zips.z.cash). Owners
Hopwood, Grigg; created 2025-03-31; discussion zcash/zips#1135. Deployment bound to NU6.3
(ZIP 258, Draft, branch ID `0x37A5165B`; Testnet activation 4134000; Mainnet
activation 3428143, added to the ZIP after this memo's original 2026-07-08
snapshot). NU6.3 introduces the Ironwood pool (v6 transactions, ZIP 229 Draft)
running Orchard with the updated Action circuit; the legacy Orchard pool becomes
spend-only with cross-address transfers disabled.

**Mechanism.** For every Ironwood output (lead byte 0x03), rcm is derived as
`ToScalar(PRFexpand_rseed([0x0B] ‖ g_d* ‖ pk_d* ‖ v ‖ ρ ‖ ψ))` — all note fields pass through
BLAKE2b, so under collapsing (HAIFA compression as RO, Unruh/Fehr) no field can vary without
changing rcm; the composite NoteCommit becomes PQ-binding once a Recovery Protocol checks the
derivation. The same trick binds CommitIvk: rivk comes from `H^rivk_legacy(sk)` or, for FROST
DKG/hardware wallets, from `H^rivk_ext_qk(ak, nk)` under a quantum key `qk = H^qk(qsk)` (one
BLAKE3 compression), with SoK^sk/SoK^qsk signatures of knowledge over SigHash. The non-normative
Recovery Statement then proves, in a to-be-chosen PQ knowledge-sound system over a re-hashed
(collapsing-hash) tree: BindKeys, the rivk branch, ivk = CommitIvk, pk_d = [ivk]g_d, the ψ/rcm
derivations, cm, a Merkle path, and nf — cost ≈ 7 BLAKE2b-512 compressions + 1 BLAKE3 +
2 Sinsemilla commits + 2 Pallas scalar muls + Merkle path. Security: classical-ROM key-binding
and Spendability theorems with an explicit QROM lift (straight-line, compressed-oracle bounds
O(q³/r_P) ≈ 2⁻⁷⁴ worst, ≈ 2⁻¹³⁴ practical). Wallets SHOULD sweep transparent/Sprout/Sapling/
legacy-Orchard funds into Ironwood.

**Gaps (stated in the ZIP).**

1. Sapling gets no equivalent; Sapling, Sprout, and pre-Ironwood Orchard (0x02) notes are
   unrecoverable — permanently unspendable once legacy protocols switch off. Migration is the
   only remedy.
2. Privacy is a Non-requirement: HNDL against note encryption remains for all pools including
   Ironwood; mitigations only "under consideration".
3. Transparent ECDSA is out of scope.
4. The Recovery Protocol itself is designed-unspecified ("details … subject to change"); no PQ
   proof system or tree hash is chosen (a stated Requirement).
5. Everything hinges on switching legacy pools off before a CRQC; attacks in the critical
   exposure period (Spendability/roadblock, spend-auth theft, turnstile-bounded inflation) are
   not repaired retroactively.
6. qsk/SoK instantiation and inter-circuit linking commitments remain open.

## 3. Other PQ-relevant drafts and artifacts

- ZIP 258 (Draft, 2026-06-19): NU6.3 deployment, Orchard-pool sealing rules.
- ZIP 229 (Draft): v6 transaction format carrying Ironwood.
- ZIP 257 (Final): NU6.2 circuit correction after the 2026-05-29 Action-circuit soundness bug
  (Hornby, GHSA-ww9q-8r59-xv46; emergency Orchard disable at height 3363426). Not quantum, but
  the reason ZIP 2005 deployment slipped to NU6.3, and evidence that proof soundness has a live
  implementation-correctness component.
- ZIP 2006 "Restricting Transfers to the Orchard Pool": Status Reserved, empty placeholder.
- ZIP 32 (Final) hardened-only Orchard derivation explicitly motivated by PQ analysis and
  ZIP 2005 recovery.
- Issues zcash/zips#1133 (PQ privacy, open since 2022) and #1134 (fully PQ Zcash, open since
  2016): discussion only, no draft ZIPs. A grep of the whole zips repo finds zero occurrences of
  ML-KEM/Kyber/ML-DSA/lattice.
- Ragu/Tachyon (successor proving stack) is deliberately ECDLP-based
  (`ragu/book/src/protocol/index.md:20-24`, citing Bowe's "reduced concern (in the medium term)"
  for PQ soundness). Zcash's quantum strategy is recoverability, not resistance.
- Marketing claims without primary-source support: "fully post-quantum in 12–18 months" (Swihart,
  Consensus Miami, CoinDesk 2026-05-08) and "ML-KEM/ML-DSA being tested" (CoinDesk research) —
  no ZIP, draft, or repo artifact corroborates either; ZIP 2005 itself disclaims making the
  protocol quantum-secure.

## 4. Threat summary, ordered by reversibility

**Retroactive — damage accruing now.** Note-encryption HNDL is the only retroactive break in
deployed Orchard: every (epk, C_enc) recorded today is decryptable by a future CRQC given the
recipient address, exposing amounts, memos, and full receiving history forever. No fix can
protect already-recorded ciphertexts; nothing is even specified for future ones. This is the
open wound.

**Prospective — exploitable only once a CRQC exists, mitigable by timely pool switch-off.**
All integrity breaks: Sinsemilla binding (note forgery, fake Merkle paths, Spendability
attacks), Pedersen cv + binding sig (silent inflation), RedPallas (spend-auth forgery → theft),
Halo 2 soundness (arbitrary false statements — the most concentrated point). Helpfully, the
recorded chain leaks no secrets to a quantum adversary without addresses: cv is unconditionally
hiding, α perfectly masks ask in rk, Halo 2 is perfectly ZK. The symmetric backbone (BLAKE2b
PRFexpand, ZIP 32 tree) and Poseidon-as-PRF survive; ZIP 2005 re-anchors ownership on exactly
that backbone, so recoverability of Ironwood notes is credible — contingent on the unspecified
Recovery Protocol, an unchosen PQ proof system, and switch-off happening before, not after, the
first quantum forgery.
