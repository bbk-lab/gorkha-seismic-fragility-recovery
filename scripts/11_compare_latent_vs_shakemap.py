"""Does the damage-inferred ('latent') regional intensity agree with the real ShakeMap PGA?
Fits the latent model WITHOUT external PGA on the chosen table and compares to data/external/region_pga.csv.
    python scripts/11_compare_latent_vs_shakemap.py --data data/processed/gorkha_clean_full.csv.gz"""
import sys, argparse; sys.path.insert(0, "src")
import numpy as np, pandas as pd, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from scipy.stats import spearmanr, pearsonr
from gfr import config, fragility as F
from gfr.config import p
ap = argparse.ArgumentParser(); ap.add_argument("--data", default="data/processed/gorkha_clean_full.csv.gz"); a = ap.parse_args()
cfg = config.load(); df = pd.read_csv(p(*a.data.split("/")))
ext = pd.read_csv(p("data", "external", "region_pga.csv"))
r = F.fit_all(df, cfg, bootstrap=False, use_external=False)
m = r["regions"].merge(ext[["geo_level_1_id", "pga_g"]], on="geo_level_1_id", suffixes=("_latent", "_shakemap"))
rho = spearmanr(m.pga_g_latent, m.pga_g_shakemap); pr = pearsonr(np.log(m.pga_g_latent), np.log(m.pga_g_shakemap))
print(f"{len(m)} regions | Spearman rho = {rho.statistic:.2f} (p={rho.pvalue:.3g}) | Pearson r(ln PGA) = {pr.statistic:.2f}")
print(f"ShakeMap: mean {np.exp(np.log(m.pga_g_shakemap).mean()):.3f} g, sd(ln) {np.log(m.pga_g_shakemap).std():.2f}   "
      f"latent (anchored): mean {np.exp(np.log(m.pga_g_latent).mean()):.3f} g, sd(ln) {np.log(m.pga_g_latent).std():.2f}")
m.round(4).to_csv(p("results", "tables", "latent_vs_shakemap.csv"), index=False)
fig, ax = plt.subplots(figsize=(4.6, 4.2)); ax.scatter(m.pga_g_shakemap, m.pga_g_latent, s=np.clip(m.n_buildings/800, 10, 120), alpha=.75, color="#2171b5")
lim = [0.05, 1]; ax.plot(lim, lim, "k--", lw=.8); ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlabel("ShakeMap PGA, district mean [g]"); ax.set_ylabel("damage-inferred PGA [g]")
ax.set_title(f"Spearman rho = {rho.statistic:.2f}", fontsize=10); ax.grid(alpha=.25); fig.savefig(p("results", "figures", "10_latent_vs_shakemap_pga.png"), dpi=200, bbox_inches="tight")
