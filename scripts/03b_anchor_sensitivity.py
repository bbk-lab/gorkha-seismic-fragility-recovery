"""How much do the absolute fragility medians depend on the ground-motion anchor assumptions?"""
import sys; sys.path.insert(0, "src")
import pandas as pd, itertools
from gfr import config, fragility as F
from gfr.config import p
cfg = config.load(); df = pd.read_csv(p("data","processed","gorkha_clean.csv.gz")); rows = []
for ref, sig in itertools.product([0.15, 0.20, 0.30], [0.30, 0.40, 0.50]):
    cfg["fragility"]["im_ref_pga_g"] = ref; cfg["fragility"]["sigma_ln_im_regions"] = sig
    t = F.fit_all(df, cfg, bootstrap=False)["table"]
    for s in ["MM_STONE|1-2fl", "CM_BRICK|1-2fl", "RC_NE|3+fl", "RC_E|3+fl"]:
        r = t[t.stratum == s].iloc[0]; rows.append(dict(im_ref_g=ref, sigma_ln=sig, stratum=s, median_DG2plus_g=r.median_DG2plus_g, median_DG3_g=r.median_DG3_g, beta=r.beta))
out = pd.DataFrame(rows).round(4); out.to_csv(p("results","tables","anchor_sensitivity.csv"), index=False)
print(out[out.stratum == "RC_NE|3+fl"].to_string())
