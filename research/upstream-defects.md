# Upstream defects found while writing the Sync Guide

Verified firsthand 2026-07-15. Ready-to-file issue bodies; a fourth defect
(`RawTransaction.height` mempool contradiction) is already tracked as
[zcash/librustzcash#1484](https://github.com/zcash/librustzcash/issues/1484).

---

## 1. zcash/zips — ZIP-307 grace-period condition inverted

**Title:** ZIP 307: second Canopy-onward lead-byte condition rejects 0x01
during the grace period

**Body:**

The compact-note trial-decryption pseudocode in `zip-0307.rst` contains two
`[Canopy onward]` lead-byte checks:

```
- [Canopy onward] if height <  CanopyActivationHeight + ZIP212GracePeriod
                  and leadByte ∉ {0x01, 0x02}, return ⊥
- [Canopy onward] if height <  CanopyActivationHeight + ZIP212GracePeriod
                  and leadByte ≠ 0x02, return ⊥
```

Both test `height < CanopyActivationHeight + ZIP212GracePeriod`. As written,
the second line rejects `leadByte = 0x01` *during* the grace period,
contradicting the first line and defeating the grace period entirely (no
pre-ZIP-212 note would ever decrypt). The second condition is evidently
intended to be the post-grace rule:

```
if height ≥ CanopyActivationHeight + ZIP212GracePeriod and leadByte ≠ 0x02,
return ⊥
```

which matches the deployed behaviour (`zip212_enforcement` in
librustzcash: `GracePeriod` accepts both lead bytes, `On` requires `0x02`).

Observed at zcash/zips `69610984`.

---

## 2. zcash/librustzcash — `ScanSummary` has no Ironwood counters

**Title:** `ScanSummary` lacks spent/received counters for the Ironwood pool

**Body:**

Struct `ScanSummary` (`zcash_client_backend/src/data_api/chain.rs:440`)
carries `spent_sapling_note_count` / `received_sapling_note_count` and, under
`feature = "orchard"`, the Orchard pair — but no Ironwood counterparts. With
NU6.3 introducing the Ironwood pool (ZIP 258) and wallets scanning Ironwood
outputs via the extended compact-block format, per-pool scan telemetry for
Ironwood appears to be an oversight; callers consuming `ScanSummary` (e.g.
progress reporting) will silently under-count activity in the new pool.

Observed at zcash/librustzcash `e30517e433`.

---

## 3. zingolabs/zaino — advertises nonexistent lightwallet protocol v0.5.0

**Title:** `LightdInfo.lightwalletProtocolVersion` hard-codes "v0.5.0",
which does not exist upstream

**Body:**

Both backends hard-code the advertised protocol version:

- `packages/zaino-state/src/backends/fetch.rs:2097`
- `packages/zaino-state/src/backends/state.rs:2776`

```rust
lightwallet_protocol_version: "v0.5.0".to_string(),
```

The canonical `zcash/lightwallet-protocol` repository's latest tagged
release is `v0.4.1`; no `v0.5.0` tag exists (and lightwalletd leaves field
18 unpopulated). Zaino's vendored proto snapshot is an intermediate state
(Ironwood fields present) that matches no published protocol version, so
clients keying behaviour on this field would be misled. Either the canonical
repo should mint the version Zaino ships, or Zaino should advertise the
version it actually implements.

Observed at zingolabs/zaino `0e057e22`.

---

# Upstream defects found while writing the ZSA Guide

Verified firsthand 2026-07-15 at zcash/zips `69610984`, QED-it/zips (zsa1)
`fd71419a`, QED-it/orchard (zsa1) `cf801a5d`, QED-it/librustzcash (zsa1)
`3f9b53fc`.

---

## 4. zcash/zips — ZIP-227 cites a ZIP-226 anchor that no longer exists

**Title:** ZIP 227: SigHash consensus rule references
`[#zip-0226-txiddigest]`, but ZIP 226 no longer contains a TxId Digest
section

**Body:**

`zip-0227.rst:474` states the SigHash is computed "with the modifications
described in ZIP 226 [#zip-0226-txiddigest]", and the footnote at line 693
links `zip-0226.rst#txid-digest`. Upstream ZIP 226 contains no "TxId
Digest" section (the v6 digest material lives in the now-withdrawn ZIP
246), so the reference is dangling. Either point the rule at ZIP 246 (with
its Withdrawn caveat) or at whatever ZIP respecifies the v6 digests.

Observed at zcash/zips `69610984` (`zip-0227.rst:474,693`).

---

## 5. zcash/zips — ZIP-226 cites ZIP 2005 under a stale title

**Title:** ZIP 226: ZIP 2005 is cited as "Orchard Quantum Recoverability";
its title is "Ironwood Quantum Recoverability"

**Body:**

`zip-0226.rst:45` reads "ZIP 2005 (Orchard Quantum Recoverability) is
expected to deploy before any ZSA activation", but `zip-2005.md`'s header
titles the ZIP "Ironwood Quantum Recoverability" (Status: Proposed). The
stale name predates the Ironwood renaming and misleads readers about which
pool the recoverability changes target.

Observed at zcash/zips `69610984` (`zip-0226.rst:45` vs `zip-2005.md`
header).

---

## 6. zcash/zips — valueBurn upper bound: "less than" vs "≤"

**Title:** Withdrawn ZIP 230's `valueBurn` bound ("less than
MAX_BURN_VALUE") contradicts ZIP 226's rule (`v ≤ MAX_BURN_VALUE`)

**Body:**

ZIP 226's burn consensus rule 2 requires
`v > 0 and v <= MAX_BURN_VALUE` (`zip-0226.rst:224`), while ZIP 230's
AssetBurn field table says `valueBurn` is "checked by consensus to be
non-zero, and less than MAX_BURN_VALUE" (`zip-0230.rst:377-380`),
excluding equality. The reference implementation rejects only amounts
strictly greater than `MAX_BURN_VALUE = (1 << 63) - 1`, i.e. permits
equality, agreeing with ZIP 226 (QED-it/orchard
`src/bundle/burn_validation.rs:16,100` @ `cf801a5d`). ZIP 230 is
Withdrawn, but any respecification inheriting its field table inherits
the off-by-one wording.

Observed at zcash/zips `69610984`; QED-it/orchard `cf801a5d`.

---

## 7. zcash/zips + QED-it/orchard — empty non-finalizing IssueAction:
implementation rule without a ZIP-227 consensus rule

**Title:** `IssueActionWithoutNoteNotFinalized` has no counterpart MUST in
ZIP 227

**Body:**

The reference implementation rejects an `IssueAction` with no notes unless
it is finalized (`IssueActionWithoutNoteNotFinalized`, QED-it/orchard
`src/issuance.rs:216-219` @ `cf801a5d`). ZIP 227's consensus-rule list
(`zip-0227.rst:470-500`) contains no such MUST, and ZIP 230 merely notes
`nNotes` may be zero "to only finalize". A ZIP-conformant validator would
accept an empty, non-finalizing action that the reference implementation
rejects — a consensus-splitting divergence if nodes disagree on which
artifact is normative. Either ZIP 227 should add the rule or the
implementation should drop the check.

Observed at zcash/zips `69610984`; QED-it/orchard `cf801a5d`.

---

## 8. QED-it forks — code diverges from upstream ZIP-226/246 as rebased

**Title:** ZSA fork stack lags upstream ZIP text: split-note ψ^nf
derivation, lead byte, and ZIP-246 digest tree

**Body:**

Three code-versus-upstream divergences at the current pins, each blocking
byte-compatibility with the upstream texts as rebased in 2026:

1. **Split-note ψ^nf.** Upstream ZIP 226 derives
   `ψ^nf = ToBase(PRFexpand_{rseed_nf}(0x0A || ρ_old))`, domain byte
   `0x0A` reserved by ZIP 2005 (`zip-0226.rst:297`); the fork ZIP samples
   ψ^nf uniformly at random on F_{q_P} (zips-zsa `zip-0226.rst:293` @
   `fd71419a`); the implementation uses the ordinary PSI byte `0x09`
   keyed by a fresh `rseed_split_note` (QED-it/orchard
   `src/circuit.rs:316-319`, `src/note.rs:417-425`; QED-it/zcash_spec
   `src/prf_expand.rs:89` @ `d5e84264`).
2. **Lead byte.** Upstream ZIP 230/226 replaced `0x03` with the
   `{{LEADBYTE}}`/`{{ZSALEADBYTE}}` placeholders (ZIP 2005 claims `0x03`);
   the implementation hard-codes `NOTE_VERSION_BYTE_V3 = 0x03`
   (QED-it/orchard `src/primitives/zcash_note_encryption_domain.rs:49`).
3. **ZIP-246 digest tree.** `librustzcash-zsa`'s txid omits the T.1f fee
   field ("TODO: Factor this out … when implementing ZIP 246 in full",
   `transaction/txid.rs:256`) and the T.6 memo branch (five-branch
   `to_hash`, `transaction/txid.rs:415-460`), and inserts a non-spec
   per-action-group memos digest with personalization `ZTxIdOrcActMHash`
   (QED-it/orchard `src/bundle/commitments.rs:27`).

All three are known interim states, but none is tracked in the upstream
ZIP text or fork issue trackers as far as the pinned trees show.

Observed at QED-it/orchard `cf801a5d`, QED-it/librustzcash `3f9b53fc`,
QED-it/zips `fd71419a`, zcash/zips `69610984`.

---

# Upstream defects found while writing the Crosslink Guide

Verified firsthand 2026-07-15 at tfl-book `fe6e1d6f` (upstream HEAD
unchanged; repository transferred to `github.com/daira/tfl-book`, rendered
at `daira.github.io/tfl-book`) and crosslink-spec `8edc3e94`.

---

## 9. tfl-book — Final Agreement safety theorem carries the wrong proof

**Title:** Security analysis: the proof under "Safety Theorem: Final
Agreement of Π_bft implies Assured Finality" is a verbatim duplicate of
the Prefix Agreement proof

**Body:**

In `src/design/crosslink/security-analysis.md`, the proof text under
"Safety Theorem: Final Agreement of Π_bft implies Assured Finality"
(lines 87-91) is byte-identical to the proof of "Safety Theorem: Prefix
Agreement of Π_bc at confirmation depth σ implies Assured Finality"
(lines 73-77): it invokes "Prefix Agreement at confirmation depth σ" and
never uses Final Agreement. The theorem is the design's load-bearing
safety claim for the case of a subverted PoW layer, and it currently has
no written proof; the intended route presumably runs through the
Linearity rule (cf. the sketch at `construction.md:592`). The defect
persists on the rendered book (`daira.github.io/tfl-book`, fetched
2026-07-15).

Observed at tfl-book `fe6e1d6f` (`security-analysis.md:73-77` vs
`87-91`).

---

## 10. informalsystems/crosslink-spec — first `add_pow` block collides
with the genesis hash

**Title:** `add_pow` assigns `PoWHashed(pow_store.size())`, so the first
added PoW block duplicates the genesis hash and self-parents

**Body:**

In `validity.md`, `PoWGenesis` is `{hash: PoWHashed(1), parent:
PoWHashed(0)}` and `add_pow` assigns `hash:
PoWHashed(pow_store.size())`. With genesis pre-loaded, the first
`add_pow` in every trace therefore mints `{hash: PoWHashed(1), parent:
PoWHashed(1)}` — a phantom, self-parented duplicate of the genesis hash;
all later hashes are fresh (the store grows strictly). The merge commit
`8edc3e9` ("added +1 to make bft blocks unique") fixed the analogous
collision on the BFT side only (`try_add_bft` uses
`BFTHashed(length()+1)`).

Impact: confined to the root. `prefix_inv` cannot be spuriously
satisfied (non-root hashes are unique, and descent from the universal
root is vacuous), so the published model-checking result stands; but
`sigmaConfirmed(genesis, ·, 1)` accepts the phantom block as a
confirmation-tail witness at the verification scope
(`confirmation_depth = 1`, stores ≤ 8), so checked coverage differs
slightly from the intended semantics. A model artifact, not a soundness
gap; the fix is to seed PoW hashes past the genesis value as the BFT
side already does.

Observed at crosslink-spec `8edc3e94` (`validity.md`: `PoWGenesis`,
`add_pow`, `sigmaConfirmed`, `isDescendant`).

---

# Wave-0 model-diff findings (DRAFT — needs owner confirmation before filing)

**DRAFT.** These 11 entries come from a breadth-first model-diff pass
(2026-07-16), firsthand-cited but not yet owner-reviewed. Do not file upstream
until each is confirmed. Every entry is a case where the guide is on the correct
side; the defect is in the upstream source. Numbering continues the dossier
(11-21). Ground-truth pins: zcash/zips `69610984` (protocol.tex `662dc87`);
orchard HEAD `bef8a27`; librustzcash `e30517e4`; zebra-crosslink `6d02a1b`;
tfl-book `fe6e1d6f`; voting-circuits `4c39abd`; vote-sdk `cb915f5`; RFC 9591;
ePrint 2024/436.

Two are `medium` (both crosslink code bugs); the rest are `low` (spec/impl
divergences and stale citation apparatus).

---

## 11. zcash/librustzcash — NU6.3 Mainnet activation height hardcoded where ZIP-258 says TBD

**DRAFT. Severity: low.**

**Title:** `MainNetwork::activation_height` pins an NU6.3 Mainnet height
(3,428,143) while ZIP-258 leaves Mainnet TBD

**Body:**

`consensus.rs:496` returns `NetworkUpgrade::Nu6_3 => Some(BlockHeight(3_428_143))`
— a concrete Mainnet activation height — but `zip-0258.md:68-70` gives
`ACTIVATION_HEIGHT (NU6.3)` as `Testnet: 4134000` / `Mainnet: TBD`. The Testnet
side agrees on both (`consensus.rs:529` = `4_134_000` = `zip-0258.md:69`), so the
divergence is strictly the Mainnet height. Likely a benign pre-finalization
placeholder rather than a true bug: an implementation ahead of an unfinalized
spec. The Ironwood Guide already reads the spec correctly and flags this
(`ironwood-guide.tex:2050-2055`). Not a duplicate of the existing ZIP-258 mention
in this dossier (entry 2 is the `ScanSummary` counters gap).

Observed at librustzcash `e30517e4` (`components/zcash_protocol/src/consensus.rs:496,529`);
zcash/zips `69610984` (`zip-0258.md:68-70`).

---

## 12. zcash/zips — protocol.tex Action Statement omits the NU6.3 cross-address input the deployed circuit enforces

**DRAFT. Severity: low.**

**Title:** §7.1.5.4 Action Statement still specifies the pre-Ironwood 9-element
primary input (conditions A1-A9), omitting the tenth flag ZIP-229/258 and the
deployed circuit mandate

**Body:**

The formal Action Statement in `protocol.tex` specifies a 7-logical / 9-flattened
primary input ending at `enableOutputs` (`protocol.tex:8008-8014`; pnote
`8103-8107` lists exactly 9 field elements as `(F_q)^9`), with conditions
stopping at [A8] Enable spend / [A9] Enable output (`8082-8086`). An adversarial
`awk` over `protocol.tex:7980-8140` returns zero tokens matching
cross-address / Ironwood, even though NU6.3 integration has begun elsewhere in
the file (`IronwoodPool` defined; `isnusixthree` toggle at `103-104`). The
deployed circuit adds the flag as public input index 9: orchard `bef8a27`
`src/circuit.rs:88` `const DISABLE_CROSS_ADDRESS: usize = 9;`,
`synthesize_cross_address_checks` (`920-960`) enforcing four affine-coordinate
equalities, gated at `1052-1053` behind `supports_cross_address_restriction`
(true only for `OrchardCircuitVersion::Ironwood`, `1599-1601`). The ZIPs mandate
it: `zip-0229.md:200,210,448` define `enableCrossAddress` as flag bit 2 "(new at
NU6.3)"; `zip-0258.md:91-94` requires every Orchard-pool Action be created with
cross-address transfers disabled, "enforced by the Action circuit verifying key".
The gap is acknowledged as deferred: `zip-0258.md:146-148` ("Many changes are
required throughout the specification ... not spelled out here"); the owning
circuit ZIP-2006 is a 273-byte `Reserved` stub; ZIP-229/258 are Draft and NU6.3
is unactivated. The Ironwood Guide documents the flag correctly (Def A10,
`ironwood-guide.tex:1517-1525`; remark `1528-1547`, noting the detail is
reconstructable only from the implementation).

Observed at zcash/zips `69610984` (protocol.tex `662dc87`, `§7.1.5.4`); orchard
`bef8a27` (`src/circuit.rs:76,88,920-960,1052-1053,1599-1601`).

---

## 13. zcash/librustzcash — zip321 CHANGELOG claims zero-valued transparent outputs are consensus-rejected

**DRAFT. Severity: low.**

**Title:** `zip321` CHANGELOG asserts a per-output positivity consensus rule for
transparent outputs that the protocol spec does not impose

**Body:**

`components/zip321/CHANGELOG.md:49` (in the `[0.7.0] - 2026-04-23` entry) states
"Zero-valued transparent outputs are rejected by the Zcash consensus rules, and
so payments to transparent addresses with the `amount` parameter explicitly set
to zero are now disallowed." The protocol spec imposes no per-output positivity
consensus rule: `protocol.tex:4091`'s sole constraint is "The remaining value in
the `transparentTxValuePool` MUST be nonnegative"; the transaction consensus
block (`13560-13600`) and transparent-output description (`4130-4165`) constrain
only `txOutCount` and the coinbase no-transparent-outputs rule, and transparent
outputs are "encoded as in Bitcoin" (`13334`/`13447`) with no per-output nonzero
rule (the `[0, MAX_MONEY]` range at `6392` applies to Sapling output
descriptions). So an individual zero-valued transparent output is
consensus-valid; it is rejected only by mempool standardness (dust) policy —
corroborated by Zebra's `IsDust` standardness error
(`zebrad/src/components/mempool/storage.rs:139-140`). The impl documentation
therefore contradicts the spec. The Wallet Guide independently identifies the
CHANGELOG assertion as inaccurate (divergence D7, `wallet-guide.tex:5335-5352`).

Observed at librustzcash `e30517e433` (`components/zip321/CHANGELOG.md:49`);
zcash/zips `69610984` (`protocol.tex:4091`).

---

## 14. zcash/zips — ZIP 227 cites ZIP 209 under a stale title (stray "Shielded")

**DRAFT. Severity: low.**

**Title:** ZIP 227 references "ZIP 209: Prohibit Out-of-Range Shielded Chain
Value Pool Balances"; the stray "Shielded" contradicts ZIP 209's own header and
ZIP 226's citation

**Body:**

`zip-0227.rst:688` cites "ZIP 209: Prohibit Out-of-Range **Shielded** Chain Value
Pool Balances", but `zip-0209.rst:4`'s own header reads "Prohibit Out-of-Range
Chain Value Pool Balances" (no "Shielded"), and `zip-0226.rst:446` cites the same
ZIP without "Shielded". A half-completed rename: the historical title was
"Prohibit **Negative Shielded** Chain Value Pool Balances" (still in the QED-it
fork — `zip-0209.rst:4` and `zip-0227.rst:688` both read that). Upstream changed
"Negative" -> "Out-of-Range" and dropped "Shielded" in the ZIP-209 header and in
ZIP-226's citation, but in `zip-0227.rst:688` changed only "Negative" ->
"Out-of-Range", leaving the stray "Shielded". Same class as dossier entry 5
(stale ZIP-2005 title). The ZSA Guide glosses it as a benign fork-vs-upstream
"one reference title" difference (`zsa-guide.tex:320-321`) — worth upgrading to a
flagged defect there.

Observed at zcash/zips `69610984` (`zip-0227.rst:688` vs `zip-0209.rst:4` /
`zip-0226.rst:446`); QED-it/zips fork for the half-rename corroboration.

---

## 15. zebra-crosslink — fat-pointer deserializer reads a reversed slice range and panics on every valid input

**DRAFT. Severity: medium.**

**Title:** `FatPointerToBftBlock{,2}::try_from_bytes` reads the u16 length prefix
from `bytes[76 - 32..2]` (= `bytes[44..2]`, reversed), panicking on every input
that clears its own length guard

**Body:**

The serializer writes the u16 signature-count immediately after the 44-byte vote
field (offset 44): `zebra-chain/src/block/header.rs:164-165`
(`buf.extend_from_slice(&self.vote_...)` then
`buf.extend_from_slice(&(self.signatures.len() as u16).to_le_bytes())`;
byte-identical copies at `lib.rs:1887-1888` and `malctx.rs:171-172`). The
deserializer reads a reversed range — all three copies contain
`let len = u16::from_le_bytes(bytes[76 - 32..2].try_into().unwrap()) as usize;`
(`header.rs:178`, `lib.rs:1900`, `malctx.rs:184`). `76 - 32 = 44`, so the slice
is `bytes[44..2]` (start 44 > end 2). The length guard one line above
(`if bytes.len() < 76 - 32 + 2 { return None; }` at `header.rs:174` /
`lib.rs:1896` / `malctx.rs:180`) returns `None` only when `len < 46`, so every
input that clears it (`len >= 46` — including the minimal 46-byte null fat pointer
that `to_bytes()` emits) reaches the reversed slice and panics. Each function is
prefixed with `#[allow(clippy::reversed_empty_ranges)]` (`header.rs:172`,
`lib.rs:1894`, `malctx.rs:178`), silencing the exact lint that flags reversed
ranges. Empirically reproduced: `&bytes[76 - 32..2]` on a 46-byte `Vec` panics
`slice index starts at 44 but ends at 2`. The intended range is `bytes[44..46]`.
No callers exist at this commit (`try_from_bytes` appears exactly 3 times, all as
the `pub fn` definitions), so this is a latent panic — but the round-trip
`to_bytes()` -> `try_from_bytes()` is provably broken for every non-rejected
input, and fires the moment deserialization is wired in. The Crosslink Guide
describes the fat pointer and its conversion (`crosslink-guide.tex:2290-2303`)
but does not flag the bug.

Observed at zebra-crosslink `6d02a1b80f896d08f923e39b2505f0565efb5787`
(`zebra-chain/src/block/header.rs:172,178`; `zebra-crosslink/src/lib.rs:1894,1900`;
`zebra-crosslink/src/malctx.rs:178,184`).

---

## 16. zebra-crosslink — decided-block handlers finalize from the tip header while `finalization_candidate()` returns the deepest

**DRAFT. Severity: medium.**

**Title:** `finalization_candidate()` returns `headers.last()` (deepest) but both
tenderlink decided-block handlers compute the new final PoW hash from
`headers.first()` (tip); the reconciling assertion is commented out

**Body:**

Two code paths disagree on which bc-header of a decided `BftBlock` identifies the
newly finalized PoW block. `chain.rs:124-125`:
`pub fn finalization_candidate(&self) -> &BcBlockHeader { &self.headers.last()... }`
— returns the deepest header, given the documented tip-first in-memory order
that is "reversed from the specification" (`chain.rs:52-54`, quoting the spec's
"deepest first"; built tip-first, so `last()` = deepest). But `lib.rs:543` and
`lib.rs:809` both compute
`let new_final_hash = new_block.headers.first().expect("at least 1 header").hash();`
— the tip header. The reconciling assertion is disabled at `lib.rs:545`
(`// assert_eq!(new_final_height.0, new_block.finalization_candidate_height);`).
Spec: tfl-book `construction.md` @ `fe6e1d6f:420-427` — `headers_bc` is
"zero-indexed, deepest first" and `snapshot(B) := B.headers_bc[0]`, so the
finalization point derives from the deepest header; the live handlers use the
tip. Corroboration that `finalization_candidate_height` is the deepest (min)
height: `viz.rs:3028-3041` (`min_hdr_h = finalization_candidate_height`,
`max_hdr_h = ... + headers.len() - 1`), so the disabled `assert_eq!` would fail
for σ>1 — the tip is `max`, the candidate is `min`. With σ=3 the two selections
are three heights apart, so the implementation over-finalizes toward the tip on
those paths. The same first/last split recurs in live viz code (`viz.rs:974`
`last()` vs `999`/`1013` `first()`). The Crosslink Guide states this accurately
(`crosslink-guide.tex:2335-2344`).

Observed at zebra-crosslink `6d02a1b` (`chain.rs:52-54,124-125`;
`lib.rs:543,545,809`; `viz.rs:974,999,1013,3028-3041`); tfl-book `fe6e1d6f`
(`construction.md:420-427`).

---

## 17. zcash/zips — ZIP 312 cites stale RFC 9591 appendix letters (off by one)

**DRAFT. Severity: low.**

**Title:** ZIP 312 labels RFC 9591 Trusted Dealer Key Generation as "Appendix B"
and Random Scalar Generation as "Appendix C"; in the published RFC these are
Appendices C and D

**Body:**

`zip-0312.rst:444` cites `[#frost-tdkg]` as "Appendix B: Trusted Dealer Key
Generation" and `:445` cites `[#frost-randomscalar]` as "Appendix C: Random
Scalar Generation". In published RFC 9591 (June 2024, local `rfc9591.txt`):
`:1686` "Appendix C. Trusted Dealer Key Generation", `:1944` "Appendix D. Random
Scalar Generation". An "Appendix A. Schnorr Signature Encoding" (`:1616`) was
inserted in the final RFC, shifting every appendix letter by one relative to
`draft-irtf-cfrg-frost-11`, against which the ZIP was written. So tdkg is labeled
B but is really C, and randomscalar is labeled C but is really D — a reader
following letter B lands on Schnorr Sig Gen/Verification. Only the human-readable
titles are stale; the URL anchors (`#name-trusted-dealer-key-generati`,
`#name-random-scalar-generation`) still resolve. Same root cause as the
§7.3->§7.5 mislabel (entry 20). The FROST Guide is correct: `frost-guide.tex:871`
cites Appendix C for trusted-dealer keygen (matching RFC 9591) and only catches
the analogous section mislabel at `1343-1345`, not these appendix letters.

Observed at zcash/zips `69610984` (`zip-0312.rst:444-445`); RFC 9591
(`rfc9591.txt:1616,1686,1944`).

---

## 18. ePrint 2024/436 — Fig. 5 challenge-hash argument order self-inconsistent

**DRAFT. Severity: low.**

**Title:** In the Rerandomized-FROST construction figure, `Sign'`/`Combine`
compute `c <- H_sig(PK-bar, R, m)` while `Verify` computes
`c <- H_sig(PK-bar, m, R)`

**Body:**

Paper ePrint 2024/436, Fig. 5 (`rerand-2024-436.txt`): `Sign'` (`467-468`) and
`Combine` (`483-484`) use `Hsig(PK-bar, R, m)`; `Verify` (`501-502`) uses
`Hsig(PK-bar, m, R)`; caption `:510`; the reduction's random oracle queries
`Hsig` on `(PK, m, R)` (`:598`). `Hsig` is defined `{0,1}* -> Z_p` (`:447`), so
argument order is significant — taken literally a signature produced by
`Sign'`/`Combine` would not verify under `Verify`. Both orderings also differ
from RFC 9591 §4.6 / RedDSA's fixed order `(R, PK, m)` that the deployed `reddsa`
crate uses, so there is no deployment impact: a preprint typo with no normative
weight. The FROST Guide quotes both orderings and reads the mismatch as a
presentational slip (`frost-guide.tex:1119-1129`).

Observed at ePrint 2024/436 (`rerand-2024-436.txt:447,467-468,483-484,501-502,598`).

---

## 19. ePrint 2024/436 — construction figure cross-referenced as "Figure 4" but captioned "Fig. 5"

**DRAFT. Severity: low.**

**Title:** The Rerandomized-FROST construction (captioned Fig. 5) is referred to
as "Figure 4" twice in Section 5; "Figure 4" is overloaded with the
unforgeability game

**Body:**

Caption `rerand-2024-436.txt:510` "Fig. 5. Rerandomized-FROST ... Differences
with plain FROST are highlighted in a grey box." Section 5 prose points at that
construction as "Figure 4" twice: `:402` "We highlight the changes to plain FROST
in grey in Figure 4." and `:404` "We show the exact details of Rerandomized-FROST
in Figure 4." Both descriptions match the Fig. 5 caption verbatim. Meanwhile
Figure 4 is genuinely a different figure — `:350` "Fig. 4. The (static)
unforgeability games ..." — correctly referenced at `:387` and Def. 6 (`:390`).
A grep of every in-text "Figure N" confirms "Figure 5" never appears, so the
construction's true number is never cited and "Figure 4" is overloaded. The FROST
Guide is accurate: construction header `frost-guide.tex:1089` cites "Figure 5", a
footnote at `:1128` notes the paper twice mislabels it "Figure 4", and `:1165`
refers to the game as "its Figure 4".

Observed at ePrint 2024/436 (`rerand-2024-436.txt:350,387,390,402,404,510`).

---

## 20. zcash/zips — ZIP 312 cites the wrong RFC 9591 section for "Removing the Coordinator Role"

**DRAFT. Severity: low.**

**Title:** ZIP 312 cites RFC 9591 "Section 7.3: Removing the Coordinator Role";
the material is §7.5 (§7.3 is "Nonce Reuse Attacks")

**Body:**

`zip-0312.rst:441` cites `[#frost-removingcoordinator]` as "RFC 9591 ... Section
7.3: Removing the Coordinator Role". In RFC 9591 (`rfc9591.txt`): `:1423` "7.3.
Nonce Reuse Attacks", `:1442` "7.5. Removing the Coordinator Role" (TOC
corroborates: `:89` 7.3 Nonce Reuse, `:91` 7.5 Removing the Coordinator Role).
The printed number "7.3" is stale draft-vs-final drift; the URL anchor
`#name-removing-the-coordinator-ro` targets the correct 7.5 heading. Footnote
consumed at `zip-0312.rst:113-114`. The FROST Guide flags this correctly
(`frost-guide.tex:1343-1347`).

Observed at zcash/zips `69610984` (`zip-0312.rst:441`); RFC 9591
(`rfc9591.txt:1423,1442`).

---

## 21. voting-circuits — README and an in-code "Spec" note say 16 proposals/round; circuit and chain enforce 15

**DRAFT. Severity: low.**

**Title:** `MAX_PROPOSAL_AUTHORITY` documentation claims 16 proposals per round,
but bit 0 is a permanent sentinel so the deployed circuit and chain cap at 15

**Body:**

voting-circuits `4c39abd`, `src/delegation/README.md:300`:
"`MAX_PROPOSAL_AUTHORITY`: `2^16 - 1 = 65535`. A 16-bit bitmask authorizing voting
on all 16 proposals." — asserts 16. Contradicted within the same repo by
`src/vote_proof/circuit.rs:124-127`: "valid values are 1-15. Bit 0 is permanently
reserved as the sentinel/unset value and is rejected by the non-zero gate in
`AuthorityDecrementChip` (`q_cond_6`). This means a voting round supports at most
15 proposals, not 16." (also `circuit.rs:143` `MAX_PROPOSAL_ID: usize = 16`;
`:156` "Only bits 1-15 correspond to usable proposals"). The deployed cap is 15:
vote-sdk `cb915f5`, `x/vote/types/keys.go:48` `const MaxProposals = 15` ("bit 0
reserved as a sentinel ... leaving bits 1-15 usable"), enforced at
`x/vote/types/msgs.go:42-43`. The Voting Guide states 15 correctly
(`voting-guide.tex:835-840`) but does not flag this README-vs-circuit
self-contradiction, and its claim that the quantization gap "is the only
spec-versus-code disagreement this volume records" (`voting-guide.tex:332,741`)
overlooks this second one — a guide gap to fix alongside filing this defect.

Observed at voting-circuits `4c39abd` (`src/delegation/README.md:300`;
`src/vote_proof/circuit.rs:124-127,143,156`); vote-sdk `cb915f5`
(`x/vote/types/keys.go:48`, `x/vote/types/msgs.go:42-43`).

---

# Wave-1 model-diff findings (DRAFT — needs owner confirmation before filing)

**DRAFT.** These 11 entries come from the Wave-1 breadth-first model-diff pass
(2026-07-16), firsthand-cited but not yet owner-reviewed. Do not file upstream
until each is confirmed. Numbering continues the dossier (22-32). Ground-truth
pins unchanged: zebra-crosslink `6d02a1b` (verified HEAD =
`6d02a1b80f896d08f923e39b2505f0565efb5787`); orchard `bef8a27`; tfl-book
`fe6e1d6f`; voting-circuits `4c39abd`; vote-sdk `cb915f5`. All paths under
zebra-crosslink are `zebra-crosslink/zebra-crosslink/…` unless noted `zebra-chain/…`
/ `zebra-state/…` / `zebra-consensus/…`.

Severity spread: **2 high, 4 medium, 5 low** — a step up from Wave-0 (whose
ceiling was medium). Both highs and all four mediums are zebra-crosslink code
bugs in the BFT / finalization path; several cluster on one file (`lib.rs`).

**Dedup notes.** This wave's raw yield was 16 findings; four pairs/triples were
folded: notarization (raw 6+13+15 → **22**), fin-extraction depth off-by-one
(raw 4+10 → **23**), `finalization_candidate_height = 0` (raw 5+14 → **26**). A
16th raw finding (voting-circuits README "16 proposals") is a **duplicate of
Wave-0 entry 21** and is *not* re-filed here; see the note after entry 32.

---

## 22. zebra-crosslink — BFT notarization verification enforces neither roster membership nor the 2/3 supermajority (and accepts an empty signature set)

**DRAFT. Severity: high.**

**Title:** Fat-pointer / notarization verification only batch-verifies ed25519
signatures against keys carried in the fat pointer itself — no roster check, no
2/3-voting-power threshold, and an empty signature set verifies as valid

**Body:**

The decided-BFT-block handler `new_decided_bft_block_from_malachite`
(`lib.rs:499-620`, invoked via `ClosureToPushDecidedBlock` at `lib.rs:1234-1247`,
which crosslink-finalizes the block through `CrosslinkFinalizeBlock` at `:581`)
gates acceptance on exactly one cryptographic check: `lib.rs:531-535`,
`// TODO: check public keys on the fat pointer against the roster` immediately
followed by `if fat_pointer.validate_signatures() == false { error!(…); panic!(); }`.
There is no summation of voting power and no 2/3 comparison anywhere in the
function; a whole-crate grep for `two-thirds|supermajority|2/3|threshold|quorum`
finds only PoW `difficulty_threshold`.

`validate_signatures()` (`lib.rs:1933-1943`, byte-identical copy at
`malctx.rs:217-227`) builds an `ed25519_zebra::batch::Verifier`, and for each
`(vote, signature)` from `self.inflate()` queues `(vk_bytes =
vote.validator_address.0, sig, msg = vote.to_bytes())`, returning
`batch.verify().is_ok()`. `inflate()` (`lib.rs:1922-1932`) sets
`vote.validator_address = MalPublicKey2(MalPublicKey::from(s.public_key))` — the
verification key is read from the *same* `FatPointerSignature2 { public_key:
[u8;32], vote_signature: [u8;64] }` (`lib.rs:1989-1991`) that carries the
signature. So the check is tautological under attacker-chosen keys: it proves
only "these are valid signatures by these keys", never that the keys are roster
members or that their weight meets 2/3. Independently, an **empty** signature set
verifies as `Ok(())`: with `self.signatures == []` the batch is empty, so (ed25519-zebra
4.1.0 `batch.rs` `verify()`) `B_coeff = Scalar::ZERO`, `check =
vartime_multiscalar_mul(once(&0), once(&B)) = identity`, and
`identity.mul_by_cofactor().is_identity()` is true — `null()` (`lib.rs:1878-1883`)
constructs exactly such a pointer.

The sibling assertion `validate_bft_block_from_malachite_already_locked`
(`lib.rs:790-820`) adds no protection — it checks only prev-block fat-pointer
linkage (`:798-807`) and that the final hash exists at some PoW height
(`:809-819`), then returns `TMStatus::Pass`. `voting_power` /
`validators_at_current_height` are used only for the malachite-bug roster
workaround (`:464`, `:510`), reward apportionment (`:654-718`), and roster-update
commands (`:988-1074`) — never to validate a fat pointer.

This is the load-bearing check the guide's Assured-Finality safety proof depends
on: `crosslink-guide.tex:1611-1622`/`2440-2443` require "at least a two-thirds
absolute supermajority of the epoch's voting units to have been cast for a
proposal P", tracing verbatim to tfl-book `construction.md` @ `fe6e1d6f:129`,
`156-161`. The guide is faithful to the spec; the deployed handler has no
enforcement behind it. (The guide flags only the roster-check TODO at `2331-2333`,
not the missing threshold or the empty-batch gap.)

**Failure mode.** Forge `FatPointerToBftBlock2` for target block `B` (blake3 =
`H`): set `vote_for_block_without_finalizer_public_key[0..32] = H` (clears the
`:523` hash-binding check), then for each slot generate a fresh ed25519 keypair
`(sk_i, pk_i)` never in the roster, build `vote` with `validator_address = pk_i`,
sign `msg = vote.to_bytes()` with `sk_i`, and push `FatPointerSignature2 {
public_key: pk_i, vote_signature: sig_i }`. `validate_signatures()` batch-verifies
each `sig_i` against `pk_i` and returns `true`; a roster minority holding <2/3, or
an empty set entirely, passes identically. The target block is crosslink-finalized
on a forged notarization. Real-world reachability of this handler depends on
`tenderlink` (a private git dep, quorum-enforced upstream of the predicate today),
but the verification step itself is provably incomplete the moment it faces
untrusted input.

Observed at zebra-crosslink `6d02a1b` (`lib.rs:499-620,523-535,1878-1883,1922-1943,
1989-1991`; `malctx.rs:217-227`); ed25519-zebra 4.1.0 `batch.rs verify()`; tfl-book
`fe6e1d6f` (`construction.md:129,156-161`).

---

## 23. zebra-crosslink — the block that gets finalized is one confirmation shallower than the code's own computed candidate (σ−1, not σ)

**DRAFT. Severity: high.**

**Title:** The decided-block handler finalizes `headers.first()` (= tip−σ+1)
instead of the spec's `snapshot(B) = headers_bc[0]⌈¹` (that header's parent, at
tip−σ); `propose_new_bft_block` computes the correct candidate at tip−σ and then
discards it

**Body:**

`propose_new_bft_block` computes the correct finalization candidate:
`finality_candidate_height = tip_height.sub(bc_confirmation_depth_sigma)` = T−σ
(`lib.rs:379-381`) and fetches `candidate_hash` at exactly that height
(`lib.rs:414-416`). But it then uses `candidate_hash` only as the
`FindBlockHeaders` anchor (`lib.rs:425-429`). `FindBlockHeaders` returns headers
*strictly after* the anchor and in ascending order: `zebra-state
src/service/read/find.rs:392-397` sets `start_height = intersection_height + 1`,
`:414` `height_range = start..=final` ascending, `:485-490` asserts "the list
must not contain the intersection hash". With `MAX_FIND_BLOCK_HEADERS_RESULTS =
160` (`constants.rs:110`) ≥ σ and σ = 3 (`chain.rs:220`), `headers = [T−σ+1 … T]`,
so the anchor block (T−σ) is *excluded* and `headers[0]` is the deepest returned
header at T−σ+1. `new_decided_bft_block_from_malachite` then finalizes
`new_final_hash = new_block.headers.first().hash()` = T−σ+1 (`lib.rs:543-544`) and
issues `CrosslinkFinalizeBlock(new_final_hash)` (`lib.rs:579-587`). The spec
finalizes `snapshot(B) := headers_bc[0]⌈¹_bc` — the *parent* of the deepest
header, at depth σ (tfl-book `construction.md` @ `fe6e1d6f:420-428`;
`candidate(H) := lca(snapshot(LF(H)), H⌈^σ)` at `:434`; the fin-depth lemma
`:490-495`, `:510-513` requires the finalized point at depth ≥ σ for Assured
Finality). So the code finalizes the deepest *header itself* (depth σ−1), one
block too shallow, and the correcting assert `lib.rs:545`
(`// assert_eq!(new_final_height.0, new_block.finalization_candidate_height)`) is
commented out.

This is distinct from Wave-0 entry 16 (the `headers.first()` vs
`finalization_candidate() = headers.last()` accessor disagreement): the off-by-one
persists even if that first/last split is reconciled, because the correct target
is `headers.first().parent`, not either end of the vector. The guide's own
header-order bullet carries a TODO admitting the direction is unresolved
(`crosslink-guide.tex:~2345`), while `1725-1731` states the correct rule ("The
snapshot is the parent of the deepest supplied header").

A related second-order effect: `is_improved_final` (`lib.rs:404`) gates on
`cand_height > latest` (height-only), comparing T−σ against the previously
recorded T′−σ+1, so finality only advances when the tip grows by ≥2 blocks — if
PoW yields exactly one block per BFT round, no proposal is emitted and finality
stalls by a block until a 2-block gap appears.

**Failure mode.** With σ = 3 and PoW tip at height T, every decided BFT block
finalizes T−2 (2 confirmations) rather than the intended candidate/snapshot at
T−3 (3 confirmations). T−2 is not ⪯ H⌈^σ = T−3, violating the σ-confirmation
invariant the Assured Finality proof depends on — every finalization is one
confirmation shallower than the protocol's safety margin, and the code holds the
correct answer (`candidate_hash` = T−3) and throws it away.

Observed at zebra-crosslink `6d02a1b` (`lib.rs:379-381,404,414-429,543-545,
579-587`; `zebra-state src/service/read/find.rs:392-397,414,485-490,526`;
`constants.rs:110`; `chain.rs:220`); tfl-book `fe6e1d6f`
(`construction.md:420-428,434,490-495,510-513`).

---

## 24. zebra-crosslink — consensus-path callbacks `panic!()` instead of returning an error (liveness/DoS)

**DRAFT. Severity: medium.**

**Title:** The tenderlink historical-block closure is an unconditional
`panic!()`, and the decided-block handler `panic!()`s on fat-pointer
hash-mismatch / signature-failure — both abort the node instead of rejecting

**Body:**

`tfl_service_main_loop` (spawned at `service.rs:207`) unconditionally spawns
`tenderlink::entry_point` at `lib.rs:1205` with a set of closures — the spawn
sits in the plain block opened at `:1116`, with no `TEST_MODE`/`cfg(test)`/validator
gate between `:1099` and `:1205` (the only `TEST_MODE` branch, `run_tfl_test` at
`:1098`, is separate). Two closures abort the process:

1. **Historical-block closure**, `lib.rs:1248-1252`:
   `ClosureToGetHistoricalBlock(Arc::new(move |height| Box::pin(async move {
   panic!(); })))` — the body ignores `height` and is an unconditional panic stub.
   A complete working alternative, `async fn get_historical_bft_block_at_height`
   (`lib.rs:843-861`, bounds-checks height, clones the block, builds the fat
   pointer, returns `Option`), sits a few hundred lines away and has **zero
   callers** (repo-wide grep) — dead code.

2. **Decided-block handler** `new_decided_bft_block_from_malachite`
   (body of `ClosureToPushDecidedBlock` at `:1234-1247`): `panic!()` at
   `lib.rs:529` when `fat_pointer.points_at_block_hash() != new_block.blake3_hash()`,
   and `panic!()` at `:534` when `fat_pointer.validate_signatures() == false`.

That this is a defect, not a simplification, is confirmed by the sibling
`ClosureToValidateProposedBlock` at `lib.rs:1220-1233`, which returns
`tenderlink::TMStatus::Fail` on undeserializable input — the codebase knows the
graceful-reject pattern; these two callbacks do not use it.

**Failure mode.** When tenderlink asks this node for a historical decided BFT
block (normal catch-up sync of a lagging peer), the closure panics and the node
crashes — a remotely-reachable liveness failure with a ready alternative left
unused. Separately, any decided value delivered with a malformed/invalid fat
pointer crashes the node via `:529`/`:534` rather than being rejected.

Observed at zebra-crosslink `6d02a1b` (`lib.rs:843-861,529,534,1205,1220-1233,
1234-1252`; `service.rs:207`). Distinct from Wave-0 entries 15 (`try_from_bytes`
reversed range) and 16 (fin `first`/`last`): this is the panic-on-failure pattern
in registered consensus callbacks.

---

## 25. zebra-consensus / zebra-crosslink — BFT voting power (roster) is mutated by staking transactions that are neither stake-backed nor per-action authorized

**DRAFT. Severity: medium.**

**Title:** A zero-input/zero-output `VCrosslink` staking transaction passes
`has_inputs_and_outputs` and adds arbitrary `voting_power` to an
attacker-chosen finalizer key — no locked ZEC, no signature by the target key,
power-of-10 rule unenforced

**Body:**

Design (nutshell.md / guide) requires the roster to be both value-backed and
key-authorized: `zebra-crosslink book/src/design/nutshell.md:96,98,102,104` — a
finalizer's voting weight is the sum of staking positions, each needing a
finalizer verification key + staked ZEC, with an unstaking/redelegation key
authorizing changes; `:86` amounts must be powers of 10 ZAT;
`crosslink-guide.tex:2386-2388` "Crosslink's finality vote is stake-weighted".

The implementation binds none of this. (1) `zebra-consensus
src/transaction/check.rs:124-130` `has_inputs_and_outputs` returns `Ok(())` for
any `VCrosslink` with `staking_action.is_some()` (comment "TODO: real staking
transactions with inputs/outputs") — a zero-input/zero-output tx is accepted.
(2) `lib.rs:948-965` `push_staking_action_from_cmd_str` builds exactly that tx:
`inputs: Vec::new()`, `outputs: Vec::new()`, both shielded `None`,
`staking_action = StakingAction::parse_from_cmd(cmd_str)`. (3) `lib.rs:988-1061`
`update_roster_for_cmd` Add path: `amount = action.val`; `member.voting_power +=
amount` or `roster.push(MalValidator::new(add_key.0, amount))` where `add_key =
action.target` parsed from the command string — no value binding, no signature by
the target key; the power-of-10 rule is unenforced (grep for
`pow(10`/`ilog10`/`%10` in consensus = none). (4) `lib.rs:697,718` add rewards
straight into `voting_power`. (5) `zebra-consensus src/transaction.rs:573-575`
hard-codes the `VCrosslink` fee ("TODO: remove this complete @Hack").

Crux: `malctx.rs:706-718` `MalValidator` implements
`malachitebft_core_types::Validator`, `voting_power()` returning the field, and
`lib.rs:458-464` serves `validators_at_current_height` as Malachite's current
validator set. So this field *is* the BFT vote weight (and the reward weight,
`lib.rs:654`).

**Failure mode.** Any party broadcasts a zero-value, zero-input `VCrosslink`
staking tx whose `staking_action` adds a large `val` to a finalizer key it
controls. It passes `has_inputs_and_outputs` (no coins required) and
`verify_v5_transaction` (nothing to verify), and every node's
`update_roster_for_cmd` raises that key's `voting_power`. One unbacked,
unauthenticated transaction can seize a supermajority of the roster.

Observed at zebra-crosslink `6d02a1b` (`zebra-consensus src/transaction/check.rs:124-130`,
`src/transaction.rs:573-575`; `lib.rs:458-464,654,697,718,948-965,988-1061`;
`malctx.rs:706-718`; `book/src/design/nutshell.md:86,96,98,102,104`).

---

## 26. zebra-crosslink — `BftBlock.finalization_candidate_height` is hard-coded 0 on every proposed (and therefore every decided) block, and committed into the block's BLAKE3 identity

**DRAFT. Severity: medium.**

**Title:** `propose_new_bft_block` passes the literal `0` as the
`finalization_candidate_height` argument to `BftBlock::try_from`, discarding the
tip−σ it just computed; the field is serialized into the block hash and the
reconciling assert is disabled

**Body:**

`propose_new_bft_block` computes the real candidate `finality_candidate_height =
tip_height.sub(bc_confirmation_depth_sigma)` = tip−σ (`lib.rs:379-391`) and uses
it for the header request (`:414`) and the `is_improved_final` gate (`:404`), but
threads the literal `0` into the block: `lib.rs:443-449`, `BftBlock::try_from(params,
internal.bft_blocks.len() as u32 + 1, internal.fat_pointer_to_tip.clone(), 0,
headers)` — the 4th positional arg binds to `finalization_candidate_height`
(signature `chain.rs:129-135`). `try_from` validates only `headers.len() ==
bc_confirmation_depth_sigma` (`chain.rs:136-140`), logs `error!("not yet
implemented: all the documented validations")` (`:142`), and echoes the value
verbatim into the struct (`:148`). So `0` flows through unreconciled. The field
is documented "The height of the PoW block that is the finalization candidate"
(`chain.rs:70-71`) and is serialized on the wire (`chain.rs:83`
`write_u32(self.finalization_candidate_height)`, deserialized `:97`) and into the
block's BLAKE3 identity (`From<&BftBlock> for Blake3Hash`, `chain.rs:166-178`).
The decided handler carries the block through unchanged (`lib.rs:577`), so every
*decided* block also advertises `0`.

The reconciling consistency check `lib.rs:545`
(`// assert_eq!(new_final_height.0, new_block.finalization_candidate_height)`) is
commented out; with the field pinned at 0 it reduces to "(height of
`headers.first()`) == 0", unsatisfiable off genesis — which is why it is
disabled. This is a distinct root cause from Wave-0 entry 16 (which attributed the
disabled assert to the tip=first vs deepest=last split at σ>1): the field being
hard-coded 0 makes the assert unsatisfiable even at σ=1 where first==last.

That 0 is a bug, not intent, is corroborated by `zebrad/tests/crosslink.rs:687-691`
(the test author populates the field with a real
`pow_blocks[0].coinbase_height().0`) and by the commented-out backfill at
`viz.rs:830-843` treating 0 as a known "unset" sentinel to repair.

**Failure mode.** Given tip H and σ=3, the proposer builds a `BftBlock` whose
`finalization_candidate_height` is 0 instead of H−3, committed into the block's
BLAKE3 identity hash, and the documented invariant (assert at `lib.rs:545`) is
permanently unsatisfiable. Any consumer reading the field mislocates the
finalization point at genesis — live today in a dev tool: `viz.rs:3028,3041,3330`
anchor decided blocks at height 0.

Observed at zebra-crosslink `6d02a1b` (`lib.rs:379-391,404,414,443-449,545,577`;
`chain.rs:70-71,83,97,129-135,136-148,166-178,220`; `viz.rs:830-843,3028,3041,3330`;
`zebrad/tests/crosslink.rs:687-691`).

---

## 27. zebra-crosslink — the finalization path implements none of the book's `updatefin` no-rollback safety logic (no descendant check, no rollback on state error, no hazard record)

**DRAFT. Severity: medium.**

**Title:** `is_improved_final` gates only on strictly-greater height, the decided
handler sets `latest_final_block` unconditionally before the state call and never
rolls it back on `Err`, and no finalization-safety hazard is ever recorded

**Body:**

The book's `updatefin` (tfl-book `construction.md` @ `fe6e1d6f:477-486`) is: `N
:= candidate(ch); if N ⪰ localfin then localfin ← N; else keep old, and if N ⋠
localfin record a finalization-safety hazard` (`:471-473`, hazard record includes
`ch` + fin history, `:488`). The guide reproduces this (def `xl-updatefin`,
`crosslink-guide.tex:1977-1994`) and claims the deployed `latest_final_block`
mirrors the book's node-local `fin_i` state machine (`4147-4153`).

The deployment implements none of the safety logic. `is_improved_final`
(`lib.rs:403-404`, in the *propose* path) = `latest.is_none() || cand_height >
latest.0` — height-only, no descendant/ancestry check. The *decide* handler
`new_decided_bft_block_from_malachite` sets `internal.latest_final_block =
Some((new_final_height, new_final_hash))` **unconditionally** (`lib.rs:579`),
before the state call and with no ⪰/descendant check; on state `Err` it only
`error!(?err)` (`:581-593`) and leaves `latest_final_block` set — no rollback.
`tfl_set_finality_by_hash` (`lib.rs:1476`) is likewise unconditional ("TODO:
sanity checks"). A grep across `zebra-crosslink/src` for
`hazard`/`rollback`/`descendant`/`conflicts` logic returns zero hits. The state
layer offers no protection either: `zebra-state non_finalized_state.rs:264-292`
`crosslink_finalize` uses `find_chain(|c| c.height_by_hash(hash).is_some())` —
*any* chain, no descendant-of-previous check — returning `None` if absent, and
`write.rs:342-380` returns `Err("Couldn't find finalized block")` on
None-and-not-in-DB, which the crosslink side only logs.

This is orthogonal to the guide's already-noted "Linearity/Extension/LFS rules
not enforced" (those are proposal/block-validity rules, `crosslink-guide.tex:2329-2330`);
the `updatefin` no-rollback check is a separate fin-extraction mechanism the guide
does not flag as dropped.

**Failure mode.** A conflicting candidate at strictly greater height (a bc-reorg
deeper than σ, or a subverted/equivocating BFT — the exact break Crosslink's fin
logic is meant to survive) passes the height-only gate; `latest_final_block` is
overwritten with no descendant check and no hazard record. When that hash is on a
fork already pruned/uncommitted, `CrosslinkFinalizeBlock` returns `Err` but
`latest_final_block` still points at the never-committed block — the service
reports a finalized tip inconsistent with the committed chain and silently omits
the Assured-Finality hazard the book requires.

Observed at zebra-crosslink `6d02a1b` (`lib.rs:403-404,579,581-593,1476`;
`zebra-state non_finalized_state.rs:264-292`, `write.rs:342-380`); tfl-book
`fe6e1d6f` (`construction.md:471-473,477-486,488`).

---

## 28. zebra-crosslink — `FatPointerToBftBlock{,2}::zcash_deserialize` pre-allocates from a 2-byte attacker length, bypassing `TrustedPreallocate` (memory-amplification DoS)

**DRAFT. Severity: low.**

**Title:** The fat-pointer deserializer runs `Vec::with_capacity(len)` on a
2-byte attacker-controlled signature count (up to ~6.3 MB) before reading a
single signature byte, hand-rolling around Zebra's `TrustedPreallocate`
DoS-hardening

**Body:**

`FatPointerToBftBlock::zcash_deserialize` (`zebra-chain
src/block/header.rs:251-252`) reads `let len = reader.read_u16::<LittleEndian>()?;`
then immediately `let mut signatures: Vec<FatPointerSignature> =
Vec::with_capacity(len.into());` — the allocation runs before any signature byte
is read (identical duplicate `FatPointerToBftBlock2` at `lib.rs:1972-1973`).
`FatPointerSignature = { public_key: [u8;32], vote_signature: [u8;64] }`
(`header.rs:127-133`), size 96, so `with_capacity(0xFFFF)` reserves 65535·96 =
6,291,360 bytes.

This bypasses the codebase's own DoS convention:
`zebra-chain src/serialization/zcash_deserialize.rs:79-99`
`zcash_deserialize_external_count` checks `external_count > T::max_allocation()`
and returns `SerializationError::Parse("Vector longer than max_allocation")`
*before* its `Vec::with_capacity` (`:95`); the trait docstring (`:178-183`) calls
blind preallocation of a generic `Vec<T>` "a DOS vector". The idiomatic
`impl<T> ZcashDeserialize for Vec<T>` (`:23-32`) routes through that checked path
via CompactSize, but the FatPointer deserializer hand-rolls a raw `u16` read +
`Vec::with_capacity`, so `FatPointerSignature` never uses `TrustedPreallocate` and
no `max_allocation` bound applies. `Block::zcash_deserialize`'s
`.take(MAX_BLOCK_BYTES)` (`serialize.rs:190`) does not help: the allocation
happens on the 2-byte `len` alone, before signature bytes are read.

Reachability is v5+ only: `Header::zcash_deserialize` calls the fat-pointer
deserializer when `logical_version >= 5` (`serialize.rs:124-126`), and
`check_version` (`:36-62`) accepts version 5. Normal Zcash blocks are v4
(`ZCASH_BLOCK_VERSION = 4`), so current exposure is the Crosslink/regtest network;
if Crosslink ships it becomes every block-header parse.

**Failure mode.** A peer sends a v5 header whose 44-byte fat-pointer stub is
followed by `len = 0xFFFF` then EOF. The deserializer reads the stub, reads
`len = 65535`, allocates `Vec::with_capacity(65535)` = 6.29 MB, then the loop's
first `read_exact` of 96 bytes fails with `UnexpectedEof` and the Vec is dropped —
~6.3 MB transient allocation from a 46-byte input (≈136,769× amplification), per
header, pre-validation.

Observed at zebra-crosslink `6d02a1b` (`zebra-chain src/block/header.rs:127-133,
251-252`; `lib.rs:1972-1973`; `zebra-chain src/serialization/zcash_deserialize.rs:23-32,
79-99,178-183`; `zebra-chain src/block/serialize.rs:36-62,124-126,190`).

---

## 29. zebra-crosslink — `TF::read_from_bytes` panics on corrupt/adversarial `.zeccltf` files instead of returning `Err`

**DRAFT. Severity: low.**

**Title:** `read_from_bytes` (contract `Result<Self, String>`) slices with the
file-supplied `instrs_o` offset without any bounds or ordering check, so a
malformed offset panics

**Body:**

`test_format.rs:376` `pub fn read_from_bytes(bytes: &[u8]) -> Result<Self, String>`
is contracted to signal failure gracefully. The write side computes a valid
offset `instrs_o = align_up(size_of::<TFHdr>() + self.data.len(),
align_of::<TFInstr>())` (`:332-336`), but the read side never bounds-checks the
raw file field `tf_hdr.instrs_o` before two slices:
`<[TFInstr]>::ref_from_prefix_with_elems(&bytes[tf_hdr.instrs_o as usize..], …)`
(`:382-383`) and `let data = &bytes[size_of::<TFHdr>()..tf_hdr.instrs_o as usize];`
(`:392`). `TFHdr` (`magic[u8;8] + u64 + u32 + u32`, `repr(C)`) has
`size_of == 24` (`:9-16`).

Non-test reachability: `TF::read_from_file` (`viz.rs:3751`, with graceful `Err(err)
=> error!(…)` at `:3766`) and `read_instrs` (`test_format.rs:675`) both do a plain
`std::fs::read` then `read_from_bytes`, with no validation guard.

**Failure mode.** A file with `instrs_o = 0` (< `size_of::<TFHdr>() = 24`) makes
`bytes[24..0]` a reversed range → panic "slice index starts at 24 but ends at 0";
`instrs_o` greater than the file length → out-of-bounds slice panic "range start
index N out of range for slice of length M". Any tooling loading an untrusted or
corrupt crosslink-test-data file aborts instead of returning `Err`.

Observed at zebra-crosslink `6d02a1b` (`test_format.rs:9-16,332-336,376,382-383,392,
675`; `viz.rs:3751,3766`).

---

## 30. zebra-crosslink — `TF` write/read `data` field does not round-trip (padding is captured into `data`)

**DRAFT. Severity: low.**

**Title:** `write()` pads the data region up to `align_of::<TFInstr>()` before the
instruction table, but `read_from_bytes` reconstructs `data` as
`bytes[24..instrs_o]`, which includes that padding — so `read(write(tf)).data !=
tf.data` whenever `data.len() % 8 != 0`

**Body:**

Write pads and emits zero bytes between data and the instruction table:
`test_format.rs:332` `instrs_o_unaligned = size_of::<TFHdr>() + self.data.len()`;
`:333` `instrs_o = align_up(instrs_o_unaligned, align_of::<TFInstr>())`; `:344`
writes `self.data`; `:347-352` if `instrs_o > instrs_o_unaligned` writes
`align_size` zero bytes. Read reconstructs `data` running all the way to
`instrs_o`, capturing that padding: `:392` `let data =
&bytes[size_of::<TFHdr>()..tf_hdr.instrs_o as usize];`, `:397` `data: data.to_vec()`.
`size_of::<TFHdr>() = 24` (multiple of 8); `align_of::<TFInstr>() = 8`
(`kind:u32, flags:u32, data:TFSlice{o:u64,size:u64}, val:[u64;2]`, `:46-53`), so
`instrs_o > instrs_o_unaligned` exactly when `self.data.len() % 8 != 0`, producing
`8 − (data.len() % 8)` trailing zero bytes.

Masked today because instruction payloads are fetched by *absolute* offset, never
from the `tf.data` vec: `tf_read_instr` (`:442`) reads each payload via
`instr.data_slice(bytes)` → `TFInstr::data_slice` (`:144-146`) →
`TFSlice::as_byte_slice_in` (`:30-32`) `&bytes[o..o+size]` indexing the full
buffer; the driver `read_instrs(internal_handle, &bytes, &tf.instrs)` (called at
`:682`) passes `bytes`, not `tf.data`. No round-trip test exists (no `#[test]` /
`mod tests` in the file), so nothing catches the inequality.

**Failure mode.** Any `TF` whose `data` length is not a multiple of 8 round-trips
with trailing zero bytes appended to `.data`; a re-serialize of the read-back `TF`
would grow the file further and can desync the stored absolute instruction
offsets. Functionally latent only because payloads are fetched by absolute offset.

Observed at zebra-crosslink `6d02a1b` (`test_format.rs:9-16,30-32,46-53,144-146,
325-352,392-397,442,682`).

---

## 31. zebra-crosslink — `BftBlock`'s documented stateless validations are unimplemented, and the deserialize path bypasses the constructor entirely

**DRAFT. Severity: low.**

**Title:** `BftBlock::try_from` (documented as the "only way to construct" a
`BftBlock`, performing four stateless validations) checks only the header count,
hard-codes `version:1`, logs "not yet implemented", and `zcash_deserialize`
never calls it

**Body:**

The contract (`chain.rs:33-38,56`) lists four validations by the "sole
constructor" `try_from` — header count = σ, known version, header ordering by
`previous_block_hash`, PoW solutions validate — and calls it "the safest design",
"the only way to construct". The implementation (`chain.rs:136-151`) checks only
`headers.len()` (else `IncorrectConfirmationDepth`), then `error!("not yet
implemented: all the documented validations")` (`:142`) and hard-codes
`version: 1` (input version ignored). Validations 2/3/4 are absent.
`finalization_candidate()` is annotated `UNVERIFIED` (`chain.rs:123`).
`zcash_deserialize` (`chain.rs:92-118`) builds the struct literal directly
(`:110-116`) — never calls `try_from`; its own `TODO: Ensure deserialization
delegates to BftBlock::try_from` (`:48`) — with only a `header_count > 2048`
sanity cap (`:99-104`), so on the network path not even the count check runs. All
fields are `pub` (`chain.rs:62-74`), refuting "only way to construct" (direct
literals at `lib.rs:551`, `viz.rs:2667/2932`).

The network accept path (`service.rs:172-174` / `lib.rs:1227` →
`validate_bft_block_from_malachite` → `..._already_locked`, `lib.rs:790-820`)
checks only prev-block fat-pointer linkage (`:798-807`) and that
`headers.first()` is a known PoW block (`:809-819`), then returns `Pass`; a
crate-wide grep for `pow`/`equihash`/`check_solution` finds no PoW-solution
verification of BftBlock headers anywhere. (The guide documents this stub
accurately, so the guide is not wrong; filed here as the underlying defect.)

**Failure mode.** A decided/proposed `BftBlock` whose `headers` are not a valid
PoW chain (bad PoW solutions, wrong parent-linkage order, unexpected version) is
accepted: `try_from` validates none of these, and the deserialize path skips
`try_from` so even the count check is absent. The remaining σ−1 headers are never
PoW-verified — latent while only `headers.first()` drives fin-extraction, but the
documented safety property does not hold.

Observed at zebra-crosslink `6d02a1b` (`chain.rs:33-38,48,56,62-74,92-118,123,
136-151`; `lib.rs:551,790-820,1227`; `service.rs:172-174`; `viz.rs:2667,2932`).

---

## 32. zebra-crosslink — `finalization_candidate()` returns the chain tip; the `chain.rs` header-order docstring is inverted

**DRAFT. Severity: low.**

**Title:** The docstring claims the in-memory header order is "reversed from the
specification (built tip-first)", but the sole producer yields ascending /
deepest-first order matching the spec — so `finalization_candidate() =
headers.last()` returns the tip (T), not the σ-confirmed snapshot (~T−σ)

**Body:**

The sole producer, `propose_new_bft_block` via `FindBlockHeaders`, yields
ascending / deepest-first headers: `lib.rs:414-439` anchors at
`finality_candidate_height = tip−σ`; `zebra-state src/service/read/find.rs:414`
`height_range = start..=final` with `start = intersection+1 = tip−σ+1`, `final =
min(tip−σ+160, tip) = tip`, iterated ascending (`:526`); read handler
`service.rs:1720-1743` returns them unreversed. So `headers[0]` = tip−σ+1
(deepest), `headers.last()` = tip. This *matches* the spec's deepest-first
convention (tfl-book `construction.md` @ `fe6e1d6f:420` "exactly σ bc-headers,
zero-indexed, deepest first"; `:427` `snapshot(B) := B.headers_bc[0]⌈¹` = the
deepest header's parent).

Yet `chain.rs:52-54` asserts the in-memory order is "reversed from the
specification (built tip-first)" — factually inverted vs the sole real producer.
Consequently `finalization_candidate()` (`chain.rs:124-126`, `&self.headers.last()`)
returns the *tip* (height T, 0 confirmations) rather than the ~σ-confirmed
snapshot near T−σ; off by σ−1 = 2 blocks. Corroboration: the wired-up validation
path (`lib.rs:809`) uses `headers.first()` (deepest = spec's `headers_bc[0]`), so
the live code and the dead accessor disagree and the dead `last()` one is the
inverted/wrong end. Latent: a grep for `.finalization_candidate(` has zero
callers. This resolves the guide's explicit open TODO
(`crosslink-guide.tex:~2345`, "pin down which end of the header vector is the
snapshot"); the guide itself makes no false claim, it is correctly hedged.

**Failure mode.** `finalization_candidate()`, documented as "the finalization
candidate for this block", returns the block at the chain tip (height T, 0
confirmations) instead of the ~σ-confirmed snapshot near T−σ. Any future caller
that trusts this accessor (e.g. a real validity/finalization path replacing the
current stub) would finalize the tip, σ−1 blocks too shallow. Latent today
because the method has no callers.

Observed at zebra-crosslink `6d02a1b` (`chain.rs:52-54,124-126,220`;
`lib.rs:414-439,809`; `zebra-state src/service/read/find.rs:414,526`,
`service.rs:1720-1743`); tfl-book `fe6e1d6f` (`construction.md:420,427`).

---

**Not re-filed — duplicate of Wave-0 entry 21.** A 16th Wave-1 raw finding
(voting-circuits `src/delegation/README.md:300` "all 16 proposals" vs the
circuit/chain cap of 15) is the same defect as dossier entry 21; the Wave-1
firsthand cross-checks (voting-circuits `4c39abd`
`src/vote_proof/circuit.rs:123-143`, `gadgets/authority_decrement.rs:214,315`,
test `proposal_id_zero_fails` `circuit.rs:2599-2608`; vote-sdk `cb915f5`
`x/vote/types/keys.go:43,48`, `msgs.go:127-128`) strengthen entry 21's evidence
but add no new defect.

---

# Wave-2 model-diff findings (DRAFT — needs owner confirmation before filing)

**DRAFT.** These 7 entries come from the Wave-2 breadth-first model-diff pass
(2026-07-16), firsthand-cited but not yet owner-reviewed. Do not file upstream until
each is confirmed. Numbering continues the dossier (33-39). Ground-truth pins:
zebra-crosslink `6d02a1b` (HEAD = `6d02a1b80f896d08f923e39b2505f0565efb5787`);
librustzcash `e30517e4`, `StakingAction` at ShieldedLabs rev `33dc74bf`; orchard
`bef8a27`; tfl-book `fe6e1d6f`. All paths under zebra-crosslink are
`zebra-crosslink/zebra-crosslink/…` unless noted `zebra-chain/…` / `zebra-state/…` /
`zebra-consensus/…`.

Severity spread: **4 high, 3 medium** — every entry a zebra-crosslink code bug on the
BFT / finalization / staking path, again clustering on `lib.rs`
`new_decided_bft_block_from_malachite` / `validate_bft_block_from_malachite`.

**Dedup notes (this wave).** Raw yield was 12 findings; folded to 7:
BftBlock.height index/fill-loop (raw 2+7 → **34**); empty-headers panic (raw 8+9 →
**35**); decide-path Pass-assert on Indeterminate (raw 4+10 → **39**); reward-loop
overflow + divide-by-zero (raw 6+12 → **38**). One raw finding (`BftBlock::try_from`
unimplemented, `chain.rs:129-151`) is a **duplicate of Wave-1 entry 31** and is *not*
re-filed; see the note after entry 39. Two entries are new failure-mode facets of
already-drafted roots, flagged inline: **36** extends the unauthorized-roster-mutation
root of #25 (theft/eviction of *others'* stake vs self-mint); **37** is a new
mechanism in the finalization-safety family of #23/#27 (no best-chain constraint on
the fin candidate). Genuinely new roots this wave: **33, 34, 35, 38, 39**.

---

## 33. zebra-crosslink — every finalizer's ed25519 signing key is derived deterministically from a public address string (forgeable roster)

**DRAFT. Severity: high.**

**Title:** `rng_private_public_key_from_address` derives each finalizer's ed25519
private signing key from a public peer-address string via a non-cryptographic 64-bit
`DefaultHasher` seed, so anyone who knows the (public) finalizer multiaddrs can
recompute every roster private key and forge a full-quorum notarization

**Body:**

Every ed25519 signing key in the crate is a pure, publicly-computable function of a
public string. `lib.rs:334-344` `rng_private_public_key_from_address(addr: &[u8])`:
`let mut hasher = DefaultHasher::new(); hasher.write(addr); let seed =
hasher.finish(); let mut rng = StdRng::seed_from_u64(seed); let private_key =
MalPrivateKey::new(&mut rng); …`. `DefaultHasher` is std's fixed-key SipHash
(`lib.rs:26`), so `seed` is deterministic; `MalPrivateKey` = `ed25519_zebra::SigningKey`
(`malctx.rs:39`) and `lib.rs:341` is the **only** `MalPrivateKey::new` site in the
crate — no secret is ever read from disk or config (Config `lib.rs:103-115` has no
signing-key field; `insecure_user_name`'s own docstring reads "temp seed for
private/public key pair").

The roster is minted from public peer strings: `service.rs:125-128` iterates
`config.malachite_peers` (docstring "List of public IP addresses for peers") and for
each calls `rng_private_public_key_from_address(peer.as_bytes())`, pushing
`MalValidator::new(public_key, 1)`. Each finalizer's own key comes from `user_name`
(= `insecure_user_name`, else public address) at `lib.rs:1106-1114`. The resulting
`my_private_key` is handed to `tenderlink::entry_point` (`lib.rs:1206`) and used to
sign Precommit/Proposal ballots (`malctx.rs:571-586`
`self.private_key.sign(&vote.to_bytes())`) — so the forgeable key *is* the real
signing key.

Spec: tfl-book `construction.md` @ `fe6e1d6f:153` "validator keys of honest nodes
must remain secret indefinitely"; `:150-152` a compromised key casting non-honest
units breaks the one-third bound and thus Final Agreement (`~:205`). Here no key is
secret: all are recomputable from public inputs, and the 64-bit non-crypto seed makes
brute force feasible even for a withheld address.

Distinct from Wave-1 entry 22 (the *verify* side — notarization checks neither roster
membership nor the 2/3 threshold): #22 is about the missing checks; this is that the
keys those checks would authenticate against are themselves forgeable — a deeper,
independent defect. Tied to entry 36 (staking commands also key off the same
name-derived keypairs).

**Failure mode.** Attacker enumerates the finalizer peer addresses from
`config.malachite_peers` (network multiaddrs are public by construction), recomputes
every roster `SigningKey` with the same derivation, and signs valid Precommit ballots
as ≥2/3 of the roster over two conflicting `BftBlock` hashes at one height. Both fat
pointers pass `validate_signatures()` (`lib.rs:532`) *and* any future roster/threshold
check (the attacker holds genuine roster keys), so two honest nodes crosslink-finalize
disagreeing blocks — Final Agreement (`construction.md:205`) violated.

Observed at zebra-crosslink `6d02a1b` (`lib.rs:26,103-115,334-344,532,1106-1114,1206`;
`service.rs:125-128`; `malctx.rs:39,571-586`); tfl-book `fe6e1d6f`
(`construction.md:150-153,205`).

---

## 34. zebra-crosslink — attacker-controlled `BftBlock.height` drives an unbounded fill loop and a `usize` index base in the decided-block handler

**DRAFT. Severity: high.**

**Title:** `new_decided_bft_block_from_malachite` computes `insert_i =
new_block.height as usize - 1` and a placeholder fill-loop bound from
`BftBlock.height`, a raw attacker-controlled u32 that neither `zcash_deserialize` nor
`validate_bft_block_from_malachite` bounds — so `height ∈ {0, huge, stale}` yields
`usize` underflow, multi-billion-element allocation, or an index-mismatch assert, each
fatal under `panic = "abort"`

**Body:**

The decided handler (`lib.rs:499`, wired as `ClosureToPushDecidedBlock`
`lib.rs:1234-1247`, runs on every node at decision then crosslink-finalizes at `:581`)
uses `new_block.height` unchecked: `lib.rs:546` `let insert_i = new_block.height as
usize - 1;`; `lib.rs:549-561` `for i in internal.bft_blocks.len()..=insert_i { …
internal.bft_blocks.push(BftBlock{ … }) }`; then `lib.rs:563-568`
`assert_eq!(internal.bft_blocks[insert_i - 1].blake3_hash(),
new_block.previous_block_fat_ptr.points_at_block_hash())` and `:570-575`
`assert!(internal.bft_blocks[insert_i].headers.is_empty(), …)`. The fill loop runs
**before** the asserts.

`height` is read raw at `chain.rs:95` `let height =
reader.read_u32::<LittleEndian>()?;` with no bound (only `header_count` is capped, at
2048, `chain.rs:99-104`), and `validate_bft_block_from_malachite_already_locked`
(`lib.rs:790-820`) never inspects it — it checks only prev-pointer linkage (`:798-807`)
and that `headers.first()` is a known PoW block (`:809-819`), then returns `Pass`.
`points_at_block_hash()` (`lib.rs:1944-1950`) is a hash of the *previous* block,
independent of the new block's own `height`, so the linkage guard does not constrain
it. A legitimate proposer sets `height = bft_blocks.len() + 1` (`lib.rs:445`); a
Byzantine proposer's raw bytes (deserialized at `lib.rs:1242`) carry any value, and
`blake3_hash()` serializes the whole struct incl. height (`chain.rs:81,166-178`) so a
genuinely-decided Byzantine block passes the `:523` hash-binding and `:532` signature
checks and reaches `:546`. `Cargo.toml` `[profile.release]` sets `panic = "abort"`
with no `overflow-checks`, so subtraction wraps in release and every panic hard-aborts
the process.

Distinct from Wave-1 entry 24 (explicit `panic!()` at 529/534/1248) and entry 26
(`finalization_candidate_height = 0`): the vector here is the unbounded fill loop /
`usize` underflow driven by the separate `height` field. Folds raw Wave-2 findings 2
and 7.

**Failure mode.** A round's proposer sets `previous_block_fat_ptr` to the current BFT
tip (so validate → Pass) but an adversarial `height`: `height = 0` → `0usize - 1`
underflows (panic in debug; `usize::MAX` → multi-billion-element push → OOM abort in
release); `height = u32::MAX` → ~4.3×10⁹ `BftBlock` pushes → OOM; `height = len + 2`
→ one placeholder pushed, then `assert_eq!` at `:564` compares the empty placeholder's
hash to the real previous pointer and panics. Every honest node crashes simultaneously
on the same decided value — network-wide halt from one Byzantine proposer.

Observed at zebra-crosslink `6d02a1b` (`lib.rs:445,499,523,532,546-575,581,790-820,
1234-1247,1242,1944-1950`; `chain.rs:81,95,99-104,166-178`; `Cargo.toml:201-202`).

---

## 35. zebra-crosslink — a `BftBlock` with zero PoW headers deserializes and panics every validating node on the pre-vote path

**DRAFT. Severity: high.**

**Title:** `BftBlock::zcash_deserialize` bounds `header_count` only from above
(rejects >2048, accepts 0), and `validate_bft_block_from_malachite` dereferences
`headers.first().expect("at least 1 header")` — so a proposal with `header_count = 0`
aborts every validator pre-vote under `panic = "abort"`

**Body:**

`ZcashDeserialize for BftBlock` (`chain.rs:98-108`) reads `header_count`, rejects only
`> 2048` (`chain.rs:99-104`), then loops `for i in 0..header_count` — so `header_count
= 0` yields `Ok(BftBlock { headers: [] })`. The exactly-σ invariant lives only in
`BftBlock::try_from` (`chain.rs:136-140`), which the deserialize path never calls (its
own `TODO` at `chain.rs:48`: "Ensure deserialization delegates to
`BftBlock::try_from`").

The proposal-validation closure `ClosureToValidateProposedBlock` (`lib.rs:1220-1231`)
deserializes untrusted proposal bytes and calls `validate_bft_block_from_malachite` →
`_already_locked` (`lib.rs:790-820`), whose only guard before the dereference is the
prev-pointer hash compare (`:798-807`, no signature check, no header-count check);
then `lib.rs:809` `let new_final_hash = new_block.headers.first().expect("at least 1
header").hash();` panics on the empty Vec. At genesis `internal.fat_pointer_to_tip =
FatPointerToBftBlock2::null()` (`service.rs:158`), whose `points_at_block_hash()` is
`[0;32]` (`lib.rs:1878-1883,1944-1950`); an attacker's matching null previous pointer
makes the `:798` guard pass. The crosslink validate path does **no** signature
verification (sigs are checked only on the decided path, `lib.rs:532-534`), so the
panic is reached pre-vote with no valid signatures. `Cargo.toml` `[profile.dev]`/
`[profile.release]` both `panic = "abort"`; no `catch_unwind` guards the closure; the
spawn at `lib.rs:1205` is unconditional.

Distinct from Wave-1 entries 23/16 (first-vs-last / σ-depth semantics) — this is the
empty-Vec deserialize + unwrap on the untrusted proposal path. Folds raw Wave-2
findings 8 and 9.

**Failure mode.** Any malachite participant proposes `BftBlock{
previous_block_fat_ptr = current tip fat ptr (satisfies the :798 hash check),
headers: [] }`. It serializes (`header_count = 0`) and deserializes fine; on every
validator, `ClosureToValidateProposedBlock` → `validate_bft_block_from_malachite` →
`lib.rs:809` `.first().expect(…)` panics → process abort. One malformed proposal =
fleet-wide DoS, no valid signatures required. (Decided-path twins at `lib.rs:543` and
the assert at `:575` corroborate the empty-Vec assumption but require valid sigs.)

Observed at zebra-crosslink `6d02a1b` (`chain.rs:48,98-108,125,136-140`;
`lib.rs:532-534,543,575,790-820,809,1205,1220-1231,1878-1883,1944-1950`;
`service.rs:158`; `Cargo.toml:173,202`).

---

## 36. zebra-crosslink / librustzcash — a finalized staking transaction can subtract, zero, or MOVE any existing finalizer's voting power to an attacker key with no authorization

**DRAFT. Severity: high.**

**Title:** `StakingAction` carries no signature and `update_roster_for_cmd` performs
no submitter authorization, so a `VCrosslink` staking tx built from public finalizer
*name strings* can evict (`Sub`/`Clear`) or steal (`Move`/`MoveClear`) another
finalizer's entire BFT voting power — theft of *others'* stake, not just self-mint

**Body:**

`StakingAction` (librustzcash `zcash_primitives/src/transaction/mod.rs:1381-1389` @
rev `33dc74bf`) has **no** signature field (`kind, val, target, source,
insecure_target_name, insecure_source_name`); `hash_to_state` (`:1390`) writes the
fields into a sighash state but nothing verifies a signature against it for a staking
tx. Keys are name-derived: `parse_from_cmd` (`:1414-1519`) runs the same
`rng_private_public_key_from_address` as entry 33 over the command's name strings, so
`source`/`target` are fixed keypairs recoverable from a victim's *public name*.

`update_roster_for_cmd` (`lib.rs:988-1061`) applies commands with no submitter check:
`Sub`/`Clear` → operate on `action.target`; `Move`/`MoveClear` → subtract from
`action.source` and add to `action.target` (`:1050-1058`). For `is_clear`, `amount =
member.voting_power - action.val` (`:1044`), so `val = 0` zeroes the victim regardless
of its power (the `:1035` guard always passes at `val = 0`). `update_roster_for_block`
(`lib.rs:1063-1081`) applies every finalized tx's staking action unconditionally, from
the real decided-block callback (`lib.rs:724`). Consensus never authenticates it:
`has_inputs_and_outputs` (`zebra-consensus src/transaction/check.rs:124-130`) returns
`Ok(())` for any `VCrosslink` with `staking_action.is_some()`, and
`verify_v5_transaction` (`transaction.rs:529-536`, body `972-997`) inspects only
transparent/Sapling/Orchard bundles — a staking tx has none. A grep for
authorization/signature tied to staking/roster/voting returns empty.

Spec: tfl-book `goals.md:17` "PoS consensus providers … cannot steal those
[delegated] funds"; `potential-changes.md:287` validators must hold stake to vote.

Distinct from Wave-1 entry 25 (unbacked self-mint via `Add`) and entry 22 (roster keys
trusted): same missing-authorization root as #25, but the exploitation direction here
is **theft/eviction of other validators' existing stake** via `Sub`/`Clear`/`Move`/
`MoveClear`, sharpened by the name-derived keys of entry 33. Filed as a new entry for
those failure modes; owner may choose to merge into #25's root when filing.

**Failure mode.** Attacker broadcasts `VCrosslink{ staking_action:
parse_from_cmd("MCL|0|attacker|victimname") }` (MoveClear victim → attacker). It passes
mempool + consensus (no inputs needed), is mined and BFT-finalized, and every node's
`update_roster_for_cmd` moves the victim's entire `voting_power` to the attacker's key.
Repeat across honest finalizers → attacker gains a BFT supermajority (finalize
arbitrary blocks / halt finalization). `"CLR|0|victimname"` instead zeroes an honest
finalizer, evicting it. No victim private key is needed — keys are name-derived.

Observed at zebra-crosslink `6d02a1b` (`lib.rs:724,988-1061,1063-1081`;
`zebra-consensus src/transaction/check.rs:124-130`, `src/transaction.rs:529-536,
972-997`); librustzcash rev `33dc74bf` (`zcash_primitives/src/transaction/mod.rs:
1381-1389,1390,1414-1519`); tfl-book `fe6e1d6f` (`goals.md:17`,
`potential-changes.md:287`).

---

## 37. zebra-crosslink — the proposal-validation closure never constrains the finalization candidate to the best chain, so a Byzantine proposer can force a reorg onto an attacker fork

**DRAFT. Severity: medium.**

**Title:** `validate_bft_block_from_malachite` accepts any `KnownBlock` as the
finalization candidate (`headers.first()`) with no best-chain-membership, σ-depth, or
descent check, and discards the `KnownBlock.location` (BestChain/SideChain)
discriminator; on decide, `crosslink_finalize` drops every chain not containing that
hash — forcing all honest nodes onto an attacker-chosen fork

**Body:**

`validate_bft_block_from_malachite_already_locked` (`lib.rs:798-820`) imposes only a
BFT-linkage check (`:798-807`, prev-pointer hash) and existence of `headers.first()`
at some PoW height (`:809-819`), then returns `Pass`. It never compares the candidate
height to tip−σ, never checks best-chain membership, and never checks descent from the
previous final block. The location discriminator is available but thrown away:
`block_height_from_hash` (`lib.rs:185-193`) matches `StateResponse::KnownBlock(Some(kb))`
and returns only `kb.height`, dropping `kb.location` — which is exactly BestChain vs
SideChain (`zebra-state src/service/read/find.rs:142-161`
`non_finalized_state_contains_block_hash` returns `SideChain` for side-chain blocks;
`service.rs:1166-1184` `Request::KnownBlock` = non-finalized (any chain) OR finalized
DB). This validate closure is the sole proposal-validity predicate before precommit
(`lib.rs:1220-1233`).

On decide, `new_decided_bft_block_from_malachite` recomputes `new_final_hash =
headers.first().hash()` (`lib.rs:543`) and issues `CrosslinkFinalizeBlock`
(`lib.rs:581`). `crosslink_finalize` (`zebra-state
src/service/non_finalized_state.rs:264-292`) does `find_chain(|c|
c.height_by_hash(hash).is_some())` then `chain_set.retain(|c|
c.contains_block_hash(hash))` (`:276`) — dropping every chain, including the current
best chain, not containing the hash; `write.rs:342-375` then commits the retained
prefix to the permanent finalized DB and rebroadcasts the new tip. The depth guard is
disabled (`lib.rs:545` commented out), and `BftBlock::try_from`'s documented
validations remain a stub (`chain.rs:129-151`, used only by the local proposer,
`lib.rs:443`).

New mechanism in the finalization-safety family of Wave-1 entry 23 (σ−1 depth) and
entry 27 (no-rollback `updatefin`): the specific novel gap is that the *validate*
closure never constrains the candidate to the canonical best chain, and the
`KnownBlock.location` field that would allow it is discarded. Owner may file under the
same finalization-safety root.

**Failure mode.** A Byzantine proposer sets `headers.first()` to a valid PoW block on a
competing (non-best) fork present in nodes' non-finalized state (or one shallower than
σ). `validate` → `Pass` (block is a `KnownBlock`, prev pointer matches the BFT tip);
≥2/3 honest finalizers precommit; on decide, `crosslink_finalize` retains only the fork
containing that block and drops the current best chain — every honest node reorgs onto
the attacker-chosen fork (double-spend / shallow-finalization enabler).

Observed at zebra-crosslink `6d02a1b` (`lib.rs:185-193,443,543,545,581,798-820,
1220-1233`; `chain.rs:129-151`; `zebra-state src/service/read/find.rs:142-161`,
`src/service.rs:1166-1184`, `src/service/non_finalized_state.rs:264-292`,
`src/service/write.rs:342-375`).

---

## 38. zebra-crosslink — unchecked u64 accumulation of attacker-controlled `val` in the reward/roster loop overflows (debug: node-wide abort; release: wrap → divide-by-zero / corrupted quorum)

**DRAFT. Severity: medium.**

**Title:** The finalizer-reward loop accumulates `total_voting_power` / `voting_power`
with plain `+=` over an attacker-supplied, uncapped `val` (up to `u64::MAX`); a large
`Add`, or sums that are a multiple of 2⁶⁴, overflow the accumulator — hard-aborting
every node in debug, or wrapping `total_voting_power` to 0 and dividing by zero at
`lib.rs:695` in release

**Body:**

Accumulation is plain u64: `lib.rs:655` `let mut total_voting_power = 0;` then `:672`
`total_voting_power += finalizer.voting_power;`; `:697` `finalizer.voting_power +=
reward;`; `:718` `finalizer.voting_power += rem_reward;` (with `pos_total_reward =
6000`, `:631`); `:487` roster-builder sum; `:1053` `member.voting_power += amount;`,
`:1055` `MalValidator::new(add_key.0, amount)`. Only the multiply was hardened (`:692`
`// TODO: most numerically stable version of this that won't overflow`, cast to u128);
every `+=` stayed u64. The loop relies on an invariant it can break: `:690` `// NOTE:
total_voting_power must be non-0 if we have any non-0 roster members`, feeding
`:695`/`:706` `let reward = (mul / (total_voting_power as u128)) as u64;`.

`val` is unbounded: librustzcash rev `33dc74bf` `zcash_primitives/src/transaction/
mod.rs:1383` `pub val: u64`, `parse_from_cmd` does `str::parse::<u64>` with no cap and
`read` does `u64::from_le_bytes` with no bound; `zebra-consensus
src/transaction/check.rs:124-130` returns `Ok` early for staking txs (no value cap),
and the `Add` path in `update_roster_for_cmd` has no bound (the `:1035` guard is only
on the `Sub`/`Clear` path). The reward loop runs on every node via
`ClosureToPushDecidedBlock` (`lib.rs:1234-1247`) → deterministic re-execution. Both
`[profile.dev]` and `[profile.release]` set `panic = "abort"`; release sets no
`overflow-checks` (silent wrap). `malctx.rs:737-739` `total_voting_power()` sums
`voting_power` and feeds malachite's quorum threshold, so a wrapped total corrupts BFT
quorum math.

Distinct from Wave-1 entries 24/28 (a new panic/wrap *site* on the reward/roster path)
and entry 25 (self-mint authorization); enabled by #25's uncapped, unauthorized `val`.
Folds raw Wave-2 finding 12 (the divide-by-zero facet).

**Failure mode.** Attacker submits `Add` with `val = u64::MAX` (or two `Add`s of ~2⁶³
to two keys). At finalization: **debug** (`debug-assertions` + `panic = "abort"`) →
`total_voting_power += …` (`:672`) or `voting_power += rem_reward` (`:718`) panics
"attempt to add with overflow" → hard abort on every node re-executing the finalized
block → deterministic consensus halt. **Release** → two ADDs summing to 2⁶⁴ wrap
`total_voting_power` to 0; the non-max finalizer branch hits `mul / 0` at `:695` →
divide-by-zero (panics even in release) → abort; lesser wraps silently corrupt
`total_voting_power()`/quorum at `malctx.rs:738` and can trip the `:708`
`assert!(reward <= rem_reward)`.

Observed at zebra-crosslink `6d02a1b` (`lib.rs:487,631,655,672,690-697,706-718,
1020,1035,1053-1055,1234-1247`; `malctx.rs:737-739`; `zebra-consensus
src/transaction/check.rs:124-130`; `Cargo.toml:172,201`); librustzcash rev `33dc74bf`
(`zcash_primitives/src/transaction/mod.rs:1383`).

---

## 39. zebra-crosslink — the decided-block handler's `assert_eq!(validate…, Pass)` and height `.unwrap()` abort the node on a legitimately-`Indeterminate` block (benign catch-up / reorg race)

**DRAFT. Severity: medium.**

**Title:** `new_decided_bft_block_from_malachite` re-validates a decided block with a
hard `assert_eq!(…, TMStatus::Pass)` and `block_height_from_hash(…).unwrap()`, but
`validate` returns the recoverable `Indeterminate` exactly when the referenced PoW
block is locally absent — so a validator behind on PoW sync (or after a benign reorg
prunes the candidate) aborts on otherwise-legitimate consensus output

**Body:**

The decide handler asserts validation equals `Pass` (`lib.rs:537-541`) then unwraps the
height (`lib.rs:543-544` `block_height_from_hash(&call, new_final_hash).await
.unwrap()`). But `validate_bft_block_from_malachite_already_locked` returns
`Indeterminate` precisely when the referenced PoW block is absent: `lib.rs:809-819`
`if let Some(h) = block_height_from_hash(…) { h.0 } else { warn!(…); return
Indeterminate }`, and `block_height_from_hash` returns `None` whenever `KnownBlock` is
`None` (`lib.rs:185-192`) — i.e. the hash is in neither the non-finalized state nor the
finalized DB (`zebra-state src/service.rs:1166-1183`, `read/find.rs:142-180`). The
internal mutex (`lib.rs:507`) does not lock zebra-state, so the PoW-block set can change
between vote and decide. `assert_eq!` is not stripped in release; both dev and release
set `panic = "abort"` (`Cargo.toml:173,202`), so the assert/unwrap abort the whole
process.

Reachability is benign, not just adversarial: the proposer picks the finalization
candidate at `bc_confirmation_depth_sigma = 3` below its own tip (`chain.rs:220`,
`lib.rs:379-381,414-439`), so `headers.first()` is a very recent PoW block. A validator
momentarily behind on PoW propagation (or briefly partitioned from block relay but
connected to BFT peers) returns `Indeterminate` at both vote and decide time; when the
≥2/3 who have the block drive it to a decision, tenderlink delivers the decided block to
the lagging node → `assert_eq!(Indeterminate, Pass)` aborts (or `.unwrap()` at `:544`
hits `None`). The sibling `force_feed_pos` (`service.rs:172-181`) *does* gate on
`== Pass` before calling the handler — proving maintainers know non-`Pass` at decide
time is possible — yet the tenderlink `ClosureToPushDecidedBlock` path (`lib.rs:1234-1247`)
omits the gate. The `:529`/`:534` `panic!()`s (Wave-1 entry 24) are for
malformed/malicious blocks and do not preempt an honest, well-signed block whose only
problem is local PoW-block absence.

Distinct from Wave-1 entry 24 (explicit `panic!()` at 529/534/1248, on malformed
input): same handler, different lines (537 assert, 544 unwrap) and a benign trigger
(honest catch-up / reorg timing). Folds raw Wave-2 findings 4 and 10. The Crosslink
Guide describes the vote-path check accurately (`crosslink-guide.tex:2319-2334`) and
even invites adversarial review of BFT/PoW-reorg interleaving — the guide is not wrong;
the defect is in the code.

**Failure mode.** A validator votes for a proposal whose finalization candidate it has
not yet synced (or which sits on a short-lived side chain pruned before decision);
`block_height_from_hash` → `None` → `validate` → `Indeterminate` →
`assert_eq!(Indeterminate, Pass)` panics (or `.unwrap()` at `:544` panics) → the node
crashes on benign consensus output. Also weaponizable by proposing a block referencing
a header peers lack.

Observed at zebra-crosslink `6d02a1b` (`lib.rs:185-192,379-381,414-439,499,507,
529,534,537-544,809-819,1234-1247`; `chain.rs:220`; `service.rs:172-181`;
`zebra-state src/service.rs:1166-1183`, `src/service/read/find.rs:142-180`;
`Cargo.toml:173,202`); crosslink-guide.tex:2319-2334.

---

**Not re-filed — duplicate of Wave-1 entry 31.** A raw Wave-2 finding
(`BftBlock::try_from` documents four stateless validations — count = σ, known version,
header ordering, PoW-solution validity — but implements only the header-count check,
logs `error!("not yet implemented: all the documented validations")` at `chain.rs:142`,
hard-codes `version: 1`, and `zcash_deserialize` bypasses the constructor entirely —
`chain.rs:129-151,92-118,48`) is the same defect as dossier entry 31. The Wave-2
firsthand cross-checks (doc contract `chain.rs:33-38`; deserialize/decide paths
`lib.rs:1226,1242` never calling `try_from`; no PoW/version/ordering check on
`headers[1..σ]`) strengthen entry 31's evidence but add no new defect.

---

# Wave-3 model-diff findings (DRAFT — needs owner confirmation before filing)

**DRAFT.** These 5 entries come from the Wave-3 **new-axis** model-diff pass
(2026-07-16), firsthand-cited but not yet owner-reviewed. Do not file upstream until
each is confirmed. Numbering continues the dossier (40-44). Ground-truth pins: zaino
`0e057e22`, lightwalletd `61fee32`; reddsa `3792daa`
(`3792daa95e588c1af6bd4805105bfb6ea7e9ad49`, v0.5.2); frost / frost-core `2016e44`;
orchard-zsa (QED-it) `cf801a5`, librustzcash-zsa (QED-it) `3f9b53f`; deployed orchard
`0.10.0`; upstream Ironwood orchard `bef8a27`.

This wave deliberately left the Ironwood / Crosslink veins and hit three fresh
surfaces: Zaino's gRPC service backends (`zaino-state`, `zaino-proto`), the FROST
crates (`reddsa`, `frost-core`), and the QED-it ZSA fork's flags parser. Severity
spread: **2 medium, 3 low**. The two mediums are genuine code-correctness roots on
*different* fresh repos — a Zaino backend hash-vs-height bug (#40) and a QED-it fork
consensus-split on v5 reserved bits (#43). The three lows are documentation/comment
defects (two of them the same reddsa comment, reported twice by the raw pass).

**Dedup notes (this wave).** Raw yield was 6 findings, folded to 5: the reddsa `EvenY`
inverted doc-comment was reported twice (raw items 2 and 5 — identical defect at
`redpallas.rs:328-334`) → single entry **41**. Checked against the whole dossier:
**#40/#44** (Zaino backends) are distinct from **#3** (Zaino's
`lightwalletProtocolVersion` string constant); **#43** (v5 vanilla flags bit 2) is
explicitly *not* covered by **#4-8** (ZIP citations, burn bound, split-note ψ, lead
byte, ZIP-246 digest tree) — it is the flags `from_byte` reserved-bit gate, a separate
root in the same fork. Genuinely new roots this wave: **all five (40-44)**; none
duplicates a prior entry.

---

## 40. zaino — StateService backend's `get_block_nullifiers` ignores `BlockId.hash` and reads only `height`, silently returning genesis nullifier data for a hash-identified block

**DRAFT. Severity: medium.**

**Title:** `LightWalletIndexer::get_block_nullifiers` on the StateService backend never
reads `request.hash`, so a `GetBlockNullifiers` request identifying a block by hash (the
standard `height = 0` hash-lookup convention) resolves to `Height(0)` and returns
genesis's nullifier set — diverging from zaino's own FetchService backend and from
lightwalletd, both of which resolve the hash first

**Body:**

`BlockId` is `{height: u64 (tag 1), hash: Vec<u8> (tag 2)}`
(`zaino-proto/src/proto/service.rs:31-36`). The StateService backend's
`get_block_nullifiers` (`packages/zaino-state/src/backends/state.rs:2033-2058`) does
`let height: u32 = request.height.try_into()…?; let block_height =
chain_types::Height(height); … get_compact_block(&snapshot, block_height,
PoolTypeFilter::includes_all()) …; Ok(Some(block)) =>
Ok(compact_block_to_nullifiers(block))` — `request.hash` is **never read**. A client
following the conventional hash lookup (hash set, height left `0`) lands on `Height(0)`
= genesis, so the method returns genesis's compact/nullifier data for any
hash-identified block.

Internal inconsistency: the *same* backend's `get_block` (`state.rs:1954-1976`) **does**
resolve hash via `blockid_to_hashorheight` + `get_block_height`; only
`get_block_nullifiers` skips it. The FetchService backend's `get_block_nullifiers`
(`fetch.rs:1011-1035`) resolves correctly — `blockid_to_hashorheight(request)` →
`HashOrHeight::Hash(hash)` → `indexer.get_block_height(&snapshot, hash.into())`, erroring
"Hash not founf in chain" (sic) if absent. `blockid_to_hashorheight`
(`zaino-proto/src/proto/utils.rs:312-323`) does
`<[u8;32]>::try_from(block_id.hash).map(Hash)…or_else(height)` — a 32-byte hash wins over
height, matching lightwalletd's precedence: `frontend/service.go:193-206` ("// Precedence:
a hash is more specific than a height. If we have it, use it first.") returns
`InvalidArgument "GetBlockNullifiers: GetBlock by Hash is not yet implemented"` rather than
silently falling through to height. The gRPC dispatch passes `BlockId` through raw with no
resolution (`zaino-serve/src/rpc/grpc/service.rs:169`). StateService is a
production-selectable backend: `zainod/src/config.rs:75 pub backend: BackendType`;
`zainod/src/indexer.rs:66 BackendType::State =>` instantiates it.

**Failure mode.** A client calls `GetBlockNullifiers` identifying the block by its
32-byte hash (height field left `0`). Against the StateService backend it returns a
CompactBlock / nullifier set for height 0 — genesis's hash and empty/wrong nullifier set
— rather than the block whose hash was supplied: silent wrong-block data feeding shielded
spend detection. Separately, after a reorg a client sending a *correct* hash plus a stale
height gets the stale-height block on StateService while FetchService and lightwalletd
return the hash's block — a silent backend divergence on identical requests.

Observed at zaino `0e057e22` (`packages/zaino-state/src/backends/state.rs:2033-2058,
1954-1976`; `packages/zaino-state/src/backends/fetch.rs:1011-1035`;
`zaino-proto/src/proto/service.rs:31-36`, `zaino-proto/src/proto/utils.rs:312-323`;
`zaino-serve/src/rpc/grpc/service.rs:169`; `zainod/src/config.rs:75`,
`zainod/src/indexer.rs:66`); lightwalletd `61fee32` (`frontend/service.go:193-206`).

---

## 41. reddsa — RedPallas `EvenY` trait doc-comment says the keys are negated "if Y is even", but the code negates when Y is ODD (inverted main clause)

**DRAFT. Severity: low.**

**Title:** The `EvenY` even-Y-normalization doc-comment states negation happens "if Y is
even"; the code negates when `!is_even`, i.e. when Y is ODD — the main clause is inverted
and self-contradictory with its own parenthetical, in the deployed ZIP-312 reference
implementation the FROST Guide pins

**Body:**

reddsa `3792daa` (v0.5.2), `src/frost/redpallas.rs`. Doc-comment (`:328-334`): "This is
done by simply negating both keys if Y is even (in a field, negating is equivalent to
computing p - x where p is the prime modulus. Since p is odd, if x is odd then the result
will be even)." Code: `has_even_y()` (`:349-355`) returns `verifying_key_serialized[31] &
0x80 == 0` — true when the sign bit is clear, i.e. Y **EVEN**; `into_even_y()`
(`:358-360`) `let is_even = is_even.unwrap_or_else(|| self.has_even_y()); if !is_even {
… -self.verifying_key().to_element() … } else { self }` — negates when `!is_even`, i.e. Y
**ODD**. Same negate-when-odd pattern for `SecretShare` (`:389-391`) and `KeyPackage`
(`:425-427`). The main clause "negating … if Y is even" is the opposite of the code; the
parenthetical ("if x is odd then the result will be even") correctly reasons about
negating an ODD coordinate to obtain an even one — contradicting its own main clause.
Blame `29162a78` (Conrado Gouvea, 2023-11-28), unchanged at the pinned HEAD.

**Failure mode.** An auditor/re-implementer deriving even-Y normalization from the
comment negates precisely when Y is already even and leaves odd-Y keys unchanged —
producing an ODD-Y `ak`. Orchard consensus requires `ak` to have even Y (protocol.pdf
orchardkeycomponents / ZIP 2005), so RedPallas spend-authorization signatures produced
under such a key fail full-node verification. No runtime impact today: the shipped code
is correct and round-trip-tested; the hazard is a security-critical comment that inverts
the normalization direction, and a well-meaning "fix" to match the comment would invert
the currently-correct code. The FROST Guide is *not* at fault: `frost-guide.tex:1480-1486`
(§`sec:fr-rerand-impl`) and `:1666-1672` describe negation "whenever the serialised key
has ỹ = 1" (ỹ = 1 denotes ODD y) — matching the code and ZIP 2005 / protocol-spec §4.2.3.

Observed at reddsa `3792daa` (`src/frost/redpallas.rs:328-334,349-355,358-360,389-391,
425-427`); guide correct at `frost-guide.tex:1480-1486,1666-1672`.

---

## 42. frost-core — batch-verifier doc-comment says the blinding scalar `z_i` is "a random 128-bit Scalar", but the code samples a full-width field element (stale wording copied from reddsa)

**DRAFT. Severity: low.**

**Title:** `frost-core/src/batch.rs` documents `z_i` as "a random 128-bit Scalar" while
the code samples a full-width scalar via `Field::random`; the 128-bit wording was copied
verbatim from reddsa's batch verifier (where it is accurate) and never updated for the
generic frost-core code

**Body:**

frost `2016e44`, `frost-core/src/batch.rs:102` doc line `/// - z_i is a random 128-bit
Scalar;`. The actual sampling at `batch.rs:129` is `let blind = <<C::Group as
Group>::Field>::random(&mut rng);`. The `Field::random` contract
(`frost-core/src/traits.rs:54-57`) is "/// Generate a random scalar from the entire space
[0, l-1]" — full-width; the concrete impl `frost-ristretto255/src/lib.rs:63-65` is
`Scalar::random(rng)` (uniform over the whole scalar field). The same docblock cites the
RedDSA batch spec (`batch.rs:111` → `zips.z.cash/protocol/protocol.pdf#reddsabatchverify`).
In reddsa `3792daa` the wording IS accurate: `gen_128_bits` (`src/batch.rs:33-42`) sets
only `bytes[0]`/`bytes[1]` ("The final 128 bits are zero") and `src/batch.rs:241` does
`let z = S::Scalar::from_raw(gen_128_bits(&mut rng));`, matching the identical comment at
`src/batch.rs:171`. So the "128-bit" line was copied from reddsa into generic frost-core
and never updated; frost-core samples a full-width field element.

**Failure mode.** An auditor verifying frost-core batch soundness against the cited
RedDSA batch spec (128-bit blinds) is told the blinds are 128-bit while they are
full-width; the code silently deviates from the referenced spec. The deviation is in the
safe direction (larger blinds are not weaker), so no exploit — but the mis-description
could mask a genuine width regression under future edits. Documentation defect only.

Observed at frost `2016e44` (`frost-core/src/batch.rs:102,111,129`;
`frost-core/src/traits.rs:54-57`; `frost-ristretto255/src/lib.rs:63-65`); reddsa
`3792daa` (`src/batch.rs:33-42,171,241`).

---

## 43. orchard-zsa / librustzcash-zsa (QED-it forks) — shared `Flags::from_byte` accepts `flagsOrchard` bit 2 with no bundle-format gate, so a legacy v5 OrchardVanilla tx with a set reserved bit is accepted instead of rejected (chain split)

**DRAFT. Severity: medium.**

**Title:** The ZSA fork's non-generic `Flags::from_byte` treats `flagsOrchard` bit 2
(its `enableZSAs` flag, `0b0000_0100`) as always-allowed, with no format/flavor
parameter, and is used to parse BOTH v6 OrchardZSA and legacy v5 OrchardVanilla bundles;
so a pre-NU7 v5 Orchard transaction whose `flagsOrchard` byte has bit 2 set deserializes
successfully (and validates, the vanilla circuit leaving ENABLE_ZSA unconstrained) rather
than being rejected under `bad-txns-v5-reserved-bits-nonzero` — an accept-vs-reject split
against deployed zcashd/zebra consensus

**Body:**

SIDE A (fork). orchard-zsa `cf801a5` `src/bundle.rs:88-89`: `const FLAG_ZSA_ENABLED: u8 =
0b0000_0100;` and `const FLAGS_EXPECTED_UNSET: u8 = !(FLAG_SPENDS_ENABLED |
FLAG_OUTPUTS_ENABLED | FLAG_ZSA_ENABLED);` — bit 2 is NOT in the reserved mask.
`from_byte(value: u8) -> Option<Self>` (`:190-201`) takes **no** format parameter and
returns `Some` whenever `value & FLAGS_EXPECTED_UNSET == 0`, so bit 2 (`0x04`) is always
accepted; `Flags` (`:61`) is a plain non-generic struct with no flavor gate; `to_byte`
(`:178`) round-trips `zsa_enabled` back to `0x04`. librustzcash-zsa `3f9b53f`
`zcash_primitives/src/transaction/components/orchard.rs:262-266`: `read_flags` calls
`Flags::from_byte(byte[0])`; `read_v5_bundle` (`orchard.rs:65-99`) is **not** behind any
`#[cfg(zcash_unstable="nu7")]` gate and returns `orchard::Bundle<Authorized, ZatBalance,
OrchardVanilla>`; `transaction/mod.rs:1037` wires `read_v5` → `OrchardBundle::OrchardVanilla`.
So a v5 tx with `flagsOrchard = 0x04` flows through the un-gated path.

SIDE B (deployed + upstream). Deployed orchard `0.10.0` (what zcashd/zebra run)
`src/bundle.rs:63,131-133`: `FLAGS_EXPECTED_UNSET = !(FLAG_SPENDS_ENABLED |
FLAG_OUTPUTS_ENABLED)` and `from_byte` returns `None` unless `value & FLAGS_EXPECTED_UNSET
== 0`, anchored `// https://p.z.cash/TCR:bad-txns-v5-reserved-bits-nonzero` — bit 2
rejected. Upstream Ironwood orchard `bef8a27` fixed exactly this by adding `enum
BundleFormat` (`src/bundle.rs:89`): `PRE_NU6_3_FLAGS_EXPECTED_UNSET = !(FLAG_SPENDS_ENABLED
| FLAG_OUTPUTS_ENABLED)` (bit 2 reserved) and `from_byte(value, format)`
(`:122-123,265-289`) selecting `PreNu6_3 =>` (rejects bit 2) vs `Nu6_3 =>
NU6_3_FLAGS_EXPECTED_UNSET` (bit 2 = `enableCrossAddress`). The fork reuses bit 2 for
`enableZSAs` — colliding, incidentally, with upstream Ironwood's reuse of the same bit for
`enableCrossAddress` — but applies the new semantics to the *legacy v5 format too*; the
missing `BundleFormat`/flavor gate is the root cause.

No neutralizing guard downstream. `src/circuit/circuit_vanilla.rs` has zero references to
`ENABLE_ZSA` (grep count 0): it binds only ANCHOR/ENABLE_SPEND/ENABLE_OUTPUT via
`assign_advice_from_instance` (`:579-601`) and CV_NET/NF_OLD/RK/CMX via `constrain_instance`.
Instance index 9 (ENABLE_ZSA, set from `flags.zsa_enabled()` at `circuit.rs:492,560`) is
left completely unconstrained — the code's own comment (`circuit.rs:438-441,537-540`) says
enable_zsa is padded/ignored in vanilla. So an attacker can produce a valid vanilla proof
with `enable_zsa=1`. No consensus check rejecting `zsa_enabled` on v5/OrchardVanilla
exists anywhere in librustzcash-zsa (grep found none). Not covered by dossier #4-8 or by
the ZSA Guide (which describes bit 2 = enableZSAs only for the v6 format, "remaining bits
zero").

**Failure mode.** A v5 Orchard transaction with `flagsOrchard = 0x04` (or `0x05`/`0x06`/
`0x07` — bit 2 set) is deserialized successfully by librustzcash-zsa as an OrchardVanilla
bundle carrying `zsa_enabled=true` (the reserved bit silently consumed, round-tripping
through `to_byte`) and — because the vanilla circuit leaves ENABLE_ZSA unconstrained —
fully validated, whereas deployed Zcash consensus (zcashd/zebra, orchard 0.10.0) and
upstream Ironwood's PreNu6_3 format reject the identical wire bytes at parse under
`bad-txns-v5-reserved-bits-nonzero`. A QED-it-fork node accepts a block the rest of the
network rejects: a chain split on identical bytes.

Observed at orchard-zsa (QED-it) `cf801a5` (`src/bundle.rs:61,88-89,178,190-201`;
`src/circuit.rs:438-441,492,537-540,560`; `src/circuit/circuit_vanilla.rs:579-601`);
librustzcash-zsa (QED-it) `3f9b53f`
(`zcash_primitives/src/transaction/components/orchard.rs:65-99,262-266`;
`transaction/mod.rs:1037`); deployed orchard `0.10.0` (`src/bundle.rs:63,131-133`);
upstream Ironwood orchard `bef8a27` (`src/bundle.rs:89,122-123,265-289`).

---

## 44. zaino — `PoolTypeFilter::new_from_slice` / `new_from_pool_types` doc-comment says the vector is rejected past 3 elements, but the code bounds it at 4 (stale, pre-Ironwood)

**DRAFT. Severity: low.**

**Title:** Both `PoolTypeFilter` constructor doc-comments state the vector errors when it
"contains more than 3 elements", but the code rejects only `len > PoolType::Ironwood as
usize == 4`; the wording is stale from before the Ironwood pool was added to `PoolType`
(Invalid=0 … Ironwood=4), and the crate's own tests assert the 4-element vector is
accepted

**Body:**

zaino `0e057e22`. Doc (`zaino-proto/src/proto/utils.rs:187-188` and again `:197-198`, on
both `new_from_slice` and `new_from_pool_types`): "If the vector contains
`PoolType::Invalid` or the vector contains more than 3 elements returns
`PoolTypeError::InvalidPoolType`". Code (`utils.rs:202`): `if pool_types.len() >
PoolType::Ironwood as usize { return Err(PoolTypeError::InvalidPoolType); }`; the enum
(`service.rs:323-329`) is `Invalid=0, Transparent=1, Sapling=2, Orchard=3, Ironwood=4`, so
`PoolType::Ironwood as usize == 4` and the guard rejects only `len > 4`. Upstream's own
tests prove the drift: `test_pool_type_filter_t_z_o` (`utils.rs:452-466`) asserts
`new_from_pool_types(&[Transparent, Sapling, Orchard, Ironwood])` — the 4-element vector
— returns `Ok(from_checked_parts(true,true,true,true))` (ACCEPTED), while
`test_pool_type_filter_fails_when_too_many_items` (`utils.rs:436-450`) needs a 5-element
vector to produce the error. Tested contract is "up to 4 OK, 5+ rejected", contradicting
the documented "more than 3 → error".

**Failure mode.** No runtime bug — the length ceiling correctly tracks the Ironwood
discriminant. Documentation drift only: a caller relying on the ">3 rejected" contract
would wrongly expect a 4-pool request (e.g. `[Transparent, Sapling, Orchard, Ironwood]`)
to error when it is accepted. Fix: change both doc-comments to "more than 4 elements".

Observed at zaino `0e057e22` (`zaino-proto/src/proto/utils.rs:187-188,197-198,202,
436-450,452-466`; `zaino-proto/src/proto/service.rs:323-329`).

---

# Wave-4 model-diff findings (DRAFT — needs owner confirmation before filing)

**DRAFT.** These 13 entries come from the Wave-4 **bounded zaino-backend final
probe** (2026-07-16) — the agreed last probe of the audit, tightly scoped to the
`zaino-state` gRPC service backends (`StateService` vs `FetchService`) and their
shared helpers, model-diffed against lightwalletd. Firsthand-cited, not yet
owner-reviewed; do not file upstream until confirmed. Numbering continues the dossier
(45-57). Ground-truth pins: zaino `0e057e22`, lightwalletd `61fee32`, zebra-rpc
`11.0.0` (zebra local `9f3166b96`).

Raw yield was 15 findings, folded to 13 by dropping two exact duplicates — the
`get_transaction` mempool-height divergence was reported twice (→ **48**) and the
`get_block` unknown-hash status-code divergence twice (→ **49**). Of the 13, **12 are
genuine zaino behavioural roots** (4 medium, 8 low) and **one (57) is a latent
lightwalletd-only bug with NO zaino defect** — recorded here because the dossier
tracks upstream defects regardless of target. Folding the two shared-cause pairs (the
unspecified-`BlockId`→`Height(0)` manifestation across `get_block` (50) and
`get_tree_state` (51); the two `get_taddress_txids_helper` range-rewrite bugs (46, 53))
leaves ~10 independent root causes.

**Dedup vs #1-44 + G1-G9.** Distinct from **#40** (that is `get_block_nullifiers`
ignoring a *set* hash and reading only height; here 45 is a different method,
`get_block_range`, and 49/50 concern the *unspecified/absent* identifier and the
unknown-hash *error mapping* — 49 explicitly notes `get_block` DOES resolve a set hash
on both backends, so it is not the #40 omission). Distinct from **#44** (that is a
doc-comment drift on `PoolTypeFilter`'s length bound; 47 is a *behavioural* omission —
FetchService `get_mempool_tx` never reads `pool_types` at all). Distinct from **#3**
(Zaino's `lightwalletProtocolVersion` constant) and **G9** (the `protoVersion`
dead-code literal). All 13 are new roots.

**Severity ceiling: MEDIUM (no HIGH).** The STOP verdict and the audit-converged
declaration live in `correctness-audit.md` §Wave 4.

---

## 45. zaino — StateService `get_block_range` silently returns an empty OK stream before the non-finalized cache loads, where FetchService errors and its own `get_block`/`get_latest_block` return `UnavailableNotSyncedEnough`

**DRAFT. Severity: medium.**

**Title:** During initial sync, StateService `get_block_range` (shared
`get_block_range_inner`, also `get_block_range_nullifiers`) returns a gRPC-OK stream
with zero `CompactBlock`s instead of an error, while FetchService's `get_block_range`
returns `FailedPrecondition` and StateService's own `get_block`/`get_latest_block`
return `UnavailableNotSyncedEnough` on the identical not-synced condition — the
silent-empty is the outlier and reads to a wallet as "range legitimately has no blocks"

**Body:**

Function `get_block_range_inner` on StateService
(`packages/zaino-state/src/backends/state.rs:581-582`) carries `// This method does not
support passthrough. Just return.` then `let Some(non_finalized_snapshot) =
snapshot.get_nfs_snapshot() else { return };` — a bare `return`, **no**
`channel_tx.send(Err(..))`. The outer method returns
`Ok(CompactBlockStream::new(channel_rx))` (`state.rs:682`); dropping `channel_tx`
closes `channel_rx` cleanly, so the client sees a gRPC-OK stream with zero blocks. Both
`get_block_range` (`state.rs:2061-2066`) and `get_block_range_nullifiers`
(`state.rs:2068-2073`) route through this helper. The reachable window: `get_nfs_snapshot()`
returns `None` for `ChainIndexSnapshot::StillSyncingFinalizedState`
(`non_finalised_state.rs:89-96`), which `snapshot_nonfinalized_state()` returns while
`non_finalized_state.load()` is `None` (`chain_index.rs:1475-1495`). The serve layer is
a passthrough — `zaino-serve/src/rpc/grpc/service.rs` `client_method_helper` just
`Box::pin`s the subscriber's stream into `tonic::Response`, no guard.

Contrast, same condition: FetchService's identical branch does
`channel_tx.send(Err(tonic::Status::failed_precondition("zaino not yet synced")))`
(`fetch.rs:1137-1150` range, `1270-1283` nullifiers), with a comment noting it "is an
improvement over previous behaviour of acting as if we are only synced to the genesis
block." StateService's own siblings error too: `get_block` (`state.rs:1985-1989`) and
`get_latest_block` (`state.rs:1944-1948`) both return `UnavailableNotSyncedEnough`.
lightwalletd (`common/common.go:580-624`) streams blocks or pushes an error onto
`errOut` on any missing block, surfaced at `frontend/service.go:241-256` — never a
silent empty OK for an in-range request. StateService is production-selectable
(`config.rs:50-54`; `indexer.rs:64-78`).

**Failure mode.** A light wallet issues `GetBlockRange` over a valid `[start,end]`
against a StateService-backed zaino during the pre-cache-load window and receives gRPC
OK with zero blocks. A wallet that treats "range returned, no blocks" as "range
scanned, nothing relevant" advances its scanned-height watermark and silently skips
those blocks — missed transactions. A FetchService-backed zaino would error and the
wallet would retry: behaviour is deployment-backend-dependent for the identical request.

Observed at zaino `0e057e22` (`packages/zaino-state/src/backends/state.rs:581-582,682,
1944-1948,1985-1989,2061-2073`; `packages/zaino-state/src/backends/fetch.rs:1137-1150,
1270-1283`; `chain_index.rs:1475-1495`; `non_finalised_state.rs:89-96`); lightwalletd
`61fee32` (`common/common.go:580-624`; `frontend/service.go:241-256`).

---

## 46. zaino — shared `get_taddress_txids_helper` clamps both range bounds down to the chain tip and swaps a backwards range, so an out-of-range or reversed taddr query returns a wrong over-inclusive set instead of the empty/error the reference produces

**DRAFT. Severity: medium.**

**Title:** Helper `get_taddress_txids_helper` (used by BOTH backends) rewrites the
caller's block range before querying — clamping start and end down to the tip and
swapping them when `start > end` — so `getaddresstxids` runs on a different range than
lightwalletd would issue for the same input, returning transactions the client never
asked for

**Body:**

Helper `get_taddress_txids_helper` (`packages/zaino-state/src/indexer.rs:593-649`, a
single definition, no per-backend override) reads `let chain_height =
self.chain_height().await?` (`:598`), then clamps `start` (`:603`) and `end` (`:615`)
with `Ok(height) => Some(height.min(chain_height.0))`, and swaps a backwards range
(`:627-628` `if start > end { (Some(end), Some(start)) }`), before
`get_address_tx_ids(GetAddressTxIdsRequest::new(vec![request.address], start, end))`
(`:642-647`). StateService reaches it via `state.rs:2118 → 1885 →
validator_connector.rs:983-1052`, whose own guards (`:999` `start > end`, `:1004`
bounds vs tip) then PASS because the values are already normalized, and the query runs
on the rewritten `Height(start)..=Height(end)` (`:1014-1025`). FetchService reaches it
via `fetch.rs:1445 → 858 → validator_connector.rs:1054 → connector.rs:875-887`, sending
the rewritten `{addresses,start,end}` verbatim to the node's `getaddresstxids`.

lightwalletd forwards the caller range unchanged: `frontend/service.go:109-115` sets
`Start` verbatim and `End` only `if addressBlockFilter.Range.End != nil` — no clamp, no
swap — then hands it to `getaddresstxids` (`:124`). Serve dispatch does no range
validation (`service.rs:179-181`; macro `:43-53`). Both backends are
production-selectable (`zainod/src/config.rs:26`).

**Failure mode.** Tip=150, client requests taddr txids for `[start=180,end=200]`: zaino
clamps to `[150,150]` and returns block-150 transactions the client never asked for;
zcashd returns empty, zebrad errors. Tip=1000, backwards range `[500,300]`: zaino swaps
to `[300,500]` and returns that whole range; zcashd returns empty, zebrad errors. Same
class as #40 (wrong block set for a taddr/height query); affects both backends.

Observed at zaino `0e057e22` (`packages/zaino-state/src/indexer.rs:593-649`;
`backends/state.rs:1885,2118`; `backends/fetch.rs:858,1445`;
`validator_connector.rs:983-1052,1054`; `zaino-fetch/src/jsonrpsee/connector.rs:875-887`;
`zaino-serve/src/rpc/grpc/service.rs:43-53,179-181`); lightwalletd `61fee32`
(`frontend/service.go:109-124`).

---

## 47. zaino — FetchService `get_mempool_tx` ignores `request.pool_types` entirely (hardwired `to_compact(0)` = default filter), so the requested-pool filter is silently dropped on the DEFAULT backend where StateService and lightwalletd honour it

**DRAFT. Severity: medium.**

**Title:** FetchService `get_mempool_tx` never reads `request.pool_types`; its only
conversion is `to_compact(0)`, hardwired to `PoolTypeFilter::default()`
(Sapling+Orchard+Ironwood, transparent excluded), so a caller asking for a specific
pool gets the default set and an invalid pool code is served instead of rejected —
whereas StateService validates and applies the filter, and lightwalletd rejects
`PoolType_INVALID` and applies `FilterTxPool`

**Body:**

Method `get_mempool_tx` on FetchService
(`packages/zaino-state/src/backends/fetch.rs:1630-1748`) never references
`request.pool_types`; the only request field read is `request.exclude_txid_suffixes`
(`:1636`). Its single conversion is `transaction.1.to_compact(0)` (`:1691`), and
`to_compact(self, index)` is defined `self.to_compact_tx(Some(index),
&PoolTypeFilter::default())` (`zaino-fetch/src/chain/transaction.rs:270`).
`PoolTypeFilter::default()` = `{transparent:false, sapling:true, orchard:true,
ironwood:true}` (`zaino-proto/src/proto/utils.rs:162-171`); `to_compact_tx` gates each
pool on `includes_*()` (`transaction.rs:282-364`), so it emits sapling+orchard+ironwood
and drops transparent regardless of the request.

StateService instead validates via `PoolTypeFilter::new_from_slice(&request.pool_types)`
(`state.rs:2324`, `InvalidArgument` on invalid/unknown pools, empty→default —
`utils.rs:189-227`) and applies `to_compact_tx(None, &pool_types)` (`state.rs:2381`).
lightwalletd `GetMempoolTx` (`frontend/service.go:600-708`) rejects
`PoolType_POOL_TYPE_INVALID` (`:607-609`), maps empty→`[SAPLING,ORCHARD]` (`:610-616`),
and applies `common.FilterTxPool` per tx (`:700`; `common/common.go:526-551`). Serve
dispatch is a passthrough (`service.rs:197`, `:93-133`); FetchService's
`get_mempool_transactions(exclude_txids)` (`fetch.rs:1662`) reintroduces no filter.
FetchService is the **DEFAULT** backend (`#[default] Fetch`, `config.rs:58-59`; zainod
`.set_default("backend","fetch")`, `zainod/src/config.rs:315`; dispatch
`zainod/src/indexer.rs:72-77`), so the divergence is live. Distinct from #44, which is a
doc-comment drift on `PoolTypeFilter`'s length bound — this is a behavioural omission.

**Failure mode.** A wallet asks FetchService-backed zaino for transparent-only mempool
data (`pool_types=[Transparent]`) and receives the default filter (Sapling+Orchard+
Ironwood, transparent excluded): zero transparent data requested, shielded data not
requested. `pool_types=[Orchard]` over-discloses Sapling/Ironwood. `pool_types=[Invalid(0)]`
returns OK with default data instead of the `InvalidArgument` StateService and
lightwalletd both raise. StateService serves the identical request correctly.

Observed at zaino `0e057e22` (`packages/zaino-state/src/backends/fetch.rs:1630-1748,1691,
1662`; `state.rs:2302-2429,2324,2381`; `zaino-fetch/src/chain/transaction.rs:270,282-364`;
`zaino-proto/src/proto/utils.rs:162-171,189-227`;
`zaino-serve/src/rpc/grpc/service.rs:93-133,197`; `config.rs:58-59`;
`zainod/src/config.rs:315`; `zainod/src/indexer.rs:72-77`); lightwalletd `61fee32`
(`frontend/service.go:600-708`; `common/common.go:526-551`).

---

## 48. zaino — for a mempool transaction, StateService `get_transaction` returns `RawTransaction.height = 0` while FetchService returns the chain-tip height, for identical wire input (StateService matches lightwalletd; FetchService diverges)

**DRAFT. Severity: medium.**

**Title:** `get_transaction` maps Zebra's `height = None` (mempool) differently per
backend — StateService `unwrap_or(0)` → 0, FetchService substitutes the best-tip height
— so the same unconfirmed tx reports height 0 (unconfirmed) via StateService and
lightwalletd, but ~tip (looks mined, confirmations = 1) via FetchService

**Body:**

FetchService `get_transaction` (`packages/zaino-state/src/backends/fetch.rs:1402-1414`):
`None => { let snapshot = self.indexer.snapshot_nonfinalized_state().await?; … 
non_finalized_snapshot.best_tip.height.0 as u64 }` (comment "Zebra returns None for
mempool transactions, convert to `Mempool Height`") — returns the chain-tip height.
StateService `get_transaction` (`state.rs:2094-2097`): `height:
transaction_object.height().unwrap_or(0) as u64` — returns 0. Both backends bake
`height = None` for mempool identically (`state.rs:1841`, `fetch.rs:789`:
`Some(BestChainLocation::Mempool(_)) => (None, Some(0), None, Some(false))`). Zebra
origin: `zebra-rpc/src/methods/types/transaction.rs:283-287` `pub(crate) height:
Option<i32>` "`None` if the tx is in the mempool".

lightwalletd matches StateService (0), NOT FetchService: `common/common.go`
`ParseRawTransaction` sets `Height: uint64(txinfo.Height)`, and its doc DEFINES "height
0: the transaction is in the mempool"; `common/mempool.go:143-147` `if rawtx.Height != 0
{ continue }` proves mempool txs carry `Height == 0`. Zaino's own proto contract agrees:
`packages/zaino-proto/proto/service.proto:74` "height 0: the transaction is in the
mempool". Both backends production-selectable (`service.rs:175`; `zainod/src/config.rs`
`backend` field, default "fetch", State selectable). One raw sub-finding wrongly cited
zaino's internal streaming convention (`indexer.rs:959-962` `None => chain_height`, used
by `get_taddress_transactions`) as the "lightwalletd reference"; corrected here —
lightwalletd returns 0, that internal convention is itself a zaino deviation.

**Failure mode.** A wallet queries `GetTransaction` for a just-broadcast, still-in-mempool
tx. Via FetchService it gets `height = tip`, so `confirmations = tip - height + 1 = 1`
and the tx appears mined/confirmed while unconfirmed; via StateService (and lightwalletd)
it gets `height = 0`. Same tx, contradictory confirmation status by backend. The
inter-backend inconsistency is CONFIRMED; the wallet impact is PLAUSIBLE (depends on how
the client reads height).

Observed at zaino `0e057e22` (`packages/zaino-state/src/backends/fetch.rs:1402-1414,789`;
`backends/state.rs:2094-2097,1841`; `packages/zaino-proto/proto/service.proto:74`); zebra
`zebra-rpc/src/methods/types/transaction.rs:283-287`; lightwalletd `61fee32`
(`common/common.go` `ParseRawTransaction`; `common/mempool.go:143-147`).

---

## 49. zaino — for a well-formed but non-existent block hash, StateService `get_block` returns gRPC `NOT_FOUND` while FetchService returns `INVALID_ARGUMENT` (FetchService's message also carries a `founf` typo); pure error-mapping divergence, not the #40 omission

**DRAFT. Severity: low.**

**Title:** `get_block` resolves a set 32-byte hash on BOTH backends (so this is not
#40), but the hash-not-found arm maps to different gRPC status codes — StateService
`NOT_FOUND` (5), FetchService `INVALID_ARGUMENT` (3) — plus a `Hash not founf in chain`
typo in the FetchService message; a client that branches on status code behaves
per-backend for the identical unknown-hash request

**Body:**

Helper `blockid_to_hashorheight` (`zaino-proto/src/proto/utils.rs:312-323`) tries
`<[u8;32]>::try_from(block_id.hash)` FIRST, so a well-formed 32-byte hash yields
`HashOrHeight::Hash` on both backends — `get_block` does resolve it, this is NOT the #40
hash-ignored omission. The divergence is purely the not-found mapping. StateService
(`state.rs:1966-1975`): `… .ok_or_else(|| StateServiceError::TonicStatusError(
tonic::Status::not_found("Error: Block not found for given hash.")))?` → NOT_FOUND (5).
FetchService (`fetch.rs:939-952`): `Ok(None) => return
Err(FetchServiceError::TonicStatusError(tonic::Status::invalid_argument("Error: Invalid
hash and/or height out of range. Hash not founf in chain")))` → INVALID_ARGUMENT (3),
with the `founf` typo. Both statuses pass to the wire unchanged (`error.rs:144,235`;
`service.rs:62,161`).

lightwalletd rejects any by-hash `GetBlock` with `codes.InvalidArgument` "GetBlock:
Block hash specifier is not yet implemented" (`frontend/service.go:176-181`) — so
FetchService's code matches lightwalletd and StateService is the outlier. Both backends
production-reachable (`zainod/src/indexer.rs:65-77`; default "fetch", State selectable).

**Failure mode.** A client requesting a block by a well-formed but unknown/non-canonical
32-byte hash, branching on status (e.g. retry on NOT_FOUND, hard-fail on
INVALID_ARGUMENT), behaves differently solely by deployed backend. Secondary: the
user-facing `founf` typo (cosmetic).

Observed at zaino `0e057e22` (`packages/zaino-state/src/backends/state.rs:1966-1975`;
`backends/fetch.rs:939-952`; `zaino-proto/src/proto/utils.rs:312-323`;
`packages/zaino-state/src/error.rs:144,235`; `zaino-serve/src/rpc/grpc/service.rs:62,161`;
`zainod/src/indexer.rs:65-77`); lightwalletd `61fee32` (`frontend/service.go:176-181`).

---

## 50. zaino — `get_block` on a default/empty `BlockId` (height 0, no hash) returns the genesis CompactBlock on both backends, where lightwalletd rejects it with `InvalidArgument "request for unspecified identifier"`

**DRAFT. Severity: low.**

**Title:** Neither backend has an unspecified-identifier guard;
`blockid_to_hashorheight(BlockId{height:0, hash:[]})` yields `HashOrHeight::Height(0)`
(never `None`), so an accidental default/uninitialised `BlockId` is served the genesis
block with gRPC OK instead of the `InvalidArgument` lightwalletd returns

**Body:**

Helper `blockid_to_hashorheight` (`zaino-proto/src/proto/utils.rs:312-323`) with fields
`height: u64` / `hash: Vec<u8>` (`service.rs:33,35`): for a default `BlockId{height:0,
hash:vec![]}`, `<[u8;32]>::try_from(empty Vec)` fails (len 0 ≠ 32), `.or_else` runs
`0u64.try_into::<u32> = Ok(0)` → returns `Some(HashOrHeight::Height(Height(0)))`, never
`None`. So the `.ok_or(InvalidArgument)?` guard in both backends fires only for
`height > u32::MAX`, never for the unspecified case. StateService `get_block`
(`state.rs:1954-1980`) → `Height(0)` → `get_compact_block(.., Height(0),
includes_all())` → `Ok(Some(block)) => Ok(block)` = genesis with gRPC OK. FetchService
`get_block` (`fetch.rs:929-972`) → same fall-through → genesis with gRPC OK. Serve
dispatch forwards the raw `BlockId` unvalidated (`service.rs:166-167`, macro `:29-39`).

lightwalletd rejects it: `frontend/service.go:170-173` `if id.Height == 0 && id.Hash ==
nil { return nil, status.Error(codes.InvalidArgument, "GetBlock: request for unspecified
identifier") }`. Shares its root cause (helper collapses unspecified→`Height(0)`; no
serve-layer guard) with #51 (`get_tree_state`), different method.

**Failure mode.** A client that accidentally sends an uninitialised/default `BlockId`
receives the genesis block with gRPC OK from zaino (both backends) instead of the
`InvalidArgument` error lightwalletd returns; a client relying on the server to reject
unspecified requests silently proceeds with genesis data.

Observed at zaino `0e057e22` (`zaino-proto/src/proto/utils.rs:312-323`;
`zaino-proto/src/proto/service.rs:33,35`;
`packages/zaino-state/src/backends/state.rs:1954-1980`; `backends/fetch.rs:929-972`;
`zaino-serve/src/rpc/grpc/service.rs:29-39,166-167`); lightwalletd `61fee32`
(`frontend/service.go:170-173`).

---

## 51. zaino — `get_tree_state` on a default/unspecified `BlockId` returns the genesis (empty) treestate with gRPC OK on both backends, where lightwalletd returns `InvalidArgument`

**DRAFT. Severity: low.**

**Title:** Same unspecified-`BlockId`→`Height(0)` collapse as #50, in `get_tree_state`:
a default `BlockId{}` (or `{height:0}`) never hits the `invalid_argument("Invalid hash
or height")` guard, so the RPC returns `TreeState{height:0, hash:<genesis>,
sapling_tree:"", orchard_tree:""}` with status OK instead of rejecting the malformed
request; `get_tree_state` does correctly honour a *provided* hash

**Body:**

Helper `blockid_to_hashorheight` (`zaino-proto/src/proto/utils.rs:312-323`) maps
`BlockId{height:0, hash:vec![]}` to `Some(Height(0))` (never `None`; see #50).
StateService `get_tree_state` (`state.rs:2516-2521`) and FetchService `get_tree_state`
(`fetch.rs:1836-1841`) therefore never reach their `.ok_or(tonic::Status::
invalid_argument("Invalid hash or height"))` guard for a default `BlockId`. Both call
`z_get_treestate("0")` (`state.rs:1487-1495` / `fetch.rs:595-605`):
`get_indexed_block_by_height(Height(0))` returns genesis, `get_treestate(genesis_hash)`
returns `(None,None,None)` for pre-Sapling genesis, and the sapling/orchard trees pass
through `.unwrap_or_default()` (`state.rs:2535,2543`; `fetch.rs:1855,1863`) to `""`. The
result is `TreeState{height:0, hash:<genesis>, sapling_tree:"", orchard_tree:""}` with
gRPC OK. Serve dispatch does no `BlockId` pre-validation (`service.rs:29-40,93-120`).

lightwalletd rejects it: `frontend/service.go:311-315` `if id.Height == 0 && id.Hash ==
nil { return nil, status.Error(codes.InvalidArgument, "GetTreeState: must specify a
block height or ID (hash)") }`. Same root as #50, sibling of #40's genesis behaviour but
distinct method and distinct trigger (default height, not an ignored hash).

**Failure mode.** A client sending a default/unset `BlockId` silently receives the empty
genesis note-commitment frontier with status OK and may treat the tree as legitimately
empty rather than surfacing the malformed request.

Observed at zaino `0e057e22` (`zaino-proto/src/proto/utils.rs:312-323`;
`packages/zaino-state/src/backends/state.rs:1487-1495,2516-2521,2535,2543`;
`backends/fetch.rs:595-605,1836-1841,1855,1863`;
`zaino-serve/src/rpc/grpc/service.rs:29-40,93-120`); lightwalletd `61fee32`
(`frontend/service.go:311-315`).

---

## 52. zaino — `get_tree_state` for a block at or before Sapling activation returns a `TreeState` with an empty sapling tree and status OK, where lightwalletd walks the `z_gettreestate` SkipHash chain and returns `InvalidArgument`

**DRAFT. Severity: low.**

**Title:** For a pre-Sapling-activation height both backends return
`TreeState{sapling_tree:""}` (StateService) / hex-of-empty-tree (FetchService) with
status OK, while lightwalletd, finding no non-empty `FinalState` up the SkipHash chain,
returns `InvalidArgument`; benign in practice (wallets query at post-Sapling birthdays)
but a real OK-vs-error contract split, identical on both backends

**Body:**

StateService: `validator_connector.rs:398-419` sets `sapling = None` for `height <
Sapling activation` (not substituted with an empty tree, unlike ironwood at `:481-489`);
`z_get_treestate` builds `Commitments::new(None, sapling)` with `final_state = None`
(`state.rs:1510-1517`); `get_tree_state` then `sapling_tree =
hex::encode(..final_state().clone().unwrap_or_default()) = ""` (`state.rs:2529-2536`),
returning `Ok(TreeState{sapling_tree:"", ..})`. FetchService: identical
`unwrap_or_default` handling (`fetch.rs:1849-1856`); its `validator_connector.rs:493-512`
Fetch variant maps absent sapling to `Some(serialized empty tree)` — returns `Ok` either
way. Serve macro passes `Ok(TreeState)` straight through (`service.rs:93-133,202`), no
emptiness/activation-height post-check.

lightwalletd: `service.go:359-364` loop breaks when `Sapling.Commitments.FinalState !=
""` OR `Sapling.SkipHash == ""`; terminal `service.go:372-374` `if
…FinalState == "" { return status.Error(codes.InvalidArgument, "GetTreeState:
z_gettreestate did not return treestate") }`. Its comment (`:341-345`) notes zcashd
hard-stops the SkipHash walk at Sapling activation, so a pre-Sapling request yields empty
FinalState + empty SkipHash → the terminal error fires.

**Failure mode.** `GetTreeState(height=100)` on mainnet (100 ≪ Sapling activation
419200): StateService returns `Ok(TreeState{sapling_tree:""})`, FetchService returns
`Ok(TreeState{sapling_tree:<hex empty tree>})`, lightwalletd returns `InvalidArgument`.
A client treating OK+empty as "valid empty frontier" diverges from the lightwalletd
error contract. (StateService's primary path succeeds via finalized_state for a finalized
block 100, `chain_index.rs:1373-1408,1613-1625`; the fallback rpc path is never reached.)

Observed at zaino `0e057e22` (`packages/zaino-state/src/validator_connector.rs:398-419,
481-489,493-512`; `backends/state.rs:1510-1517,2529-2536`; `backends/fetch.rs:1849-1856`;
`chain_index.rs:1373-1408,1613-1625`; `zaino-serve/src/rpc/grpc/service.rs:93-133,202`);
lightwalletd `61fee32` (`frontend/service.go:341-374`).

---

## 53. zaino — a start-only taddr-txids request (`Range.Start` set, `Range.End` omitted) errors on StateService with `InvalidArgument "start N must be less than or equal to end 0"`, where lightwalletd forwards it and returns the address's transactions

**DRAFT. Severity: low.**

**Title:** When the caller supplies a start but omits end, `get_taddress_txids_helper`
leaves `end = None` (should mean "up to tip", the way `start` is clamped via
`.min(chain_height)`), and `GetAddressTxIdsRequest::into_parts` collapses `None` to `0`;
StateService then rejects `start > 0 = end` as `InvalidArgument`, while lightwalletd
drops the empty `End` via `omitempty` and (on zcashd) returns all of the address's
transactions

**Body:**

Helper `get_taddress_txids_helper` (`packages/zaino-state/src/indexer.rs:613-624`): when
`range.end` is `None`, `end = None`; the `match (start, end)` at `:625-634` hits `_ =>
(start, end)`, so `(Some(100), None)` stays `(Some(100), None)`. `into_parts`
(`zebra-rpc 11.0.0 methods.rs:4381-4386`) returns `(addresses, self.start.unwrap_or(0),
self.end.unwrap_or(0))` → `end = None` collapses to `0`. StateService
`validator_connector.rs:999-1003` `if start > end { error_string = Some(format!("start
{start:?} must be less than or equal to end {end:?}")) }` fires (100 > 0), returning
`Err(...Unrecoverable)` → gRPC `InvalidArgument`. Full path: `service.rs:181 → state.rs:2161
→ 2165 → 2118 → 1881 → get_address_txids → validator_connector.rs:978`, no end-required
guard anywhere.

lightwalletd (`frontend/service.go:105-115`) errors only if `Range.Start` is nil, sets
`End` only when non-nil, and `common/common.go:110-115` marshals `End uint64
json:"end,omitempty"` — so a start-only request marshals to
`{"addresses":[...],"start":100}` and zcashd returns data (no upper bound). Node-dependent
(zebrad also errors on `start > end`). FetchService instead forwards `{start:100,end:0}`
explicitly (`connector.rs:875-887`). Root: the helper leaves `end = None` where it should
mean up-to-tip; `into_parts` turns `None` into "block 0", inverting the range for any
`start > 0`. Shares the `get_taddress_txids_helper` root with #46. Guide-scope:
`sync-guide.tex:1321-1334` lists these RPCs as out-of-scope — not guide-wrong.

**Failure mode.** A protocol-legal `GetTaddressTxids` with `Range.Start = 100`,
`Range.End = nil` returns a guaranteed gRPC `InvalidArgument` on StateService before
reading any chain data, whereas lightwalletd (on zcashd) returns the address's
transactions.

Observed at zaino `0e057e22` (`packages/zaino-state/src/indexer.rs:613-634,642`;
`backends/state.rs:1881,2118,2161,2165`; `validator_connector.rs:978,986,999-1012`;
`zaino-fetch/src/jsonrpsee/connector.rs:875-887`); zebra-rpc `11.0.0`
(`methods.rs:4354-4386`); lightwalletd `61fee32` (`frontend/service.go:105-115`;
`common/common.go:110-115`).

---

## 54. zaino — `get_taddress_balance_stream` sums a per-address balance query per streamed address with no dedup, so a duplicate address in the stream is counted once per occurrence — double-counting where the non-stream path and lightwalletd dedup

**DRAFT. Severity: low.**

**Title:** The streaming balance endpoint issues one single-address `getaddressbalance`
per streamed address and accumulates `total_balance += balance.balance()`, so streaming
the same taddr twice returns 2× its balance; the non-stream `get_taddress_balance`
passes the whole vec to one call which dedups via a `HashSet`, and lightwalletd collects
all addresses into a single call — so zaino breaks its own stream-vs-non-stream invariant

**Body:**

StateService `get_taddress_balance_stream` (`state.rs:2203-2210`): `let mut
total_balance: u64 = 0; loop { … Some(taddr) => { let taddrs =
GetAddressBalanceRequest::new(vec![taddr]); let balance =
…z_get_address_balance(taddrs).await?; total_balance += balance.balance(); } … }` — one
single-address query per streamed address, summed, no cross-stream dedup. FetchService
`fetch.rs:1527-1534` is byte-identical. Serve forwards the raw `Streaming<Address>`
verbatim (`service.rs:277-291`). The non-stream `get_taddress_balance`
(`state.rs:2169-2174` / `fetch.rs:1497-1499`) passes the WHOLE vec to one call, which
dedups: `valid_addresses()` collects into a `HashSet<Address>` (zebra
`methods.rs:3597-3611`; zaino `validator_connector.rs:940`
`ReadRequest::AddressBalance(strings_set)`). So `[A,A]` in one call → `{A}` → counted
once, but `[A]` then `[A]` as two calls → `A + A = 2A`.

lightwalletd `GetTaddressBalanceStream` (`service.go:561-576`) appends every
`addr.Address` (dups included) into one `addressList`, then a single
`getTaddressBalanceZcashdRpc(addressList)` — the same call its non-stream
`GetTaddressBalance` makes (`:549-556`), so stream == non-stream regardless of node.

**Failure mode.** Streaming taddr A twice → zaino returns 2A (both backends);
lightwalletd-on-zebrad returns A (zebrad HashSet-dedups the single call). Zaino also
breaks its own stream-vs-non-stream invariant that lightwalletd preserves. Reference is
node-dependent (zcashd `getaddressbalance` also double-counts) and duplicate-address
streams are unusual — low severity/confidence.

Observed at zaino `0e057e22` (`packages/zaino-state/src/backends/state.rs:2169-2174,
2203-2210`; `backends/fetch.rs:1497-1499,1527-1534`; `validator_connector.rs:940`;
`zaino-serve/src/rpc/grpc/service.rs:277-291`); zebra `9f3166b96` (`methods.rs:3597-3611`);
lightwalletd `61fee32` (`frontend/service.go:549-576`).

---

## 55. zaino — `get_lightd_info` reports the last-listed (already-activated) network upgrade as `upgrade_name`/`upgrade_height` instead of the next *pending* one, contradicting its own proto contract and lightwalletd

**DRAFT. Severity: low.**

**Title:** Both backends set `upgrade_name`/`upgrade_height` from
`latest_network_upgrade(...) = upgrades.last()` (highest-height upgrade, status never
inspected), whereas the proto documents these as "next pending upgrade, empty/zero if
none scheduled" and lightwalletd computes exactly the lowest-height `pending` upgrade —
so in steady state (all NUs active, none pending) zaino shows a live upgrade as "next
scheduled"

**Body:**

Shared helper `latest_network_upgrade` (`packages/zaino-state/src/backends.rs:13`):
`upgrades.last().map(|(_, upgrade)| upgrade)` — last-inserted (highest-height) upgrade,
returned unconditionally, status never checked. Zebra's `into_parts`
(`methods.rs:3766`) returns `(NetworkUpgrade, Height, NetworkUpgradeStatus)`; zaino keeps
`.0`/`.1` and discards the status (`.2`). Both backends are field-identical
(`state.rs:2745-2750,2774-2775`; `fetch.rs:2066-2071,2095-2096`). The proto documents
`upgrade_name` = "name of next pending network upgrade, empty if none scheduled" and
`upgrade_height` = "height of next pending upgrade, zero if none is scheduled"
(`zaino-proto/src/proto/service.rs:162-167`).

lightwalletd computes the contract: `common/common.go:287-294` keeps only `u.Status ==
"pending"` with the lowest `ActivationHeight`, and `:316-317` sets `UpgradeName`/`UpgradeHeight`
→ `""`/`0` when nothing is pending. In Zebra, `upgrades` is built in height order with
`Active` if `tip_height >= activation_height` else `Pending` (`methods.rs:1069-1090`), so
`.last()` is the highest-height upgrade regardless of status.

**Failure mode.** In steady state (all NUs active, none pending — the normal mainnet
condition between upgrades) lightwalletd returns `upgrade_name=""`, `upgrade_height=0`,
while zaino returns the most-recent already-activated upgrade's name and its past
activation height. A client displaying "next scheduled upgrade" shows an already-live
upgrade as if pending. Informational field only.

Observed at zaino `0e057e22` (`packages/zaino-state/src/backends.rs:13`;
`backends/state.rs:2745-2750,2774-2775`; `backends/fetch.rs:2066-2071,2095-2096`;
`zaino-proto/src/proto/service.rs:162-167`;
`zaino-serve/src/rpc/grpc/service.rs:219`); zebra `9f3166b96` (`methods.rs:1069-1090,3766`);
lightwalletd `61fee32` (`common/common.go:287-317`).

---

## 56. zaino — `send_transaction` can never populate a nonzero `SendResponse.error_code`; a mempool rejection becomes a gRPC Status error instead of the `Ok(SendResponse{error_code, error_message})` the protocol defines and lightwalletd returns

**DRAFT. Severity: low.**

**Title:** Both backends only ever build `SendResponse{error_code: 0, error_message:
<txid>}` and `?`-propagate any submission failure, which the serve layer turns into a
gRPC Status error with no `SendResponse` payload — so the structured, nonzero
`error_code` the walletrpc proto defines (and lightwalletd emits inside a successful
response) is unreachable; both backends behave the same (no inter-backend split)

**Body:**

StateService `send_transaction` (`state.rs:2102-2110`) and FetchService
(`fetch.rs:1429-1437`) are byte-identical: `let tx_output =
self.send_raw_transaction(hex_tx).await?; Ok(SendResponse{ error_code: 0, error_message:
tx_output.hash().to_string() })` — `error_code` is a hardcoded `0` literal reachable only
on success; `error_message` is bare hex (no quotes). The connector's
`send_raw_transaction` returns `Result<_, RpcRequestError<SendTransactionError>>`
(`zaino-fetch/src/jsonrpsee/connector.rs:569-576`); a `sendrawtransaction` rejection is
the `Err` arm, which `?`-propagates and is turned into a gRPC Status by the serve macro
`client_method_helper!` `.map_err(Into::into)?` under `Indexer::Error: Into<tonic::Status>`
(`service.rs:38,161`) — no `SendResponse` payload.

The proto defines the opposite: a nonzero `errorCode` rides inside a SUCCESSFUL gRPC
response (walletrpc `service.proto:84-90`). lightwalletd honours it
(`frontend/service.go:455-509`): on rejection it splits zcashd's `CODE:MESSAGE` and
returns `Ok(SendResponse{ErrorCode: <nonzero>, ErrorMessage})`; on success `errMsg =
string(result)` = raw JSON (the txid WITH quotes). A client that branches on the code —
e.g. zcash-android-wallet-sdk `backend-lib/.../tor.rs:152-166` (`if response.error_code
== 0 { Ok(()) } else { Err(...) }`) — never receives it from zaino.

**Failure mode.** A wallet submits a tx the mempool rejects (already-in-chain,
insufficient fee, double-spend). Against lightwalletd it gets `Ok(SendResponse{error_code:
-25/-26, error_message})` and can branch on the code; against zaino it gets a gRPC Status
error, losing the structured `error_code`. Both zaino backends behave identically (no
inter-backend split); wallet impact PLAUSIBLE (clients typically handle both). Secondary:
success `error_message` is unquoted hex vs lightwalletd's quoted JSON.

Observed at zaino `0e057e22` (`packages/zaino-state/src/backends/state.rs:2102-2110`;
`backends/fetch.rs:1429-1437`; `zaino-fetch/src/jsonrpsee/connector.rs:569-576`;
`zaino-serve/src/rpc/grpc/service.rs:38,161`); walletrpc `service.proto:84-90`;
lightwalletd `61fee32` (`frontend/service.go:455-509`); zcash-android-wallet-sdk
(`backend-lib/src/main/rust/tor.rs:152-166`).

---

## 57. lightwalletd (NOT zaino) — `GetTreeState` hex-encodes `id.Hash` without reversing, contradicting its own little-endian wire convention; zaino handles the byte order correctly

**DRAFT. Severity: low. Target: lightwalletd — NO zaino defect.**

**Title:** Recorded for completeness: zaino correctly treats `BlockID.hash` as
little-endian internal (serialized) order and reverses it to the big-endian hash string
for lookup; lightwalletd's `GetTreeState` hex-encodes `id.Hash` WITHOUT reversing,
contradicting its own convention (`GetLatestBlock`/`GetTransaction` treat wire hashes as
little-endian) — a latent lightwalletd bug, not a zaino divergence

**Body:**

Zaino (both backends) treats `BlockID.hash` as little-endian and reverses it:
`blockid_to_hashorheight → zebra block::Hash` where `.0` is serialized/LE, `Display`
reverses to big-endian, and `HashOrHeight::from_str` re-parses (`state.rs:2516-2525,
1475-1481`; `fetch.rs:1836-1845`; zebra `block/hash.rs:28-42,82-85`). lightwalletd
hex-encodes `id.Hash` WITHOUT reversing: `frontend/service.go:328-329` `// id.Hash is
big-endian, keep in big-endian for the rpc` `hash := hex.EncodeToString(id.Hash)`. This
contradicts its own LE convention — `GetLatestBlock` (`service.go:83-84`, `// Binary
block hash should always be in little-endian format`, `Reverse`) and `GetTransaction`
(`service.go:412-413`, `// Convert from little endian to big endian`, `Reverse`).
`GetTreeState` is lightwalletd's lone byte-order outlier.

Cross-check (no zaino divergence in siblings): zaino `get_transaction`
(`state.rs:2076-2084`, `transaction::Hash` reverses LE→BE) matches lightwalletd
`GetTransaction`; zaino `get_block` uses `block::Hash(h.0)` as LE and lightwalletd
rejects by-hash `GetBlock`.

**Failure mode.** A client that takes a `BlockID` from `GetLatestBlock` (little-endian
hash) and passes it to lightwalletd `GetTreeState` calls `z_gettreestate` with a reversed
hash string and gets `InvalidArgument`/not-found; zaino resolves the same bytes to the
correct block. The defect is in lightwalletd, not zaino — logged so the audit's zaino
byte-order review is on record.

Observed at zaino `0e057e22` (`packages/zaino-state/src/backends/state.rs:1475-1481,
2076-2084,2516-2525`; `backends/fetch.rs:1836-1845`); zebra local
(`zebra-chain/src/block/hash.rs:28-42,82-85`); lightwalletd `61fee32`
(`frontend/service.go:83-84,328-329,412-413`).
