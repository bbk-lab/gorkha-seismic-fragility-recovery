"""Pokhara study-ward inventory and Monte-Carlo damage simulation."""
import numpy as np, pandas as pd
from scipy.special import ndtr
from .config import p

CLASSES = ["MM_STONE","MM_BRICK","CM_STONE","CM_BRICK","RC_NE","RC_E","RC_MIX","TIM_OTH"]

def build_inventory(cfg, frag_table, seed=None, mix=None):
    sc = cfg["scenario"]; b = sc["bbox"]; rng = np.random.default_rng(seed if seed is not None else cfg["seed"])
    d = pd.read_csv(p("data","processed","osm_buildings.csv"))
    d = d[(d.lat.between(b["lat_min"], b["lat_max"])) & (d.lon.between(b["lon_min"], b["lon_max"]))]
    d = d[d.area_m2.between(sc["min_footprint_m2"], sc["max_footprint_m2"])]
    d = d[~d.building.isin(["greenhouse","hut","farm_auxiliary","shed","garage","garages","roof","carport","ruins","construction","demolished"])].reset_index(drop=True)
    mix = mix or sc["class_mix"]; names = list(mix); pr = np.array([mix[k] for k in names]); pr = pr/pr.sum()
    d["bclass"] = rng.choice(names, size=len(d), p=pr)
    fl = np.zeros(len(d), int)
    for c in names:
        m = (d.bclass == c).values; fp = np.array(sc["floors_by_class"][c]); fp = fp/fp.sum()
        if m.sum() == 0: continue
        fl[m] = rng.choice([1,2,3,4,5], size=m.sum(), p=fp)
    d["floors"] = fl
    # OSM building:levels (when tagged) overrides the assumed floors
    lv = pd.to_numeric(d.levels, errors="coerce"); m = lv.notna() & (lv >= 1) & (lv <= 8)
    d.loc[m, "floors"] = lv[m].astype(int)
    strata = set(frag_table.stratum)
    def stratum(c, f):
        if f"{c}|1-2fl" in strata and f"{c}|3+fl" in strata: return f"{c}|1-2fl" if f <= 2 else f"{c}|3+fl"
        return f"{c}|all"
    d["stratum"] = [stratum(c, f) for c, f in zip(d.bclass, d.floors)]
    d["floor_area_m2"] = d.area_m2*d.floors
    d["hh"] = np.maximum(1, np.round(d.floor_area_m2/sc["floor_area_per_hh_m2"])).astype(int)
    cost = cfg["replacement_cost_npr_m2"]; d["replacement_cost"] = d.floor_area_m2*d.bclass.map(cost)
    return d

def frag_probs(inv, frag_table, pga, retrofit_classes=(), mult=1.0, beta_mult=1.0):
    """P(DG>=2), P(DG=3) per building at given PGA (array or scalar), with optional retrofit."""
    t = frag_table.set_index("stratum").loc[inv.stratum]
    m2 = t.median_DG2plus_g.values.copy(); m3 = t.median_DG3_g.values.copy(); be = t.beta.values.copy()
    rf = inv.bclass.isin(retrofit_classes).values
    m2[rf] *= mult; m3[rf] *= mult; be[rf] *= beta_mult
    pga = np.asarray(pga)
    x = np.log(pga[..., None] if pga.ndim else pga) 
    P2 = ndtr((x - np.log(m2))/be); P3 = ndtr((x - np.log(m3))/be)
    return P2, np.minimum(P3, P2)

def simulate_damage(inv, frag_table, pga, cfg, n_mc=None, retrofit=False, seed=0, U=None, Z=None):
    """Returns damage-grade array [n_mc, n_bldg]; common random numbers (U, Z) allow paired comparisons."""
    sc = cfg["scenario"]; n_mc = n_mc or sc["n_mc"]; nb = len(inv); rng = np.random.default_rng(seed)
    if U is None: U = rng.random((n_mc, nb))
    if Z is None: Z = rng.standard_normal(n_mc)
    im = pga*sc["site_factor"]*np.exp(sc["im_event_sigma"]*Z)          # shared event-level uncertainty
    rc = cfg["decision"]["retrofit"]
    P2, P3 = frag_probs(inv, frag_table, im, rc["target_classes"] if retrofit else (),
                        rc["median_multiplier"], rc["beta_multiplier"])
    dg = np.where(U < P3, 3, np.where(U < P2, 2, 1)).astype(np.int8)
    return dg, U, Z
