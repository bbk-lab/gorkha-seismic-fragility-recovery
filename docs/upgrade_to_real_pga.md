# Upgrading from anchored (latent) intensity to the real USGS ShakeMap

**Goal:** replace the two assumed numbers (`im_ref_pga_g = 0.20`, `sigma_ln_im_regions = 0.40`) by real ground motion, so that the fragility medians are in "real g".

**Why the subset cannot do this:** the DrivenData subset hides which district each `geo_level_1_id` is, so a ShakeMap value cannot be attached to it. The full survey keeps `district_id` (and `vdcmun_id`, `ward_id`), so you need that file.

| Step | What | Command / action |
|---|---|---|
| 1 | Get the ShakeMap grid | `python scripts/fetch_external_data.py` -> `data/external/shakemap_grid.xml` (manual fallback below) |
| 2 | Get the full survey | download `csv_building_structure.csv` (Open Data Nepal / NPC portal, or the Nepal NSO microdata catalogue). Check the terms of use. |
| 3 | Convert it | `python scripts/10_build_full_survey_table.py --structure path/to/csv_building_structure.csv` |
| 4 | District polygons | a file with one polygon per district and a column holding the SAME integer `district_id` used in the survey (see "Making the district file") |
| 5 | ShakeMap -> one PGA per district | `python scripts/09_shakemap_to_region_pga.py --polygons districts.geojson --id-col district_id` -> `data/external/region_pga.csv` |
| 6 | Check: does damage-inferred intensity agree with ShakeMap? | `python scripts/11_compare_latent_vs_shakemap.py` |
| 7 | Fit with real PGA | `python scripts/03_empirical_fragility.py --data data/processed/gorkha_clean_full.csv.gz --suffix _full` |
| 8 | Use the new curves downstream | set `fragility_table: results/tables/empirical_fragility_params_full.csv` in `config/params.yaml`, then run scripts 06, 07, 08 |

## Manual ShakeMap fallback
Open `https://earthquake.usgs.gov/earthquakes/eventpage/us20002926/shakemap/intensity`, go to the Downloads tab, save `grid.xml` as `data/external/shakemap_grid.xml`.

## Making the district file
Any polygon file works (GeoJSON, shapefile, GeoPackage). Typical route: download Nepal admin level 2 (districts) from GADM or geoBoundaries, open it in QGIS or geopandas, and add an integer column `district_id` that matches the survey's numbers. The portal ships a name-mapping file for its IDs; join on district names and check the spelling differences by eye (e.g. Kavrepalanchok / Kavrepalanchowk). Without polygons you can supply one lat/lon point per district via `--centroids` (CSV columns `geo_level_1_id,lat,lon`); that is cruder.

## What you will see, and what it means
- The ShakeMap grid has PGA in %g; the script converts to g and uses the geometric mean (mean of ln PGA) per district.
- Step 6 gives a Spearman correlation between damage-inferred and ShakeMap district PGA. A high value supports the latent model. A low value is also informative: ShakeMap is a smooth model constrained by few records, and Hough et al. argue that PGA is a poor intensity measure for this earthquake (long-period energy) - so fragility versus PGA will be noisy.
- Expect larger dispersions (beta) and less tidy curves in step 7 than with the latent fit. That is a real result, not a bug: district-average PGA cannot resolve site effects inside a district. Report both.
- With real PGA fixed, the anchor settings are no longer used.

## Status of these scripts
`09`, `10` and `11` were tested only on synthetic stand-in files that mimic the formats (they run end to end). They have not been run against the real USGS grid or the real portal file; `10` assumes the portal's column names and stops with a clear message if one differs.
