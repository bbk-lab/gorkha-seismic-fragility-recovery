import sys; sys.path.insert(0, "src")
import pandas as pd, numpy as np
from gfr import viz
from gfr import config
from gfr.config import p
cfg = config.load()
emp = pd.read_csv(p(*cfg["fragility_table"].split("/")))
mp = p("results","matlab","analytical_fragility.csv")
if not mp.exists(): sys.exit("Run the MATLAB step first (matlab/run_analytical_fragility.m or scripts/run_matlab.sh)")
ana = pd.read_csv(mp)
pairs = [("RC non-engineered, 3+ floors", ["RC_NE|3+fl"], ["RC_NE_3st", "RC_NE_4st"]),
         ("RC engineered, 3+ floors", ["RC_E|3+fl"], ["RC_E_3st", "RC_E_4st"])]
viz.validation(emp, ana, pairs)
rows = []
for ttl, es, cs in pairs:
    e = emp[emp.stratum == es[0]].iloc[0]
    for ds, ek in [("DS2_DG2plus", "median_DG2plus_g"), ("DS3_DG3", "median_DG3_g")]:
        a = ana[(ana.case.isin(cs)) & (ana.ds == ds)]
        rows.append(dict(class_=es[0], state="DG>=2 / DS2" if ds.startswith("DS2") else "DG3 / DS3",
                         empirical_median_g=e[ek], empirical_beta=e.beta, empirical_extrapolated=bool(e.DG3_extrapolated) if ds.startswith("DS3") else False,
                         analytical_median_g_min=a.median_pga_g.min(), analytical_median_g_max=a.median_pga_g.max(),
                         analytical_beta_total=a.beta_total.mean(), ratio_analytical_to_empirical=a.median_pga_g.mean()/e[ek]))
v = pd.DataFrame(rows); v.round(3).to_csv(p("results","tables","validation_analytical_vs_empirical.csv"), index=False); print(v.round(3).to_string())
# P(state) at the three hazard levels
from scipy.stats import norm
lv = {"0.15g": 0.15, "0.30g": 0.30, "0.58g": 0.58}; rr = []
for ttl, es, cs in pairs:
    e = emp[emp.stratum == es[0]].iloc[0]
    for ds, ek in [("DS2_DG2plus", "median_DG2plus_g"), ("DS3_DG3", "median_DG3_g")]:
        for nm, a in lv.items():
            pe = norm.cdf(np.log(a/e[ek])/e.beta)
            pa = np.mean([norm.cdf(np.log(a/r.median_pga_g)/r.beta_total) for _, r in ana[(ana.case.isin(cs)) & (ana.ds == ds)].iterrows()])
            rr.append(dict(class_=es[0], state=ds, pga=nm, P_empirical=pe, P_analytical=pa))
pd.DataFrame(rr).round(3).to_csv(p("results","tables","validation_probabilities_at_hazard_levels.csv"), index=False)
print(pd.DataFrame(rr).round(3).to_string())
