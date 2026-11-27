# phase lane: resume state and decision record (rewrite on every change)
Task: closed-form ridge with per-layer-stack (band / queen-state) components in the 512-slot budget; held-out R2/MAE vs round-1
pairs; write + exact-check nets; smoke 200 games 10+0.1 conc 12 vs closedform/out/pairs.nnue. This Mac only, no optimiser loop.
Labels: closedform/data/ds.npz = the DEFAULT net's depth-10 search (allowed in this lane), so every net here borrows the default
net's judgement through a least-squares fit.
STATE: COMPLETE. Running: nothing. Best net: out/p13x.nnue.

## Result (instruments: compare.py on the round-1 test split, 219,934 positions; exact_pc.py; smoke.sh + pool.py)
- out/p13x.nnue vs round-1 closedform/out/pairs.nnue: +62.0 Elo [95% +40.2, +84.4], 600 games over 3 opening seeds
  (4242: +72.3 +/- 36.4; 777: +31.4 +/- 41.2; 1234: +83.2 +/- 36.7; 0 time forfeits). The two seeds run after p13x was selected:
  +57.0 [+29.6, +85.0]. Not rated against UCI_Elo anchors.
- Attribution, same tuning objective: p13x vs its round-1-structure control p0x +57.9 +/- 39.2; p0x vs round-1 +20.9 +/- 40.7.
  So about +58 comes from the phase structure and about +21 from lambda retuning (sum consistent with +62 within noise).
- Test (exact engine ints): R2 .7853 vs .7762, MAE_cp 138.2 vs 141.1, MAE_cp(|label|<=300) 99.0 vs 100.2; 292 of 512 slots.
- Exactness: every built net PASSES exact_pc.py (3000/3000 engine == prediction, 375 per band, linear fill on every active slot,
  masked-off saturations ignored by the engine, planted fault fires).

## What p13x is
P13 = base (psq + threat + pair rows, group and material columns, 192 stack constants) + psq deltas per band b0..b7 + a
queenless (no queen on board) psq delta. Ridge lambdas psq 900, threat 2700, pair 3000; delta multipliers b0 .0123, b1 1,
b2 81, b3 81, b4 81, b5 27, b6 3, b7 1, noq 9 (b2-b4 are effectively off). Chosen by coordinate search on the VALIDATION split
(tune.py --objective trans = val MAE cp over |label|<=300 in bands 1-3); test untouched.

## Findings (most important first)
1. Overall R2 is a bad proxy for play here. p13t has the best test R2 (.7947, tuned on val R2) and plays +1.7 +/- 38.8 vs round 1.
   Across the 7 nets smoked, Elo tracked MAE(|label|<=300) in bands 2-3 (9-16 pieces). Tuning on that objective (bands 1-3) gave
   p13x, which replicated. The objective was picked after seeing smokes from seed 4242 only; seeds 777/1234 are the clean check.
2. Writer layout saves slots with no change to the fitted function: (a) a component masked to some stacks only needs linear fill
   on those stacks (fc_0 weight 0 elsewhere, so a saturated slot contributes 0; engine-verified); psq cap = 4*(maxband+1) pieces
   (proof). (b) side/cross split: slots of one sign holding only one side's non-king psq rows have at most 15 active rows (proof);
   the 2 king rows add 2. Round-1 pairs re-written: 476 -> 286 slots, predictions 99.99% bit-equal, exact PASS (out/r1).
3. DESIGN BOUNDS (not proofs): base threat 63 (round-1 value; measured max 50 over 2.21M positions x 2 perspectives); base pair 56
   (measured max 40; round 1 used the proof bound 120 here, so this is a new risk); masked threat/pair caps ceil(1.4 x measured).
   p13x's deltas are psq-only, so only the base threat 63 / pair 56 design bounds apply to it. A position past them would
   saturate a slot (wrong eval, no crash).
4. Per-band threat/pair deltas (P7, P9, P10) did not pay for their slots; a free endgame delta plus per-band endgame deltas (P17)
   was best on middlegame MAE but lost to round 1 (-70.4 +/- 35.6).

## Smokes (200 games each, 10+0.1, conc 12; >5% time forfeits = void)
p13t-r1 +1.7+/-38.8 (0 TF) | p13m-r1 VOID (16 TF, tuner load); rerun +43.7+/-34.8 (1); seed 777 -5.2+/-37.6 (0) | p13m-p0m +77.7+/-36.8 (0)
p17m-r1 -70.4+/-35.6 (0) | p17m-p13m -36.6+/-38.3 (0) | p13x-r1 +72.3/+31.4/+83.2 (0/0/0) | p13x-p13m +65.0+/-37.4 (0)
p13x-p0x +57.9+/-39.2 (0) | p0x-r1 +20.9+/-40.7 (1)

## Files
phase.py (probe/build; block-PCG ridge; per-component per-sign writer), tune.py, exact_pc.py, compare.py, pool.py, bounds.py,
rewrite_r1.py, smoke.sh, chain_*.sh; out/*_report.json, out/*_exact.json, out/compare.json, out/probe*/probe.json, out/tune*.json.
