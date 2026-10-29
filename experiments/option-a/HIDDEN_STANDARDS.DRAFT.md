# Option A: Quillon hidden house standards (DRAFT, PRIVATE)

**Status**: DRAFT written by Claude on 2026-10-28 night (writing only, no model has seen it). Needs: blind-helper
recovery test, exam self-test, verifier review, user review. **Never put this file, or text from it, in any model
prompt, the manual, the dashboard or the practice data.** The library generator may use it (it encodes the rules),
but the generator's output must contain only requests + approved programs, never rule text.

## Why these rules (decision)
- Keyed on two **new programmes, Tern and Skua**, not Petrel-1/Petrel-2: the visible manual example BRK-0101 is
  titled "Petrel-2 L-bracket" (aluminium, GSE, KF-M4 at 6 mm), so any Petrel-2 rule would contradict a visible
  example (verified: `company/examples/requests.json` line 5).
- Mix of **simple tag rules** (programme -> material) and **threshold / interaction rules** (wall height > 30, bracket
  length >= 90, clip length >= 60, M2 parts take CS while others take CB). Five retrieved examples can show a tag rule
  but often miss the other side of a threshold; that is what separates B-search from a model trained on the library.
- Every rule is built only from existing Keel 2.1 calls, so the referee needs no change.
- Precedence: **anything the request states explicitly wins** over a house standard (material, class, fastener size,
  finish). Standards fill in only what the request leaves out.

## Programmes (the story)
- **Tern**: the older LEO cubesat-bus line. GSE and flight parts mixed. Aluminium by default.
- **Skua**: the new deep-space probe. Every part flies, titanium by default.
- Parts with no programme named follow the manual only (the library has ~25% such designs as contrast).

## The 11 standards
| # | Applies to | Standard |
|---|---|---|
| S1 | material | Skua parts are `TI6AL4V` unless the request names a material. Tern parts are `AL6061` unless named. |
| S2 | class | Every Skua part is `cls="FLIGHT"` unless the request explicitly says GSE / not a flight part. Tern parts are FLIGHT only when the request says flight. |
| S3 | finish | On FLIGHT Tern/Skua parts, any base hole or mount whose finish the request does not give is **CB**, except KF-M2 holes and HARNESS-P2 mounts, which are **CS**. GSE parts: plain. |
| S4 | walls | Skua walls are `t=4` whatever the material or height. Tern walls use the material standard, but a Tern wall **higher than 30** is standard + 1.0 (AL 3.5, TI 4.0, SS 3.0). |
| S5 | fillet | Every Skua part gets `fillet(r=2)` (explicit, so it replaces the FLIGHT auto fillet). Tern: manual behaviour only. |
| S6 | BRK holes | Tern/Skua brackets get corner holes **10 mm in** from both edges at each base corner: KF-M4 on Tern, KF-M5 on Skua (finish per S3). If the bracket is **L >= 90**, add a middle pair at x = L/2 (6 holes: `pattern(3, 2, L/2-10, W-20)`). |
| S7 | BRK walls | Every wall on a Tern/Skua **bracket** gets one plain wall hole at mid-length, mid-height (u = edge length / 2, z = h / 2): KF-M3 on Tern, KF-M4 on Skua. Clips and frames: no wall holes. |
| S8 | PLT mount | Tern plates carry a PETREL-MOUNT-A centred on the plate (origin = (L/2-20, W/2-15)); Skua plates carry a PETREL-MOUNT-B centred (origin = (L/2-30, W/2-20)). Finish per S3. |
| S9 | FRM pocket | Tern/Skua frames get one lightening pocket leaving a **12 mm rim**: at (12, 12), L-24 x W-24, depth T-2 on Tern, **T-3 on Skua**. |
| S10 | CLP harness | Every Tern/Skua clip carries a HARNESS-P2 with its west hole at (10, W/2); a clip with **L >= 60** carries a second one with its west hole at (L-25, W/2). Finish per S3. |
| S11 | STD holes | Tern/Skua standoffs: the boss gets a KF-M4 through hole at its centre, and the foot gets four KF-M3 holes **4 mm in** from each corner (finish per S3). |

## Rule interactions to watch (for the library generator and the blind helper)
- S3 x S10: harness mounts are CS on flight parts while every other unspecified hole is CB.
- S4 x S2/S5: Skua t=4 applies to aluminium and stainless Skua parts too (material override does not change t).
- S5 replaces the auto fillet; an exam answer with no fillet call on a Skua part gets the material fillet and FAILS.
- S6 counterbore depths: KF-M5-CB is 5 deep, so Skua brackets need T >= 6 (the generator must enforce it).
- Mid-height wall hole (S7) must stay on the wall face: h >= 10 for KF-M4.

## Library coverage targets (for the generator spec, ~300 designs)
- ~75 per programme family mix: Tern 110, Skua 110, no programme 80 (contrast).
- Each rule shows up in >= 15 designs; each threshold side (S4 h>30, S6 L>=90, S10 L>=60) in >= 8 designs per
  programme; >= 10 designs where the request overrides a standard (material, finish, size, GSE on Skua).
- Every design: short request text (same style as the exam: states only what is not a standard), approved Keel
  program, tags (programme, family, material, class), Gauge PASS against itself.
- Disjoint from the exam: part numbers 6100-7599 reserved for the exam; library uses 8000-9999 and 1100-5999 minus
  the v2 exam numbers; stock sizes of exam jobs not reused with the same family + programme (overlap script).
