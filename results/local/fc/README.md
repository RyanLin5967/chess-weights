# wspnet/fc: nonlinear fc layers programmed on the round-1 linear accumulator (no gradient training)

Labels/data: closedform/data/ds.npz (2.21M positions, DEFAULT net depth-10 search scores; same game split as round 1:
train 1,772,719 / val 219,877 / test 219,934). Metrics: R^2 and MAE on y (internal units, |y| clipped 3000) from the EXACT
integer engine output of the written net; MAE_cp after scale_evaluation + to_cp (round-1 solve.metrics definitions).

## Construction
- FT: round-1 closedform pairs weights re-encoded in 286 slots (phase lane side/cross layout; rebuilt here byte-identical,
  sha256 d9b0dc...; known answer: slot simulation == r1re exact predictions on 219,934/219,934 test positions) + 58 extra slots
  (slots2.py) holding PARTIAL sums of the same base weights (threats by attacker/attacked side, psq per piece plane, pawn pairs),
  read only by nonlinear rows. Row 30 (skip) = round-1 eval, unchanged.
- fc_0 rows 0..29: hand-written integer rows (scaled copies of the round-1 eval E with per-stack bias knots = ramps; signed partial
  sums), chosen greedily from 132 candidates by val R^2 (select.py; each candidate scored by exact ridge solves).
- fc_1 rows 0..31: hand-written products / maxima of fc_0 ClippedReLU outputs (31(a+b), 31(a-b), 31a), chosen greedily (fc1sel.py).
- fc_2 (128 inputs) + bias per raw stack (192 stored stacks): hierarchical exact ridge global -> band -> stack on y - E_r1, int8
  bounds enforced by an active-set of exact linear solves, round to int8, bias re-solved exactly (fcnet.py, build.py).

## Results (test split unless noted)
| net | fc_0 / fc_1 rows | test R^2 | MAE int | MAE cp | MAE cp (|label|<=300) | exact check | smoke vs closedform pairs.nnue (200 g, 10+0.1, c12) |
|---|---|---|---|---|---|---|---|
| round-1 pairs (r1re) | linear | 0.7762 | 428.4 | 141.1 | 100.2 | phase lane PASS | - |
| E17G | 25 / 0 | 0.8220 | 354.1 | 124.4 | 95.4 | PASS | +52.5 +/- 34.8 (6 time forfeits, valid) |
| X30 | 30 / 0 (+58 partial-sum slots) | 0.8250 | 350.9 | 123.3 | 94.7 | PASS | +59.6 +/- 36.0 VOID (26 forfeits, load 68) |
| XF | 30 / 32 | 0.8303 | 344.7 | 121.5 | 93.5 | PASS (fc_1 fault fires) | see below |
Default net static eval on the same sample: R^2 0.858 (closedform/out/ref_same_sample.json).
Exact checks (check.py): file params == saved params; writer.simulate on the FILE == vectorised prediction 400/400; engine ==
prediction 3000/3000 (375 per band); planted faults: prediction+1 -> exactly 1 mismatch; fc_2 weight +1 -> 374; fc_0 bias
+4096 -> 29; fc_1 bias +8 -> 298.
