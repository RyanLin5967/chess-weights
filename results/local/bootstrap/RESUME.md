# bootstrap resume state (rewrite on every change)
Task: closed-form net WITHOUT Stockfish's trained net. Labels only from our own WSP nets' depth-10 search.
Gen0 labeller = programmed/out/v3.nnue. Each gen: label fixed position set with EvalFile=<best WSP net>, ridge (round-1 pairs spec,
eg phase, groups) -> out/genK.nnue (template = v3.nnue, so the default-net FILE is never read), exact check, 200-game smoke vs previous gen.
Up to 4 gens; stop after two gens without a smoke gain. Compute: this Mac only, every command under timeout.
Positions: fresh own-net games (games/own.pgn: v3 vs v2 / v3 vs v1, nodes-limited) + round-1 positions taken from closedform/data/*_fens.tsv
(FEN files with NO labels). Round-1 default-net labels are read ONLY by diag (R^2 vs default labels), after each solve.
Done: scripts gen_games.sh build_feats.py label_bs.py solve_bs.py diag.py smoke.sh run_all.py chain.sh; full dry run of run_all.py on 3000
  positions in scratch (ROUNDS=2) passed incl. stop rule; fingerprint guard and default-net refusal both fire-checked.
Done: games/own_v3_v2.pgn (7000), own_v3_v1.pgn (7000 when finished).
Running: chain.sh (pid in logs/chain.pid) -> run_all.py, log logs/run_all.log, state logs/state.json. Re-entrant: rerun
  `nohup ./chain.sh > logs/run_all.log 2>&1 &` (skips steps whose outputs exist).
Next: read logs/state.json when run_all prints ALL DONE.
DECISION 2026-11-27 07:20: gen1 lambda grid over scale {0.3,1,3} gave val R2 .8769/.8772/.8746 (flat; scale 1 chosen). From gen2 on,
  solve_bs.py default --scales is "1" (round-1 lambdas unscaled) to save ~50 min per generation. gen1 itself used the full grid.
gen1 (labels: v3 depth 10): test R2 own .8762; vs default labels (diag) .7588; smoke vs v3 +63.2 +/- 42.0 -> BEST.
gen2 (labels: gen1): test R2 own .8863; diag .7715; smoke vs gen1 -45.4 +/- 35.3 -> no gain (miss 1). gen3 labels from gen2, smoke vs gen1.
gen3 (labels: gen2): test R2 own .8862; diag .7702; smoke vs gen1 -135.0 +/- 39.5 -> miss 2 -> STOP. BEST = gen1.
Extra: gen1 vs closedform pairs +153.4 (s4242) / +111.4 (s4343); v3 vs pairs -38.4 (reproduces round 1's -33.1); gen1 vs v3 s4343 +68.6.
Audit: out/evalfile_audit.json PASS (no default net), fire-checked. Results table: README.md.
TASK COMPLETE. Running: nothing.
