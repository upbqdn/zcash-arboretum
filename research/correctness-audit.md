# Correctness audit — guide-fix worklist

Wave-0, 2026-07-16.

## Method

A model-diff pass: each guide's factual claims were diffed against ground truth
(zcash/zips `69610984`, protocol.tex `662dc87`; orchard HEAD `bef8a27`;
librustzcash `e30517e4`; zebra-crosslink `6d02a1b`; tfl-book `fe6e1d6f`;
voting-circuits `4c39abd`, vote-sdk `cb915f5`; RFC 9591; ePrint 2024/436). Each
divergence is sorted into one of two bins:

- **guide-fix** — the guide is wrong; correct the guide. Tracked here.
- **upstream defect** — the guide is right, the upstream source is wrong.
  Tracked in `upstream-defects.md`.

This file is the guide-fix bin only. Findings are firsthand-cited but this wave
is breadth-first (a shallow diff, not a per-volume grid), so absence of a finding
in a volume is not evidence of correctness there.

## This wave's coverage

Volumes touched: Ironwood, ZSA, Wallet, Crosslink, FROST, Voting.
Bin totals: **3 guide-fixes** (1 medium, 2 low), 11 upstream defects (2 medium,
9 low — see the other file).

All three guide-fixes are localized citation/scope errors, not structural
rewrites; the guide reasoning is sound in each case and the surrounding text
already states the correct fact, so these are one- to three-line edits.

## Priority worklist

| # | Sev | Volume : section | Area |
|---|-----|------------------|------|
| G1 | medium | Ironwood : `sec:action-stmt` (Def A8/A9) | `enableSpends` rule for `flagsIronwood` phrased as universal, not coinbase-only |
| G2 | low | Ironwood : `sec:action-stmt` (`rem:action-versions`) | `crate orchard 0.15.0` version pin — no such release exists |
| G3 | low | ZSA : `sec:zsa-v6` (Action Groups) | ZIP-230 `nAGExpiryHeight` MUST mis-attributed to the rationale section |

---

### G1 — `enableSpends` consensus rule for `flagsIronwood` reads as universal (medium)

**Volume : section.** Ironwood Guide, `sec:action-stmt`, Definition "Orchard
Action statement" A8/A9 — `ironwood-guide.tex:1512-1514`.

**What's wrong.** The clause "and from NU6.3 the `enableSpends` bit of
`flagsIronwood` MUST be 0 --- ZIP-229" has its own subject and a temporal
("from NU6.3") rather than coinbase scope, so it asserts a *universal* NU6.3
rule. ZIP-229 forces `enableSpends = 0` on `flagsIronwood` only **for coinbase
transactions** (`zip-0229.md:256-257`); ZIP-258's NU6.3 universal consensus list
(`zip-0258.md:88-99`) carries no such blanket rule — only coinbase-empty-Orchard,
`enableCrossAddress = 0`, and `valueBalanceOrchard >= 0`. Read literally the
guide forbids ever spending an Ironwood note, inverting the purpose of the pool
value flows into. Contradicted directly by `protocol.tex:13574` (permits
`nActionsIronwood > 0` with `enableSpendsIronwood = 1`) and
`protocol.tex:13579-13580` ("at least one of `enableSpendsIronwood` and
`enableOutputsIronwood` MUST be 1" from NU6.3).

**The fix.** Re-scope the second clause to coinbase, or drop it. Correct
statement: coinbase must set `enableSpendsIronwood = 0` (the v5
`enableSpendsOrchard = 0` analog, `protocol.tex:13654`); non-coinbase Ironwood
actions may set `enableSpends = 1`. If a universal NU6.3 line is wanted, cite the
real ones from `zip-0258.md:88-99`.

---

### G2 — `crate orchard 0.15.0` version pin does not exist (low)

**Volume : section.** Ironwood Guide, `sec:action-stmt`, Remark
`rem:action-versions` — `ironwood-guide.tex:1535`; recurs at `:1986` and `:2472`.

**What's wrong.** Body text pins the Ironwood circuit source to "crate `orchard`
0.15.0 `src/circuit.rs`", but the Ironwood code is unreleased dev on 0.14.0.
orchard HEAD `bef8a27` (`git describe` = `0.14.0-18-gbef8a27`): `Cargo.toml:3`
`version = "0.14.0"`, no `0.15.0` tag and no `0.15.0` string anywhere;
`CHANGELOG.md` top section is `[Unreleased]` and its body is exactly the Ironwood
circuit / `enableCrossAddress` work. The cited symbol names are all correct
(`supports_cross_address_restriction` at `circuit.rs:147`; the
`InsecurePreNu6_2` / `FixedPostNu6_2` / `PostNu6_3` enum) — only the version
number is wrong. The guide contradicts itself: its own methodology note at
`ironwood-guide.tex:2470-2473` pins "crate orchard at git commit `bef8a27e`
(v0.14.0, 2026-06-16)" for the same circuit claims.

**The fix.** Replace "0.15.0" with the pin the methodology note already uses —
orchard git `bef8a27` (0.14.0 + unreleased Ironwood) — at `:1535`, `:1986`, and
`:2472`. A phrasing like "crate `orchard`, unreleased @ `bef8a27` (`src/circuit.rs`)"
removes the forward-looking guess and matches `:2470-2473`.

---

### G3 — ZIP-230 `nAGExpiryHeight` MUST mis-attributed to the rationale section (low)

**Volume : section.** ZSA Guide, `sec:zsa-v6` (Orchard fields: Action Groups) —
`zsa-guide.tex:2955-2957`.

**What's wrong.** After citing "(ZIP-230, Rationale for `nAGExpiryHeight`)", the
guide writes "The same rationale section states ``In NU7, `nExpiryHeight` MUST be
set to 0''", attributing the sentence to the rationale section. The sentence is
verbatim in ZIP-230 (`zip-0230.rst:321-322`) but lives in the **normative MUST
bullet list** that *precedes* the rationale heading (heading at `zip-0230.rst:324`);
the rationale body (`:327-329`) only introduces `nAGExpiryHeight` for ZIP-228
forward compatibility and draws a ZIP-203 analogy — it never contains the "In NU7
... MUST be set to 0" sentence (grep confirms the sentence occurs once, at line
321). The mis-attribution also demotes a normative MUST to non-normative
rationale prose.

**The fix.** Attribute the sentence to ZIP-230's normative consensus-rule bullet
list (`zip-0230.rst:315-322`), not "Rationale for `nAGExpiryHeight`", and label
it normative. Keep the separate, correct citation of the rationale section for
the `nAGExpiryHeight = 0`-by-consensus convention.

---

## Wave 1

Wave-1, 2026-07-16. Same model-diff method as Wave-0.

Volumes touched (guide-fix bin): Ironwood, ZSA. Bin totals: **3 guide-fixes**
(1 high, 1 medium, 1 low). Two are Ironwood `DEPLOYED-at-bef8a27` attribution
errors — the guide paraphrases the spec correctly but attributes note-format
code and a version model to orchard `bef8a27` that do not exist there; the
circuit/cross-address side it also cites *is* deployed, which is what makes the
false half plausible. The third is an isolated off-by-79-lines citation in ZSA.

### Priority worklist

| # | Sev | Volume : section | Area |
|---|-----|------------------|------|
| G4 | high | Ironwood : "The Ironwood note…" / `rem:iw-legacy-rcm` | ZIP-2005 recoverable note format claimed DEPLOYED at orchard `bef8a27`; none of the note-format code exists there |
| G5 | medium | Ironwood : `sec:iw-pools` "One circuit, one verifying key" | Fabricated orchard bundle/circuit version model (`ValuePool`/`ProtocolVersion` enums, `permits_cross_address_transfers`) — not the deployed enums |
| G6 | low | ZSA : Orchard fields (AssetId subscript note) | `zip-0227.rst` subscript-omission citation off by ~79 lines (points at a figure) |

---

### G4 — ZIP-2005 recoverable note format claimed DEPLOYED at orchard `bef8a27`; the note-format code does not exist there (high)

**Volume : section.** Ironwood Guide, §"The Ironwood note: lead byte 0x03 and
the hashed trapdoor" / Remark `rem:iw-legacy-rcm` — `ironwood-guide.tex:2180-2182`,
`2252-2261`, `2270-2273` (headline ~`2255`).

**What's wrong.** The guide presents the ZIP-2005 quantum-recoverable Ironwood
note format as *deployed in crate `orchard` @ `bef8a27`*: a note-version tag
`NoteVersion {V2, V3}` with `Note::from_parts` "now taking one" (`2181-2182`,
"crate orchard at bef8a27 src/note.rs"); a `Note::rcm()` dispatching on
`NoteVersion` — "V2 to `rcm_v2`, V3 to `rcm_v3`", the latter one BLAKE2b-512 call
over the 137-byte `pre_rcm` `rseed || 0x0B || gd* || pkd* || LE64(v) ||
LE256(rho) || LE256(psi)` ("crate orchard at bef8a27 src/note.rs, `rcm_v3`,
domain separator constant `0x0B`", `2255-2261`); and note encryption where
"sealed marker types give `OrchardDomain` (expects `0x02`) and `IronwoodDomain`
(expects `0x03`) … src/note_encryption.rs" (`2270-2273`). At `bef8a27`
(`git describe` = `0.14.0-18-gbef8a27`) **none** of this note-format code exists.
The deployed `rcm()` is the legacy single-tag trapdoor: `src/note.rs:132-136`
`NoteCommitTrapdoor(to_scalar(PrfExpand::ORCHARD_RCM.with(&self.0,
&rho.to_bytes())))`, with `ORCHARD_RCM = 0x05` (`zcash_spec-0.2.1
src/prf_expand.rs:88`), i.e. `rcm = ToScalar(PRFexpand_rseed(0x05 || rho))` — no
`pre_rcm`, no 137-byte BLAKE2b, no `0x0B`. `from_parts` (`:182-187`) takes four
args, no version. `note_encryption.rs:63` hardcodes `if plaintext[0] != 0x02 {
return None; }` and `:172` `np[0] = 0x02;` — one `OrchardDomain` (`:84`), no
`0x03` branch, no `IronwoodDomain`, no sealed marker pair. Crate-wide grep of
`src/`: `NoteVersion`, `rcm_v3`, `rcm_v2`, `IronwoodDomain`, `pre_rcm` all zero
hits. The circuit/cross-address side the guide cites *is* genuinely deployed
(`OrchardCircuitVersion::Ironwood`, `DISABLE_CROSS_ADDRESS`), and the spec
paraphrase (Definition `iw-derive`) correctly matches ZIP-2005 §4.7.3 /
`protocol.tex`; only the "deployed at `bef8a27`" attribution is false.

**The fix.** Re-scope the three note-format passages from DEPLOYED to
spec/planned. Drop the "crate orchard at bef8a27 src/note.rs /
src/note_encryption.rs" attributions at `2181-2182`, `2255-2261`, `2270-2273`
(and the "Every Ironwood-pool output note is a recoverable note" headline
~`2255`), or replace them with the ZIP-2005 spec citation. Keep Definition
`iw-derive` as the (correct) spec statement it already is. State that the
deployed `rcm()` at `bef8a27` is the legacy single-tag trapdoor
(`note.rs:132-136`), not `rcm_v3`.

---

### G5 — fabricated orchard bundle/circuit version model (medium)

**Volume : section.** Ironwood Guide, §`sec:iw-pools` "One circuit, one verifying
key" — `ironwood-guide.tex:2162-2172`.

**What's wrong.** The paragraph describes orchard's version model as "the pair of
a `ValuePool {Orchard, Ironwood}` and a `ProtocolVersion {InsecureV1, V2, V3}`;
`circuit_version()` maps V3 to `PostNu6_3` for both pools, `note_version()` maps
Orchard to V2 and Ironwood to V3, and `permits_cross_address_transfers()` is
false exactly for the pair `(V3, Orchard)`". None of these enums/methods exist at
`bef8a27`. The real model: `BundleFormat {PreNu6_3, Nu6_3}` (`src/bundle.rs:89-93`);
`OrchardCircuitVersion {InsecurePreNu6_2, FixedPostNu6_2, Ironwood}`
(`src/circuit.rs:125-135`); `circuit_version()` returns an `OrchardCircuitVersion`
(`Ironwood` for NU6.3, not "PostNu6_3", `src/builder.rs:1251`); the cross-address
predicate is `OrchardCircuitVersion::supports_cross_address_restriction()`
(`src/circuit.rs:147`) / `Flags::cross_address_enabled()` (`src/bundle.rs:283-284`).
Crate-wide grep of `src/`: `ValuePool`, `enum ProtocolVersion`, `InsecureV1`,
`PostNu6_3`, `note_version`, `permits_cross_address_transfers` all zero hits. The
paragraph is internally inconsistent with the guide's own text: `:1536` correctly
names `OrchardCircuitVersion::supports_cross_address_restriction` and `1530-1544`
gives the real three-version model (insecure NU5 / NU6.2 correction / NU6.3
Ironwood). Possible dedup with G2 (the `0.15.0` version-pin error) — same
"orchard version" area, but distinct: G2 is a wrong version *number*, G5 a wholly
fabricated enum/method *model*.

**The fix.** Rewrite `2162-2172` to the deployed model — `BundleFormat
{PreNu6_3, Nu6_3}`, `OrchardCircuitVersion {InsecurePreNu6_2, FixedPostNu6_2,
Ironwood}`, `circuit_version()` → `Ironwood` at NU6.3, cross-address gated by
`supports_cross_address_restriction()` / `Flags::cross_address_enabled()` —
matching the guide's own correct `1530-1544`.

---

### G6 — ZSA `AssetId`-subscript citation off by ~79 lines (low)

**Volume : section.** ZSA Guide, Orchard fields (the `AssetId` subscript
convention) — `zsa-guide.tex:689-690`.

**What's wrong.** The guide writes "The subscript $\mathsf{AssetId}$ may be
omitted when clear from context (`zip-0227.rst:303--308`)." At the guide's target
commit `69610984` (anchored `zsa-guide.tex:118`), `zip-0227.rst:303-308` is the
OrchardZSA asset-identifier-relation *figure* block (`:303` `.. figure::
../rendered/assets/images/zip-0227-asset-identifier-relation-orchard-zsa.png`,
`:304-306` `:width:`/`:align:`/`:figclass:` directives, `:308` the "Diagram
relating the Issuer identifier, asset description, asset description hash, Asset
Identifier, Asset Digest, and Asset Base for the OrchardZSA Protocol." caption).
The actual subscript-omission note is at `zip-0227.rst:224`: "**Note:** To keep
notations light and concise, we may omit $\mathsf{AssetId}$ in the subscript when
the Asset Identifier is clear from the context." (grep confirms it is the only
such note in the file). Off by ~79 lines. Isolated: ~15 other zip-0227/0226/0230
line citations in the same guide spot-checked correct.

**The fix.** Change the citation at `zsa-guide.tex:690` from `zip-0227.rst:303--308`
to `zip-0227.rst:224`.

---

## Wave 2

Wave-2, 2026-07-16. Same model-diff method as Wave-0/1.

Volumes touched (guide-fix bin): Ironwood. Bin totals: **2 guide-fixes** (1 high,
1 medium). Both are Ironwood `DEPLOYED-at-bef8a27` over-attributions in the same
class as Wave-1 G4/G5: the guide's spec paraphrase and reasoning are sound, but it
pins v6-digest and provenance facts to orchard `bef8a27` (v0.14.0) that are not true
at that commit. G7 continues the finding that the Ironwood NU6.3 API is unreleased
dev on 0.14.0; G8 corrects the "version librustzcash pins" provenance (librustzcash
actually pins the published orchard **0.15.0** crate, not `bef8a27`). Both firsthand
re-confirmed: orchard `bef8a27` = `0.14.0-18-gbef8a27`, zero `_v6`/Ironwood
personalization strings in `src/`; librustzcash `e30517e4` `Cargo.lock` and workspace
`Cargo.toml` both pin `orchard = 0.15.0`.

### Priority worklist

| # | Sev | Volume : section | Area |
|---|-----|------------------|------|
| G7 | high | Ironwood : `sec:iw` "The Ironwood pool" (v6 digest ¶) | Full NU6.3 v6/Ironwood txid+auth BLAKE2b personalizations claimed DEPLOYED at orchard `bef8a27`; none exist there (introduced in 0.15.0) |
| G8 | medium | Ironwood : `sec:iw-pools` provenance sentence | "orchard `bef8a27` … the version librustzcash pins" — librustzcash pins orchard 0.15.0; `bef8a27` is 0.14.0 |

---

### G7 — v6/Ironwood txid+auth personalizations claimed DEPLOYED at orchard `bef8a27`; none exist there (high)

**Volume : section.** Ironwood Guide, §`sec:iw` "The Ironwood pool", the v6-digest
paragraph — `ironwood-guide.tex:2146-2155`.

**What's wrong.** The paragraph lists the full NU6.3 v6/Ironwood BLAKE2b txid+auth
personalizations — `ZTxIdIronwd_H_v6`, `ZTxIdIrnActCH_v6`, `ZTxIdIrnActMH_v6`,
`ZTxIdIrnActNH_v6`, `ZTxAuthIrnwdH_v6`, plus revised Sapling/Orchard-branch
`ZTxIdSSpendNH_v6`, `ZTxAuthSapliH_v6`, `ZTxIdOrchardH_v6`, `ZTxAuthOrchaH_v6` — and
attributes them all as "deployed in crate `orchard` at `bef8a27`,
`bundle/commitments.rs`, and in `zcash_primitives`, `transaction/txid.rs`". At
`bef8a27` (`git describe` = `0.14.0-18-gbef8a27`) **none** of these strings exist.
`src/bundle/commitments.rs` there defines only five non-versioned 16-byte
personalizations — `ZTxIdOrchardHash`, `ZTxIdOrcActCHash`, `ZTxIdOrcActMHash`,
`ZTxIdOrcActNHash`, `ZTxAuthOrchaHash` — and `hash_bundle_txid_data(bundle, format)`
applies no per-pool/version personalization dispatch (`format` feeds only the flags
byte). No Ironwood txid function exists; `git grep _v6 bef8a27 -- src/` and
`git grep 'ZTxIdIronwd\|ZTxIdIrnAct\|ZTxAuthIrnwd' bef8a27 -- src/` both return zero
hits (re-confirmed); there is no 0.15.0 tag in the local repo. Secondary: in
librustzcash `zcash_primitives/src/transaction/txid.rs` @ `e30517e4` only the two
Sapling v6 personalizations are production (`ZTxIdSSpendNH_v6:44`,
`ZTxAuthSapliH_v6:54`); the Orchard/Ironwood `_v6` strings appear only as expected
literals in `tests.rs` (`ZTxAuthOrchaH_v6:125`, `ZTxIdOrchardH_v6:159`,
`ZTxIdIronwd_H_v6:160`), never in production code. Same class as Wave-1 G4/G5
(Ironwood `DEPLOYED-at-bef8a27` over-attribution), distinct passage (the v6 digest
personalizations rather than note format / version enums).

**The fix.** Re-scope the v6-digest paragraph from DEPLOYED to spec/planned: keep the
ZIP-229 personalization list as the spec statement it is, but drop the "deployed in
crate `orchard` at `bef8a27`, `bundle/commitments.rs`" attribution (the five strings
there are the non-versioned `ZTxIdOrchardHash` set, not the `_v6` set), and scope the
`zcash_primitives`/`txid.rs` cite to the two Sapling `_v6` personalizations that are
actually production — noting the Orchard/Ironwood `_v6` strings exist there only as
test vectors.

---

### G8 — "orchard `bef8a27`, the version librustzcash pins" — librustzcash pins 0.15.0 (medium)

**Volume : section.** Ironwood Guide, `sec:iw-pools` provenance sentence —
`ironwood-guide.tex:2043-2045`, echoed at `2481-2483`.

**What's wrong.** The provenance sentence grounds Ironwood-pool "deployed behaviour"
on "crate `orchard` at `bef8a27` (crates.io; the version `librustzcash` pins)", and
`2481-2482` confirms the pin as "crate `orchard` at git commit `bef8a27e` (v0.14.0,
2026-06-16)". But `bef8a27` is not the orchard version librustzcash `e30517e4` depends
on: that tree's `Cargo.lock` pins `orchard` `version = "0.15.0"` from
`registry+…crates.io` (checksum `cca2ede6…`), and its workspace `Cargo.toml` requires
`orchard = { version = "0.15.0", … }` (both re-confirmed firsthand). Meanwhile orchard
`bef8a27` is `version = "0.14.0"` (`git describe` = `0.14.0-18-gbef8a27`), with the
NU6.3/Ironwood API staged in `CHANGELOG.md` `[Unreleased]`, not a release. So the git
commit the guide cites (0.14.0 + unreleased Ironwood) and the crate librustzcash
actually pins (published 0.15.0) are different artifacts; the parenthetical "the
version librustzcash pins" is false. Interacts with Wave-0 G2: G2 flagged the guide's
bare "orchard 0.15.0" citation as pointing at a release absent from the *local orchard
repo* — this finding shows the complement, that 0.15.0 *was* published (librustzcash's
lockfile references it with a checksum) and is the true pin, while the `bef8a27` git
commit the guide equates with that pin is the separate unreleased 0.14.0 tree.

**The fix.** Correct the parenthetical: `bef8a27` is orchard **0.14.0 + unreleased
Ironwood dev**, *not* the version librustzcash pins (that is the published **0.15.0**
crate on crates.io). Either cite `bef8a27` as the unreleased dev tree the guide reads
the Ironwood code from and separately note librustzcash pins the released 0.15.0, or
drop the "the version librustzcash pins" clause. Apply at `2043-2045` and `2481-2483`,
and reconcile with G2's fix so the guide's orchard-version story is internally
consistent.

---

## Wave 3

Wave-3, 2026-07-16. Same model-diff method as Wave-0/1/2, run as the **new-axis
pass**: deliberately aimed at surfaces no prior wave touched — Zaino's gRPC service
backends, the FROST crates (reddsa / frost-core), and the QED-it ZSA fork's flags
parser — instead of re-diffing Ironwood/Crosslink.

Volumes touched (guide-fix bin): Sync. Bin totals: **1 guide-fix** (low), plus 5
upstream defects (2 medium, 3 low — see the other file). The lone guide-fix is a
Zaino `DEPLOYED-at-0e057e22` over-attribution in the same class as Wave-1/2's orchard
`bef8a27` errors: the Sync Guide's wire/divergence reasoning is sound, but it credits
deployed Zaino with a `protoVersion` value that lives only in dead code. One- to
three-line edit; the surrounding text already states the correct wire facts.

### Priority worklist

| # | Sev | Volume : section | Area |
|---|-----|------------------|------|
| G9 | low | Sync : `sec:sync-compact-wire` / `sec:sync-compact-divergences` | "Zaino sets `protoVersion` to 1 (`block.rs:218`)" — deployed Zaino serves `proto_version: 0` on every path; the `=1` literal is unreachable dead code |

---

### G9 — "Zaino sets protoVersion to 1" credits a dead-code literal as deployed behaviour (low)

**Volume : section.** Sync Guide, `sec:sync-compact-wire` — the "three deployed
behaviours" list, `sync-guide.tex:270-273` — echoed in `sec:sync-compact-divergences`
at `:713-714` and `:731-733`. The guide pins Zaino `0e057e22` at `:206` and `:842`.

**What's wrong.** The guide lists as one of "three deployed behaviours" for
`protoVersion` that "`Zaino` sets it to~1 (`zaino-fetch`, `src/chain/block.rs`,
line~218)" (`:272-273`), and the divergences section repeats "`Zaino` sets~1"
(`:713-714`) and concludes "`Zaino` still sets a field the canonical proto reserves"
(`:731-733`) — all framed as deployed-server behaviour. At the pinned commit
`0e057e22`, every compact-block *serving* path emits `proto_version: 0`. The
`proto_version: 1` at `block.rs:218` sits inside `FullBlock::into_compact_block` (def
`:186`), whose only caller (`git grep -nw into_compact_block` → def + one hit) is
`block.rs:177`, a `format!(…)` debug string in the `ParseError::InvalidData` branch of
`parse_from_hex` — the CompactBlock it builds is `Debug`-formatted into an error
message and dropped, never serialized. No serving path and no test call it. Every
serving builder emits `0`: `IndexedBlock::to_compact_block` (`legacy.rs:1113`),
finalized-V1 `get_compact_block` (`compact_block.rs:285`), and `get_compact_block_stream`
(`compact_block.rs:1201`); both gRPC-facing backends route through `chain_index`
(`fetch.rs:965`; `NodeBackedChainIndexSubscriber::get_compact_block`,
`chain_index.rs:1711-1752`) to exactly those three. `git grep -n proto_version` over
all of zaino returns only these CompactBlock literals, and `block.rs:218` is the sole
non-zero one — the dead one. Because the vendored proto declares a plain proto3 scalar
`uint32 protoVersion = 1;` (`compact_formats.proto:28`; generated `pub proto_version:
u32`), the served `0` is omitted on the wire — byte-indistinguishable from
lightwalletd's unset field.

**The fix.** Two edits. (1) In `sec:sync-compact-wire`, drop Zaino from the "sets it
to~1" branch: deployed Zaino serves `proto_version: 0` on every path
(`compact_block.rs:285`, `legacy.rs:1113`); mention `block.rs:218`'s `=1` only as
unreachable dead code (a `Debug` string in a parse-error branch) if at all. The list
then has two on-wire behaviours — lightwalletd's absent field and Zaino's `0` — which
for a proto3 scalar serialize identically. (2) In `sec:sync-compact-divergences`,
correct "`Zaino` sets~1" (`:713-714`) to "Zaino serves 0 (byte-identical to
lightwalletd's unset field)", and delete the clause "`Zaino` still sets a field the
canonical proto reserves" (`:731-733`) — false at the pin, since serving `0` is
wire-indistinguishable from not setting it. The vendored-changelog-skew observation in
the same bullet (`:729-732`) is independent and stands.
