"""Plot helpers (matplotlib). All figures are written to results/figures."""
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import norm
from .config import p

plt.rcParams.update({"figure.dpi": 130, "savefig.dpi": 200, "axes.grid": True, "grid.alpha": 0.25,
                     "axes.spines.top": False, "axes.spines.right": False, "font.size": 9})
PAL = {"MM_STONE":"#8c2d04","MM_BRICK":"#d94801","CM_STONE":"#6a51a3","CM_BRICK":"#2171b5",
       "RC_NE":"#238b45","RC_E":"#00441b","RC_MIX":"#74c476","TIM_OTH":"#737373"}
SUFFIX = ""      # e.g. "_full" so figures made from the full survey do not overwrite the subset ones
def _save(fig, name):
    path = p("results","figures",name.replace(".png", SUFFIX + ".png")); fig.savefig(path, bbox_inches="tight"); plt.close(fig); return path
def _cls(s): return s.split("|")[0]

def damage_by_class(df):
    t = df.groupby("bclass").damage_grade.value_counts(normalize=True).unstack().reindex(PAL.keys())
    n = df.groupby("bclass").size().reindex(PAL.keys())
    fig, ax = plt.subplots(figsize=(7, 3.6)); bottom = np.zeros(len(t))
    for g, c, lab in [(1,"#fee08b","DG1 low"),(2,"#fc8d59","DG2 medium"),(3,"#b30000","DG3 near-complete destruction")]:
        ax.bar(t.index, t[g], bottom=bottom, color=c, label=lab); bottom += t[g].values
    for i, (k, v) in enumerate(n.items()): ax.text(i, 1.01, f"n={v:,}", ha="center", fontsize=7)
    ax.set_ylabel("share of buildings"); ax.set_ylim(0, 1.08); ax.legend(ncol=3, fontsize=7, loc="lower center", bbox_to_anchor=(0.5, -0.32))
    ax.set_title("Gorkha 2015 survey: damage grade by structural class"); plt.xticks(rotation=30)
    return _save(fig, "01_damage_by_class.png")

def fragility_curves(tab, boots):
    a = np.linspace(0.01, 1.0, 200)
    groups = [("Mud-mortar masonry", ["MM_STONE","MM_BRICK"]), ("Cement-mortar masonry", ["CM_STONE","CM_BRICK"]),
              ("RC frames / hybrids / timber", ["RC_NE","RC_E","RC_MIX","TIM_OTH"])]
    fig, axs = plt.subplots(1, 3, figsize=(13, 3.9), sharey=True)
    for ax, (ttl, cl) in zip(axs, groups):
        for _, r in tab[tab.stratum.map(_cls).isin(cl)].iterrows():
            c = PAL[_cls(r.stratum)]; ls = "-" if "3+fl" in r.stratum else ("--" if "1-2fl" in r.stratum else "-")
            for key, lw, alpha, nm in [("median_DG2plus_g", 1.8, 1.0, "DG>=2"), ("median_DG3_g", 1.0, 0.7, "DG3")]:
                y = norm.cdf(np.log(a/r[key])/r.beta)
                ax.plot(a, y, color=c, ls=ls if nm == "DG>=2" else ":", lw=lw, alpha=alpha,
                        label=r.stratum if nm == "DG>=2" else None)
                if boots is not None and nm == "DG>=2":
                    b = boots[boots.stratum == r.stratum]
                    Y = norm.cdf(np.log(a[None]/b[key].values[:, None])/b.beta.values[:, None])
                    ax.fill_between(a, np.percentile(Y, 5, 0), np.percentile(Y, 95, 0), color=c, alpha=0.12, lw=0)
        ax.set_title(ttl); ax.set_xlabel("PGA [g]  (inferred regional intensity, anchored)"); ax.legend(fontsize=6.5, loc="lower right")
    axs[0].set_ylabel("P(damage >= state)"); fig.suptitle("Empirical fragility curves - solid: DG>=2, dotted: DG3; bands = 5-95% bootstrap", y=1.02, fontsize=10)
    return _save(fig, "02_empirical_fragility.png")

def calibration(cells):
    fig, axs = plt.subplots(1, 2, figsize=(8, 3.6))
    for ax, k, ttl in zip(axs, ["2","3"], ["DG>=2","DG3"]):
        c = cells.assign(cl=cells.stratum.map(_cls))
        for cl, g in c.groupby("cl"): ax.scatter(g[f"P{k}_pred"], g[f"P{k}_obs"], s=np.clip(g.n/60, 4, 90), color=PAL[cl], alpha=0.7, label=cl)
        ax.plot([0,1],[0,1],"k--",lw=0.8); ax.set_xlabel("predicted"); ax.set_ylabel("observed"); ax.set_title(f"{ttl}: region x stratum cells (size ~ n)")
    axs[0].legend(fontsize=6, ncol=2); return _save(fig, "03_fragility_calibration.png")

def regions(reg):
    r = reg.sort_values("pga_g"); fig, ax = plt.subplots(figsize=(7, 3.2))
    ax.bar(r.geo_level_1_id.astype(str), r.pga_g, color="#4292c6"); ax.set_xlabel("survey region (geo_level_1_id, anonymised)")
    ax.set_ylabel("inferred PGA [g]"); ax.set_title("Latent regional shaking inferred from damage (anchored to config mean/spread)")
    plt.xticks(rotation=90, fontsize=7); return _save(fig, "04_inferred_regional_pga.png")

def ml(res, group_imp):
    fig, axs = plt.subplots(1, 3, figsize=(14, 3.8))
    full = res["structure_plus_location"]; so = res["structure_only"]
    cm = full["cm"]/full["cm"].sum(1, keepdims=True)
    im = axs[0].imshow(cm, cmap="Blues", vmin=0, vmax=1)
    for i in range(3):
        for j in range(3): axs[0].text(j, i, f"{cm[i,j]:.2f}", ha="center", va="center", color="white" if cm[i,j] > .5 else "black")
    axs[0].set_xticks(range(3)); axs[0].set_xticklabels(["DG1","DG2","DG3"]); axs[0].set_yticks(range(3)); axs[0].set_yticklabels(["DG1","DG2","DG3"])
    axs[0].set_xlabel("predicted"); axs[0].set_ylabel("true"); axs[0].grid(False)
    axs[0].set_title(f"Hold-out recall (micro-F1 {full['micro_f1']:.3f}; structure-only {so['micro_f1']:.3f}; majority {res['majority_baseline']:.3f})", fontsize=8)
    t = full["importance"].head(12).iloc[::-1]; axs[1].barh(t.feature, t.mean_drop, xerr=t["std"], color="#6baed6"); axs[1].set_title("Permutation importance: top features (drop in accuracy)", fontsize=9)
    g = group_imp.iloc[::-1]; axs[2].barh(g.group.str.slice(0, 34), g.mean_drop, color="#fd8d3c"); axs[2].set_title("Importance by feature group", fontsize=9)
    fig.tight_layout(); return _save(fig, "05_ml_gradient_boosting.png")

def validation(emp, ana, pairs):
    a = np.linspace(0.02, 1.2, 240); fig, axs = plt.subplots(1, len(pairs), figsize=(5.2*len(pairs), 3.8), sharey=True)
    for ax, (title, estrata, acases) in zip(np.atleast_1d(axs), pairs):
        for s in estrata:
            r = emp[emp.stratum == s].iloc[0]
            ax.plot(a, norm.cdf(np.log(a/r.median_DG2plus_g)/r.beta), color="#d7301f", lw=2, label=f"empirical {s} DG>=2")
            ax.plot(a, norm.cdf(np.log(a/r.median_DG3_g)/r.beta), color="#d7301f", lw=1.2, ls=":", label=f"empirical {s} DG3")
        for k, cs in enumerate(acases):
            for ds, ls in [("DS2_DG2plus", "-"), ("DS3_DG3", ":")]:
                r = ana[(ana.case == cs) & (ana.ds == ds)].iloc[0]
                ax.plot(a, norm.cdf(np.log(a/r.median_pga_g)/r.beta_total), color=["#2171b5","#08306b"][k], ls=ls, lw=1.6 if ls == "-" else 1.1,
                        label=f"MATLAB {cs} {'DS2' if ds.startswith('DS2') else 'DS3'}")
        ax.set_title(title, fontsize=9); ax.set_xlabel("PGA [g]"); ax.legend(fontsize=6)
    np.atleast_1d(axs)[0].set_ylabel("P(damage >= state)"); return _save(fig, "06_validation_analytical_vs_empirical.png")

def ward_map(inv, dg, title, name):
    fig, ax = plt.subplots(figsize=(6.4, 6)); col = np.array(["#fee08b", "#fc8d59", "#b30000"])[dg-1]
    ax.scatter(inv.lon, inv.lat, c=col, s=np.clip(inv.area_m2/6, 3, 60), edgecolor="k", linewidth=0.15)
    ax.set_aspect(1/np.cos(np.radians(inv.lat.mean()))); ax.set_xlabel("lon"); ax.set_ylabel("lat"); ax.set_title(title, fontsize=9)
    from matplotlib.lines import Line2D
    ax.legend(handles=[Line2D([0],[0],marker="o",color="w",markerfacecolor=c,markeredgecolor="k",label=l) for c, l in zip(["#fee08b","#fc8d59","#b30000"], ["DG1","DG2","DG3"])], fontsize=7)
    return _save(fig, name)

def recovery(days, results, name):
    fig, axs = plt.subplots(1, len(results), figsize=(5*len(results), 3.6), sharey=True)
    for ax, (ttl, d) in zip(np.atleast_1d(axs), results.items()):
        for lab, c, col in [("baseline", "#b30000", d["base"]), ("masonry retrofit", "#2171b5", d["retro"])]:
            ax.plot(days/365, col.mean(0)*100, color=c, lw=2, label=lab)
            ax.fill_between(days/365, np.percentile(col, 5, 0)*100, np.percentile(col, 95, 0)*100, color=c, alpha=0.15, lw=0)
        ax.set_title(ttl, fontsize=9); ax.set_xlabel("years after the earthquake"); ax.set_ylim(0, 102); ax.legend(fontsize=7, loc="lower right")
    np.atleast_1d(axs)[0].set_ylabel("households housed [%]"); return _save(fig, name)

def decision(bt, loss_curves, a_grid, cfg, name_a="08_eal_curves.png", name_b="09_bcr_sensitivity.png", tag=""):
    from .decision import hazard_curve
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.6))
    for lab, y in loss_curves.items(): ax[0].plot(a_grid, y/1e6, label=lab)
    ax[0].set_xlabel("PGA [g]"); ax[0].set_ylabel("expected loss [million NPR]"); ax[0].legend(fontsize=7); ax[0].set_title("Expected loss vs shaking (ward)", fontsize=9)
    ax[1].loglog(a_grid, hazard_curve(cfg, a_grid), color="k"); ax[1].set_xlabel("PGA [g]"); ax[1].set_ylabel("annual exceedance rate")
    ax[1].set_title("Assumed hazard curve (anchored to NBC 105 Z at 475 yr)", fontsize=9); fig.suptitle(tag, fontsize=9, y=1.03); p1 = _save(fig, name_a)
    pv = bt.pivot_table(index="median_multiplier", columns="discount_rate", values="BCR")
    fig, ax = plt.subplots(figsize=(5, 3.4)); im = ax.imshow(pv.values, cmap="RdYlGn", vmin=0, vmax=max(2.0, pv.values.max()), aspect="auto"); ax.grid(False)
    ax.set_xticks(range(pv.shape[1])); ax.set_xticklabels([f"{c:.0%}" for c in pv.columns]); ax.set_yticks(range(pv.shape[0])); ax.set_yticklabels([f"x{m}" for m in pv.index])
    for i in range(pv.shape[0]):
        for j in range(pv.shape[1]): ax.text(j, i, f"{pv.values[i,j]:.2f}", ha="center", va="center", fontsize=8)
    ax.set_xlabel("discount rate"); ax.set_ylabel("retrofit capacity multiplier"); ax.set_title(f"BCR {tag} (placeholder costs!)", fontsize=9); fig.colorbar(im)
    return p1, _save(fig, name_b)
