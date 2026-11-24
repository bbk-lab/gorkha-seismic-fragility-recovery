# Results snapshot (generated with the shipped config)
All numbers conditional on the assumptions in `config/params.yaml` - see `docs/limitations.md`.

## Gorkha survey (260,601 buildings)
Class sizes and damage shares: `tables/damage_by_class.csv`. Pure RC buildings with masonry flags (RC_MIX) are damaged much more often than pure RC.

## Empirical fragility (PGA in g, anchored latent intensity 0.20 g mean, 0.40 ln-sd)
| Stratum | n | median DG>=2 | median DG3 | beta | note |
|---|---|---|---|---|---|
| MM_STONE 1-2 fl | 154,232 | 0.061 | 0.247 | 0.60 | |
| MM_STONE 3+ fl | 46,657 | 0.052 | 0.255 | 0.61 | |
| MM_BRICK 1-2 / 3+ fl | 6,860 / 8,543 | 0.076 / 0.075 | 0.294 / 0.306 | 0.57 / 0.46 | |
| CM_BRICK 1-2 / 3+ fl | 12,766 / 2,748 | 0.115 / 0.118 | 0.855 / 0.563 | 0.93 / 0.69 | |
| CM_STONE | 3,273 | 0.064 | 0.431 | 0.80 | |
| RC_NE 3+ fl | 1,397 | 0.230 | 0.877 | 0.71 | |
| RC_E 3+ fl | 1,121 | 0.329 | 1.235 | 0.92 | DG3 extrapolated |
| RC_NE 1-2 fl, RC_E 1-2 fl, RC_MIX | | | | 1.4-2.3 | DG3 medians meaningless (extrapolated) |
Fit to region x stratum cells (in-sample): R2 0.89 (DG>=2), 0.97 (DG3). Anchor sensitivity (`tables/anchor_sensitivity.csv`): MM_STONE 1-2 fl DG>=2 median ranges 0.034-0.123 g over the tested anchors.

## Gradient boosting (hold-out 20 %)
micro-F1 0.739 (structure + location), 0.618 (structure only), 0.569 (majority). Quadratic kappa 0.60 / 0.35. Grouped permutation importance: location 0.249, foundation/floors/roof 0.041, superstructure material 0.029, age 0.011, geometry 0.011.

## Analytical (MATLAB code run in Octave 8.4, synthetic records)
| Case | T1 [s] | Vmax/W | median DS2 [g] | median DS3 [g] | beta_total |
|---|---|---|---|---|---|
| RC_NE 3 st | 1.02 | 0.26 | 0.294 | 0.597 | 0.44 / 0.40 |
| RC_NE 4 st | 1.34 | 0.19 | 0.256 | 0.501 | 0.40 / 0.39 |
| RC_E 3 st | 0.87 | 0.39 | 0.413 | 0.913 | 0.46 / 0.41 |
| RC_E 4 st | 1.15 | 0.27 | 0.348 | 0.768 | 0.39 / 0.42 |
Periods are long because the models are cracked bare frames.

## Validation (3+ floor pure RC)
Analytical/empirical median ratio: 1.20 (NE, DS2), 1.16 (E, DS2), 0.63 (NE, DS3), 0.68 (E, DS3). P(DG>=2) at 0.15 g: empirical 27 % / 20 % (NE / E) vs analytical 8 % / 1 %. See notebook 04 for discussion.

## Pokhara study ward (OSM tile, 3,190 buildings, about 13,100 households; assumed class mix)
Mean over 300 Monte Carlo runs, baseline -> retrofit of mud-mortar masonry (median x1.6):
| Mix | Scenario | DG3 buildings | persons displaced at day 0 | median t90 [days] |
|---|---|---|---|---|
| urban core | 0.15 g | 211 -> 129 | 14,975 -> 13,700 | 690 -> 630 |
| urban core | 0.30 g (475 yr) | 720 -> 524 | 24,907 -> 23,492 | 1,080 -> 990 |
| urban core | 0.58 g (2475 yr) | 1,450 -> 1,307 | 34,715 -> 33,804 | 1,590 -> 1,530 |
| masonry-heavy | 0.30 g | 1,274 -> 770 | 27,271 -> 23,876 | 1,380 -> 1,110 |
Full table: `tables/scenario_results.csv`.

## Benefit-cost (30 y, placeholder costs)
| Mix | Targets | Retrofit cost [M NPR] | EAL base [% value] | BCR 5 / 8 / 12 % | break-even cost share (8 %) |
|---|---|---|---|---|---|
| urban core | 673 | 644 | 1.47 | 1.41 / 1.03 / 0.74 | 21 % |
| masonry-heavy | 1,748 | 1,631 | 2.44 | 1.51 / 1.11 / 0.79 | 22 % |
