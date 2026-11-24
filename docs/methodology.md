# Methodology

## 1. Data
| Data | Source in this folder | Notes |
|---|---|---|
| Building damage survey | `data/raw/gorkha/train_values.csv`, `train_labels.csv` | DrivenData *Richter's Predictor* subset of the 2015 Nepal Earthquake Open Data Portal survey: 260,601 buildings, 3 damage grades. Region IDs anonymised, no ground motion, no district names. |
| Building footprints | `data/raw/osm/pokhara.osm.pbf` | OSM extract of the Pokhara area, 75,778 building polygons, 2016 snapshot (c) OpenStreetMap contributors, ODbL. |
| Ground motion | *not included* | USGS ShakeMap (event `us20002926`) could not be downloaded when this project was generated. `scripts/fetch_external_data.py` fetches it. |
| Seismic parameters | `config/params.yaml -> hazard` | NBC 105:2020 zone factor for Pokhara is an **assumption (0.30 g)** - verify. |
| Ground-motion records | `matlab/records/synthetic_gm_set.csv` | 30 synthetic Clough-Penzien records. Add real records to `matlab/records/real/`. |

## 2. Cleaning and classes (`src/gfr/data_prep.py`)
- `age = 995` -> NaN + `age_unknown` flag; age capped at 100 y; floors capped at 6.
- Primary structural class from the superstructure flags: `RC_E`, `RC_NE` (pure RC), `RC_MIX` (RC flag together with masonry flag), `CM_BRICK`, `CM_STONE`, `MM_BRICK`, `MM_STONE` (mud mortar / adobe / stone), `TIM_OTH`.
- Strata = class x height band (<=2 vs >=3 floors) when both halves have >= 1000 buildings.

## 3. Empirical fragility (`src/gfr/fragility.py`)
Ordered probit with latent regional intensity:
`P(DG>=2) = Phi((x_r - ln m2_s)/beta_s)`, `P(DG=3) = Phi((x_r - ln m3_s)/beta_s)`, `m3_s >= m2_s`.
- `x_r = ln PGA_r` for the 31 anonymised survey regions is estimated jointly with the class medians and dispersions by maximum likelihood on region x stratum count cells (multinomial).
- Not identifiable from damage alone: the location and spread of `x_r`. These are fixed by `fragility.im_ref_pga_g` (0.20 g) and `fragility.sigma_ln_im_regions` (0.40). Class-to-class ratios and curve shapes come from the data; absolute medians scale with the anchor (`results/tables/anchor_sensitivity.csv`).
- A prior N(ln 0.7, 0.3) on ln beta regularises sparse strata. Several RC strata still want very flat curves; their DG3 medians lie far beyond the surveyed intensities and are flagged `DG3_extrapolated`.
- Bootstrap (60 reps) resamples buildings within cells: it reflects sampling noise only, not anchor or model uncertainty.
- Logistic variant (statsmodels `Logit` on inferred ln PGA) and building-level logit odds ratios with region fixed effects are in `results/tables`.
- If you obtain real regional PGA, put it in `data/external/region_pga.csv` (`geo_level_1_id,pga_g`) and the fit uses it instead of the latent values.

## 4. Machine learning (`src/gfr/ml_model.py`)
`HistGradientBoostingClassifier`, 80/20 stratified split. Two models: structure only, and structure + geo IDs. Metrics: micro-F1 (accuracy), macro-F1, quadratic weighted kappa. Permutation importance on 10,000 hold-out buildings, grouped by engineering meaning.

## 5. Analytical fragility (`matlab/`)
1. `section_mphi.m` - fibre moment-curvature (Mander confined/unconfined concrete, bilinear-hardening steel) of every column (by storey and exterior/interior axial load) and beam. Gives Mn, Mmax, effective yield curvature, ultimate curvature, effective EI.
2. `build_frame.m` - 2D three-bay frame, rigid diaphragms, elastic elements with rotational hinge springs (Ibarra-Krawinkler n = 10), hinge length by Paulay-Priestley.
3. `pushover_frame.m` - displacement-controlled Newton pushover with first-mode load pattern.
4. `idealize_sdof.m` - equivalent SDOF and equal-energy elastic-perfectly-plastic backbone. DS2 = effective yield, DS3 = first column hinge at rotation capacity (or 4 % MIDR).
5. `ida_sdof.m` - vectorised central-difference NLTHA of the SDOF over 30 records x 26 PGA levels (0.05-6 g).
6. Lognormal fit to the PGA that first exceeds each threshold; `beta_total = sqrt(beta_RTR^2 + 0.30^2)`.
Two designs: `NE` (350 mm columns, fc 15 MPa, 8 mm ties @150 mm, ineffective-confinement factor 0.4) and `E` (400 mm columns, fc 25 MPa, 10 mm ties @100 mm). Edit `frame_config.m` to match your own ETABS design.

## 6. Community scenario (`src/gfr/scenario.py`, `recovery.py`)
- Footprints inside the study tile, 15-2000 m2, minus sheds/huts. **Class and floors are randomly assigned from an assumed mix** (config), unless OSM carries `building:levels`.
- Damage: Monte Carlo (300 runs), shared lognormal event-level PGA uncertainty (sigma 0.25), paired random numbers between baseline and retrofit.
- Recovery: damaged buildings (all DG3, 50 % of DG2) wait for inspection + financing (lognormal delays), then queue for a limited number of crews (10 per 100 buildings, doubling after day 365); work duration scales with floor area. Output: households housed vs time, t50, t90, resilience loss.

## 7. Decision support (`src/gfr/decision.py`)
Retrofit raises the median capacity of target classes (default x1.6, an assumption - the survey contains no retrofitted buildings). Expected loss = repair (loss ratios DG1 0 / DG2 0.25 / DG3 1.0 of replacement cost) + displacement (rent x months). EAL integrates loss over a power-law hazard curve anchored at Z (475 yr), slope 2.5, PGA 0.05-1.5 g. BCR = PV of avoided EAL over 30 y / retrofit cost, for 5/8/12 % discount rates and capacity multipliers 1.3-2.0. `breakeven_cost_fraction` is the largest retrofit cost share for which BCR = 1.
