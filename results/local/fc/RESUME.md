# fc lane resume state (rewrite on every change)
Task: keep round-1 linear accumulator (phase side/cross re-encoding r1re, 286 slots, rebuilt here as data/r1re.nnue, sha pinned);
program fc_0/fc_1 as fixed nonlinear features; solve fc_2 + biases by exact ridge (hierarchical global->band->stack, bounded
active-set exact solves for int8 range); exact check engine == simulator with planted faults; smoke 200 g vs closedform pairs.
No gradient training. Compute: this Mac only so far. Every command under timeout.
Done: prep.py (slot activations, known answer 219,934/219,934 test == r1re exact preds); probe.py/probe2.py (float headroom:
  per-stack hinges of E val .8173); exp.py designs E17 (val exact .8190) and E17G (val .8206, test .8220, MAE 354 vs 428);
  check.py E17G PASS (engine 3000/3000, scalar sim 400/400, faults a/b/c fire); smoke E17G vs r1pairs +52.5 +/- 34.8
  (200 g, 6 time forfeits = 3%, load ~40 from other lanes).
  probe3.py: finer partial sums of the same linear function (threat by attacker/attacked side, psq per plane, pairs) add
  float val R2 .8207 -> .8328.
Done: slots2.py: 58 extra FT slots (286..343) = partial sums of the same round-1 base weights (threat by side, psq per plane,
  pairs), read only by nonlinear rows. select.py greedy 30 fc_0 rows of 132 candidates (out/select_x.json, float val .8278);
  build X30 (exact val .8238 test .8250; int8 bounds cost ~.004) check PASS; smoke X30 vs r1 +59.6+/-36.0 but 26/200 time
  forfeits (load 68) -> VOID. fc1sel.py: 32 fc_1 product/max rows (out/fc1_x.json, float val .8320).
  build XF (30 fc_0 + 32 fc_1 rows, lam 1:1:3): exact val .8291, test .8303, MAE 344.7 (r1 428.4), MAE_cp 121.5 (r1 141.1);
  check XF PASS (engine 3000/3000, sim 400/400, faults a,b,c,d fire).
Running: smoke XF vs r1pairs (logs/smoke_XF.log).
Next: read smoke; if time forfeits > 5% rerun when load is lower.
