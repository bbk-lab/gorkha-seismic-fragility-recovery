# MATLAB part
Run `run_analytical_fragility.m` (MATLAB R2019b+ or GNU Octave 8+). No toolboxes required.
Outputs go to `../results/matlab/`: `analytical_fragility.csv`, `capacity_<case>.csv`, `ida_<case>.csv`.

| File | Role |
|---|---|
| `frame_config.m` | geometry, materials, reinforcement of the NE / E designs (edit to match your ETABS model) |
| `section_mphi.m` | fibre moment-curvature (Mander) |
| `build_frame.m` | 2D hinge-model frame |
| `pushover_frame.m` | displacement-controlled pushover |
| `idealize_sdof.m` | equivalent SDOF, EPP idealisation |
| `ida_sdof.m` | vectorised IDA |
| `bilin.m` | 1D elasto-plastic kinematic-hardening law |
| `plot_analytical_results.m` | makes the four PNG figures from the CSV results (`results/matlab/figures/`) |
| `load_records.m` | loads `records/synthetic_gm_set.csv` plus any `records/real/*.txt` (two columns: t[s], a[g]) |

A full run takes a few minutes in Octave (most of it in the 9 section analyses per case).
To add real records (e.g. KATNP 2015 from CESMD or PEER NGA) save them as two-column text in `records/real/`.
