import sys; sys.path.insert(0, "src")
import pandas as pd, numpy as np
from gfr import config, scenario as S, recovery as R, decision as DEC, viz
from gfr.config import p
cfg = config.load(); tab = pd.read_csv(p(*cfg["fragility_table"].split("/")))
a = np.geomspace(0.05, 1.5, 60); out = []
mixes = {"urban_core": None, **cfg["scenario"].get("mix_scenarios", {})}
for mname, mix in mixes.items():
    inv = S.build_inventory(cfg, tab, mix=mix)
    # mean displacement duration by grade from the recovery model at the design-level scenario
    dg, _, _ = S.simulate_damage(inv, tab, cfg["hazard"]["scenarios_g"]["design_475yr"], cfg, n_mc=100, seed=3)
    _, _, T = R.run_recovery(dg, inv, cfg["recovery"], seed=11)
    d2 = T[dg == 2].mean() if (dg == 2).any() else 300; d3 = T[dg == 3].mean() if (dg == 3).any() else 700
    dur = (0, float(d2), float(d3)); print(mname, "mean displacement days DG2/DG3:", round(d2), round(d3))
    bt, cost = DEC.bcr_table(inv, tab, cfg, a, dur=dur); bt.insert(0, "mix", mname)
    tot = inv.replacement_cost.sum(); bt["EAL_base_pct_of_value"] = 100*bt.EAL_base/tot
    out.append(bt)
    curves = {"baseline": DEC.expected_loss_curve(inv, tab, cfg, a, False, dur=dur),
              f"retrofit x{cfg['decision']['retrofit']['median_multiplier']}": DEC.expected_loss_curve(inv, tab, cfg, a, True, dur=dur)}
    viz.decision(bt[bt.discount_rate == cfg["decision"]["discount_rates"][1]], curves, a, cfg, f"08_eal_curves_{mname}.png", f"09_bcr_sensitivity_{mname}.png", tag=mname)
    n_t = inv.bclass.isin(cfg["decision"]["retrofit"]["target_classes"]).sum()
    print(f"{mname}: {n_t} target buildings, retrofit cost {cost/1e6:,.0f} M NPR, EAL base {bt.EAL_base.iloc[0]/1e6:,.0f} M NPR ({bt.EAL_base_pct_of_value.iloc[0]:.2f}% of value)")
res = pd.concat(out); res.round(4).to_csv(p("results","tables","benefit_cost.csv"), index=False)
base = res[(res.median_multiplier == cfg["decision"]["retrofit"]["median_multiplier"])]
print(base[["mix","discount_rate","EAL_avoided","PV_benefit","retrofit_cost","BCR","NPV","breakeven_cost_fraction"]].round(3).to_string())
