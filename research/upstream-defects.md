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
