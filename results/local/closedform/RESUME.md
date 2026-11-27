# closedform resume state (rewrite on every change)
Task: ridge (closed-form/Krylov) linear eval -> writer nets: material, PSQT, +threats, +pairs; held-out R2/MAE; exactness check; 200-game smokes.
Compute: this Mac only. No training/optimiser.
Done: games/gen.pgn (10000, 5000 unique), games/gen2.pgn (12000); labels depth 10 data/{ka,gen,gen2}_labels.tsv; data/ds.npz (build_data.py).
  Probes on ds1 (840k): phase eg best per slot (none .7385 / eg .7411 / egop .7420 val R2 psqt lam 300); groups help (+.003-.006).
Done: solve.py -> out/{material,psqt,threats,pairs}.nnue, out/report.json (test R2 .636/.763/.771/.776); exact.py PASS all 4 (out/*_exact.json); ref.py out/ref_same_sample.json (default net R2 .858).
Done: smokes (smoke/*/log.txt): pairs-threats +54.3+/-38.0, threats-psqt +190.9+/-36.6, psqt-material +334.1+/-67.6 Elo (200 g each).
TASK COMPLETE. Running: nothing.
Next: none for this stage. Was: smoke.sh (fastchess 200 games 10+0.1 c8) pairs-vs-threats, threats-vs-psqt, psqt-vs-material.
