import sys; sys.path.insert(0, "src")
import argparse, pandas as pd, numpy as np
from gfr import config, fragility as F, viz
from gfr.config import p
ap = argparse.ArgumentParser(description="Empirical fragility fit")
ap.add_argument("--data", default="data/processed/gorkha_clean.csv.gz", help="cleaned building table")
ap.add_argument("--suffix", default="", help="added to output names, e.g. _full")
ap.add_argument("--no-external", action="store_true", help="ignore data/external/region_pga.csv (latent mode)")
a = ap.parse_args(); SUF = a.suffix; viz.SUFFIX = SUF
cfg = config.load(); df = pd.read_csv(p(*a.data.split("/")))
r = F.fit_all(df, cfg, bootstrap=True, use_external=not a.no_external)
tab = r["table"]; tab.round(4).to_csv(p("results","tables",f"empirical_fragility_params{SUF}.csv"), index=False)
r["regions"].round(4).to_csv(p("results","tables",f"inferred_region_pga{SUF}.csv"), index=False)
m = F.weighted_fit_metrics(r["cells"]); pd.Series(m).to_csv(p("results","tables",f"fragility_fit_metrics{SUF}.csv"))
print(tab.round(3).to_string()); print(m)
lg = F.logistic_fragility(r["df"], r["regions"]); lg.round(4).to_csv(p("results","tables",f"logistic_fragility{SUF}.csv"), index=False)
orr = F.logit_odds_ratios(r["df"]); orr.round(4).to_csv(p("results","tables",f"logit_odds_ratios{SUF}.csv"), index=False)
print(orr[orr.outcome == "DG>=2"].round(2).to_string())
viz.fragility_curves(tab, r["boots"]); viz.calibration(r["cells"]); viz.regions(r["regions"])
