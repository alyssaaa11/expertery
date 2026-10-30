# Claude's blind rebuild (factory PLAN A4), 2026-10-30
Built from the job text only (jobs.jsonl "text"; references not opened; F5-1's reference had been seen, so F5-2 is used).
Run only in the cloud box + grader (rule: no AI-written code on the Mac). Pass bar: 10/10 at 1e-6.
Readings where the text left a choice (each is a wording risk if it fails):
- F3: groove from the two widths; the 16° side angle is only approximately consistent with them (rounded).
- F4: "slot 5.9 wide" read as rounded ends with the centreline endpoints as arc centres.
- F8: tabs fused to the plate; window corner radius as a vertical-edge fillet.
- F9: blind side port from X = 0 (centre) out past the +X face.
- F10: the recess bottom diameter is not given; read as the same wall slope as the outer cone. Rim ring = outer edge
  diameter 54.4, 4.9 wide inward. HIGH RISK: likely ambiguous wording.
- After writing these answers, Claude saw the gallery picture of F4-1 (reference slot has square ends; answer kept with rounded ends, unchanged). Disclosed so the F4 result is read correctly.
- Verifier G3 (2026-10-30): F4-1 removed from the run (not blind after the gallery). F4 is rebuilt after the generator fix, whose text states the slot ends, so knowing the reference's ends no longer helps.
- Expected now (verifier G1): F3, F7, F10 fail at 1e-6 because the text and the reference disagree; this run confirms G1, it is not the final blind-rebuild gate.
- After round 1c (jobs.jsonl e40099c4…): F4-2 (new, text says square ends), F8-1 (tab Y 29.6 → 29.7) and F10-1 (recess
  bottom + rim diameters now given) rewritten from the new texts only. F3-1/F7-1 texts unchanged (references fixed), answers kept.
  Run set: F1-1 F2-1 F3-1 F4-2 F5-2 F6-1 F7-1 F8-1 F9-1 F10-1. Gate: 10/10 PASS at 1e-6 (new_tight).
