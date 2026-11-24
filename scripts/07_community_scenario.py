import sys; sys.path.insert(0, "src")
import pandas as pd, numpy as np
from gfr import config, scenario as S, recovery as R, viz
from gfr.config import p
cfg = config.load(); tab = pd.read_csv(p(*cfg["fragility_table"].split("/")))
mixes = {"urban_core": None, **{k: v for k, v in cfg["scenario"].get("mix_scenarios", {}).items()}}
rows, loss_rows = [], []
dc = cfg["decision"]; lr = dc["loss_ratio"]; rcfg = cfg["recovery"]
for mname, mix in mixes.items():
    inv = S.build_inventory(cfg, tab, mix=mix); inv.to_csv(p("data","processed",f"ward_inventory_{mname}.csv"), index=False)
    print(mname, len(inv), "buildings,", int(inv.hh.sum()), "households;", inv.bclass.value_counts(normalize=True).round(2).to_dict())
    res = {}
    for sname, pga in cfg["hazard"]["scenarios_g"].items():
        dg0, U, Z = S.simulate_damage(inv, tab, pga, cfg, seed=1)
        dg1, _, _ = S.simulate_damage(inv, tab, pga, cfg, retrofit=True, U=U, Z=Z)
        d = {}
        for lab, dg in [("base", dg0), ("retro", dg1)]:
            days, cur, T = R.run_recovery(dg, inv, rcfg, seed=7)
            m = R.metrics(days, cur, inv.hh.sum(), cfg["scenario"]["hh_size"])
            m.update(mix=mname, scenario=sname, pga_g=pga, case=lab, DG1=(dg == 1).sum(1).mean(), DG2=(dg == 2).sum(1).mean(), DG3=(dg == 3).sum(1).mean())
            rep = ((dg == 2)*lr["DG2"] + (dg == 3)*lr["DG3"] + (dg == 1)*lr["DG1"])@inv.replacement_cost.values
            disp = (np.minimum(T, rcfg["horizon_days"])/30*inv.hh.values*dc["rent_npr_per_hh_month"]).sum(1)
            m.update(repair_loss_M_NPR=rep.mean()/1e6, displacement_cost_M_NPR=disp.mean()/1e6, total_loss_M_NPR=(rep+disp).mean()/1e6,
                     total_loss_p95_M_NPR=np.percentile(rep+disp, 95)/1e6)
            rows.append(m); d[lab] = cur
            if mname == "urban_core" and lab == "base" and sname == "design_475yr":
                viz.ward_map(inv, dg[0], f"Study ward ({len(inv):,} OSM buildings) - one realisation at PGA={pga} g", "07_ward_damage_map_475yr.png")
        res[f"{sname} (PGA {pga} g)"] = d
        # paired benefit for this scenario
    viz.recovery(days, res, f"08_recovery_{mname}.png")
out = pd.DataFrame(rows); out.round(2).to_csv(p("results","tables","scenario_results.csv"), index=False)
pd.set_option("display.width", 250); print(out[["mix","scenario","case","DG2","DG3","displaced_persons_day0_mean","t50_days_median","t90_days_median","resilience_loss_pct_mean","total_loss_M_NPR"]].round(1).to_string())
