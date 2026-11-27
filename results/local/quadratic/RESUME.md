# quadratic resume state (rewrite on every change)
Task: rank-R pair-product (quadratic) eval via ALS exact solves -> exact writer -> held-out R2/MAE -> exactness check -> 200-game smoke vs closedform/out/pairs.nnue.
Rules: no gradient training; exact linear solves only; Mac + Colab T4 (colabp, session 'quad') only; timeout every command; write only in wspnet/quadratic.
Done:
- prep.py -> data/cds.npz, data/gpu.npz (on Colab /content/gpu.npz, md5 c55961a7...).
- qwriter.py + check.py: random 2500/2500, wide 2500/2500, planted faults fire.
- build.py full pipeline; out/gtest8 (R=8 factors from a 200k GPU test): test R2 0.7975, MAE 408.4, MAE cp 134.4; check PASS 2500/2500 (out/gtest8_check.json).
- c1 (full data, tol 2e-5) too slow (35 min per half-step at R=32): killed after 1 U step (c1_R32_U1 on Colab).
Running:
- Colab chain2.sh: factors on 600k subsample, tol 1e-4, maxit 1200: R32 -> R96 -> R192 -> R320 (c-step off from R96 on). colab/status.sh shows the trail.
- Mac: build q32a from out/c2_R32_snap1.npz (logs/build_q32a.log); smoke gtest8 vs pairs (logs/smoke_gtest8.log, smoke/gtest8_vs_pairs/).
Next: c2 train-val gap is large (0.869 vs 0.784 at R32) -> try lam_factor 1e5/3e5 at R32 warm-started; build best R; check; smoke best vs pairs.
