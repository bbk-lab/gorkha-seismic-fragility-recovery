"""Stochastic recovery (re-occupancy) model with a limited local workforce."""
import heapq, numpy as np

def recovery_times(dg, inv, rcfg, rng):
    """Return time-to-functionality [days] for every building in ONE realisation (dg: [n_bldg])."""
    nb = len(dg); T = np.zeros(nb)
    area = inv.floor_area_m2.values
    unsafe2 = rng.random(nb) < rcfg.get("dg2_displaced_fraction", 1.0)     # DG2 buildings tagged unsafe
    dmg = np.where((dg == 3) | ((dg == 2) & unsafe2))[0]
    if len(dmg) == 0: return T
    ready = (rng.lognormal(np.log(rcfg["assess_median_d"]), rcfg["assess_sigma"], len(dmg))
             + rng.lognormal(np.log(rcfg["finance_median_d"]), rcfg["finance_sigma"], len(dmg)))
    base = np.where(dg[dmg] == 3, rcfg["work_days"]["DG3"], rcfg["work_days"]["DG2"]).astype(float)
    work = base*(area[dmg]/150.0)**0.6*rng.lognormal(0, 0.35, len(dmg))
    n_crews = max(1, int(round(rcfg["crews_per_100_bldg"]*nb/100)))
    free = [0.0]*n_crews; heapq.heapify(free)
    extra = int(n_crews*(rcfg["outside_labor_factor"]-1))
    for _ in range(extra): heapq.heappush(free, float(rcfg["outside_labor_ramp_day"]))
    for i in np.argsort(ready):
        t0 = heapq.heappop(free); start = max(ready[i], t0); fin = start + work[i]
        heapq.heappush(free, fin); T[dmg[i]] = fin
    return T

def functionality_curve(T, hh, days):
    """Fraction of households housed at each day (occupied building = functional)."""
    order = np.argsort(T); cum = np.cumsum(hh[order]); Ts = T[order]
    idx = np.searchsorted(Ts, days, side="right")
    housed = np.where(idx > 0, cum[np.maximum(idx-1, 0)], 0)
    return housed/hh.sum()

def run_recovery(dg_mc, inv, rcfg, seed=0, step=15):
    rng = np.random.default_rng(seed)
    days = np.arange(0, rcfg["horizon_days"]+1, step); hh = inv.hh.values
    curves = np.zeros((dg_mc.shape[0], len(days))); Ts = np.zeros(dg_mc.shape)
    for i in range(dg_mc.shape[0]):
        T = recovery_times(dg_mc[i], inv, rcfg, rng); Ts[i] = T
        curves[i] = functionality_curve(T, hh, days)
    return days, curves, Ts

def metrics(days, curves, hh_total, hh_size):
    out = {}
    out["displaced_hh_day0_mean"] = float(((1-curves[:, 0])*hh_total).mean())
    out["displaced_persons_day0_mean"] = out["displaced_hh_day0_mean"]*hh_size
    out["resilience_loss_pct_mean"] = float(100*(1-curves).mean())            # mean % hh-time lost over horizon
    out["person_years_displaced_mean"] = float(((1-curves).sum(axis=1)*(days[1]-days[0])/365*hh_total*hh_size).mean())
    for q in (0.5, 0.9):
        t = [days[np.argmax(c >= q)] if (c >= q).any() else np.nan for c in curves]
        out[f"t{int(q*100)}_days_median"] = float(np.nanmedian(t))
    return out
