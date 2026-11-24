"""Retrofit benefit-cost analysis (scenario and annualised)."""
import numpy as np, pandas as pd
from .scenario import frag_probs

def hazard_curve(cfg, a):
    h = cfg["hazard"]; Z = h["Z_pokhara_g"]*cfg["scenario"]["site_factor"]
    return (1.0/h["return_period_anchor"])*(np.asarray(a)/Z)**(-h["slope_k"])

def expected_loss_curve(inv, frag, cfg, a_grid, retrofit, mult=None, dur=(0, 300, 700)):
    """Expected loss per PGA level [NPR]: repair/reconstruction + displacement cost (analytical expectation).
    dur = mean displacement duration [days] for (DG1, DG2, DG3)."""
    dc = cfg["decision"]; lr = dc["loss_ratio"]; rc = dc["retrofit"]
    out = []
    for a in a_grid:
        P2, P3 = frag_probs(inv, frag, a*cfg["scenario"]["site_factor"], rc["target_classes"] if retrofit else (),
                            mult or rc["median_multiplier"], rc["beta_multiplier"])
        p1, p2, p3 = 1-P2, P2-P3, P3
        rep = (p1*lr["DG1"] + p2*lr["DG2"] + p3*lr["DG3"])*inv.replacement_cost.values
        disp = (p2*dur[1] + p3*dur[2])/30.0*inv.hh.values*dc["rent_npr_per_hh_month"]
        out.append((rep + disp).sum())
    return np.array(out)

def eal(loss_curve, a_grid, cfg):
    lam = hazard_curve(cfg, a_grid)
    # annual rate of occurrence in each PGA bin (hazard is decreasing in a); trapezoid on loss
    dl = -np.diff(lam); lm = 0.5*(loss_curve[1:] + loss_curve[:-1])
    return float((dl*lm).sum() + loss_curve[-1]*lam[-1])

def annuity(r, n):
    return (1-(1+r)**(-n))/r

def bcr_table(inv, frag, cfg, a_grid, mults=None, rates=None, dur=(0, 300, 700)):
    dc = cfg["decision"]; rc = dc["retrofit"]; mults = mults or rc["sensitivity_multipliers"]; rates = rates or dc["discount_rates"]
    tgt = inv.bclass.isin(rc["target_classes"])
    cost = rc["cost_fraction_of_replacement"]*inv.replacement_cost[tgt].sum()
    base = eal(expected_loss_curve(inv, frag, cfg, a_grid, False, dur=dur), a_grid, cfg)
    rows = []
    for m in mults:
        ret = eal(expected_loss_curve(inv, frag, cfg, a_grid, True, mult=m, dur=dur), a_grid, cfg)
        for r in rates:
            pv = (base-ret)*annuity(r, dc["horizon_years"])
            rows.append(dict(median_multiplier=m, discount_rate=r, EAL_base=base, EAL_retrofit=ret, EAL_avoided=base-ret,
                             PV_benefit=pv, retrofit_cost=cost, BCR=pv/cost, NPV=pv-cost,
                             breakeven_cost_fraction=pv/inv.replacement_cost[tgt].sum()))
    return pd.DataFrame(rows), cost
