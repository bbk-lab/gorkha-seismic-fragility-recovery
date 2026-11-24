# Limitations and things to replace
1. **Ground motion anchor** - absolute empirical PGA medians depend on `im_ref_pga_g` / `sigma_ln_im_regions` (assumptions). Class ratios do not.
2. **Pure RC DG3 curves** are extrapolations (flagged). Survey intensities (about 0.1-0.46 g after anchoring) rarely produce DG3 in RC.
3. **Only 3 damage grades**, no "undamaged" class (all surveyed buildings were in the affected area) -> DG1 repair cost is set to zero.
4. **Survey bias** - damage was assessed after the event by engineers/volunteers; sampling was not random.
5. **Class mix, floors, households per building, replacement and retrofit costs, loss ratios, rents, recovery delays, crew numbers, retrofit capacity gain, hazard slope** are placeholders in `config/params.yaml`. Replace with Census 2011/2021, a local walk-through survey and your own BoQ rates.
6. **OSM footprints are a 2016 snapshot** and the study tile is not an official ward polygon.
7. **MATLAB frame model**: bare frame, no infill, no pinching, no P-delta, synthetic records, SDOF-IDA instead of MDOF-IDA, NE/E designs are generic. The analytical output was produced in GNU Octave 8.4; MATLAB should run the same code but I have not been able to test that.
8. **Hazard curve** is a one-parameter power law anchored at the NBC zone factor, not a PSHA result. EAL values (1.5-2.4 % of value per year here) are high and should be read as illustrative of the assumed hazard + survey-calibrated fragility.
9. Licence of the DrivenData subset not verified - check before redistributing.
