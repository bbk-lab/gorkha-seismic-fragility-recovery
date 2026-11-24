"""Empirical fragility curves from the Gorkha damage survey.

Model (ordered probit with latent regional shaking)
---------------------------------------------------
For building stratum s in survey region r:
    P(DG >= 2) = Phi( (x_r - ln m2_s) / beta_s )
    P(DG >= 3) = Phi( (x_r - ln m3_s) / beta_s ),   m3_s >= m2_s
x_r = ln(PGA_r). If observed regional PGA is supplied (data/external/region_pga.csv)
x_r is fixed; otherwise x_r is inferred jointly with the fragility parameters and
anchored to a mean / spread (config: fragility.im_ref_pga_g, sigma_ln_im_regions).
"""
import numpy as np, pandas as pd
from scipy.optimize import minimize
from scipy.special import ndtr, log_ndtr
from scipy.stats import norm
from .config import p

EPS = 1e-9

# ------------------------------------------------------------------ strata
def make_strata(df, min_n=1000):
    """Class x height strata: split <=2 / >=3 floors when both halves have >= min_n buildings."""
    s = df.bclass.copy()
    for c, g in df.groupby("bclass"):
        lo = (g.floors <= 2).sum(); hi = (g.floors >= 3).sum()
        if lo >= min_n and hi >= min_n:
            s.loc[g.index] = np.where(g.floors <= 2, f"{c}|1-2fl", f"{c}|3+fl")
        else:
            s.loc[g.index] = f"{c}|all"
    return s

def cell_counts(df, stratum_col="stratum"):
    t = (df.groupby(["geo_level_1_id", stratum_col, "damage_grade"]).size()
           .unstack(fill_value=0).reindex(columns=[1, 2, 3], fill_value=0))
    t.columns = ["n1", "n2", "n3"]
    return t.reset_index()

# ------------------------------------------------------------------ likelihood
def _unpack(theta, R, S, w, im_ref, sig, x_fixed):
    if x_fixed is None:
        zp = theta[:R]; k = R
        z = (zp - np.average(zp, weights=w)) / np.sqrt(np.average((zp - np.average(zp, weights=w))**2, weights=w))
        x = np.log(im_ref) + sig * z
    else:
        x = x_fixed; k = 0
    m2 = theta[k:k+S]; g = theta[k+S:k+2*S]; lb = theta[k+2*S:k+3*S]
    return x, m2, m2 + np.exp(g), np.exp(lb)

def _nll(theta, ri, si, n1, n2, n3, R, S, w, im_ref, sig, x_fixed):
    x, m2, m3, beta = _unpack(theta, R, S, w, im_ref, sig, x_fixed)
    xr = x[ri]; b = beta[si]
    P2 = ndtr((xr - m2[si]) / b); P3 = ndtr((xr - m3[si]) / b)
    p1 = np.clip(1 - P2, EPS, 1); p2 = np.clip(P2 - P3, EPS, 1); p3 = np.clip(P3, EPS, 1)
    ll = n1*np.log(p1) + n2*np.log(p2) + n3*np.log(p3)
    # informative-but-loose prior on ln(beta): lognormal building fragility dispersions are typically
    # 0.4-1.0, and the 0.1-0.46 g survey range cannot identify very flat curves (N(ln 0.7, 0.3)).
    pen = 0.5*np.sum(((np.log(beta) - np.log(0.7))/0.3)**2)
    return -ll.sum() + pen

def fit_latent(counts, regions, strata, cfg, x_fixed=None, theta0=None):
    R, S = len(regions), len(strata)
    ri = counts.geo_level_1_id.map({r: i for i, r in enumerate(regions)}).values
    si = counts.stratum.map({s: i for i, s in enumerate(strata)}).values
    n1, n2, n3 = counts.n1.values, counts.n2.values, counts.n3.values
    w = counts.groupby("geo_level_1_id")[["n1", "n2", "n3"]].sum().sum(axis=1).reindex(regions).values.astype(float)
    im_ref = cfg["fragility"]["im_ref_pga_g"]; sig = cfg["fragility"]["sigma_ln_im_regions"]
    if theta0 is None:
        # initialise region scores from region mean damage grade
        dmean = counts.assign(d=(counts.n1 + 2*counts.n2 + 3*counts.n3), n=counts[["n1","n2","n3"]].sum(axis=1)) \
                      .groupby("geo_level_1_id")[["d","n"]].sum()
        z0 = ((dmean.d/dmean.n).reindex(regions).values)
        th = ([] if x_fixed is not None else list(z0)) + [np.log(im_ref)]*S + [np.log(0.5)]*S + [np.log(0.6)]*S
        theta0 = np.array(th)
    args = (ri, si, n1, n2, n3, R, S, w, im_ref, sig, x_fixed)
    res = minimize(_nll, theta0, args=args, method="L-BFGS-B", options=dict(maxiter=3000, maxfun=400000))
    x, m2, m3, beta = _unpack(res.x, R, S, w, im_ref, sig, x_fixed)
    return dict(x=x, m2=m2, m3=m3, beta=beta, theta=res.x, nll=res.fun, success=res.success,
                ri=ri, si=si, regions=regions, strata=strata)

# ------------------------------------------------------------------ driver
def fit_all(df, cfg, bootstrap=True, seed=0, use_external=True):
    fcfg = cfg["fragility"]
    df = df.copy(); df["stratum"] = make_strata(df, fcfg["min_stratum_n"])
    cnt = cell_counts(df)
    cnt = cnt[cnt[["n1","n2","n3"]].sum(axis=1) >= fcfg["min_cell_n"]].reset_index(drop=True)
    regions = sorted(cnt.geo_level_1_id.unique())
    strata = sorted(cnt.stratum.unique())
    ext = p("data", "external", "region_pga.csv")
    x_fixed = None
    if ext.exists() and use_external:
        rp = pd.read_csv(ext).set_index("geo_level_1_id").pga_g
        x_fixed = np.log(rp.reindex(regions).values); print("Using observed regional PGA from", ext)
    fit = fit_latent(cnt, regions, strata, cfg, x_fixed)
    nobs = df.groupby("stratum").size().reindex(strata).values

    def table(f):
        return pd.DataFrame({"stratum": strata, "n_buildings": nobs,
                             "median_DG2plus_g": np.exp(f["m2"]), "median_DG3_g": np.exp(f["m3"]),
                             "beta": f["beta"]})
    tab = table(fit)
    gmax = float(np.exp(fit["x"]).max())
    tab["DG3_extrapolated"] = tab.median_DG3_g > 2*gmax     # median far beyond the survey's intensity range
    boots = []
    if bootstrap:
        rng = np.random.default_rng(seed)
        base_counts = cnt[["n1","n2","n3"]].values; ntot = base_counts.sum(axis=1)
        for b in range(fcfg["n_boot"]):
            bc = cnt.copy()
            # resample buildings within each cell (multinomial) -> refit with warm start
            samp = np.array([rng.multinomial(n, row / n) for n, row in zip(ntot, base_counts)])
            bc[["n1","n2","n3"]] = samp
            fb = fit_latent(bc, regions, strata, cfg, x_fixed, theta0=fit["theta"])
            boots.append(table(fb).assign(rep=b))
        bt = pd.concat(boots)
        for col in ["median_DG2plus_g", "median_DG3_g", "beta"]:
            q = bt.groupby("stratum")[col].quantile([0.05, 0.95]).unstack()
            tab[f"{col}_p05"] = tab.stratum.map(q[0.05]); tab[f"{col}_p95"] = tab.stratum.map(q[0.95])
    reg = pd.DataFrame({"geo_level_1_id": regions, "pga_g": np.exp(fit["x"]),
                        "n_buildings": cnt.groupby("geo_level_1_id")[["n1","n2","n3"]].sum().sum(axis=1).reindex(regions).values})
    cnt["P2_pred"] = ndtr((fit["x"][fit["ri"]] - fit["m2"][fit["si"]]) / fit["beta"][fit["si"]])
    cnt["P3_pred"] = ndtr((fit["x"][fit["ri"]] - fit["m3"][fit["si"]]) / fit["beta"][fit["si"]])
    n = cnt[["n1","n2","n3"]].sum(axis=1)
    cnt["P2_obs"] = (cnt.n2 + cnt.n3)/n; cnt["P3_obs"] = cnt.n3/n; cnt["n"] = n
    return dict(table=tab, regions=reg, cells=cnt, fit=fit, boots=pd.concat(boots) if boots else None, df=df)

def curve(median, beta, pga):
    return norm.cdf(np.log(np.asarray(pga)/median)/beta)

def weighted_fit_metrics(cells):
    out = {}
    for k in ["2", "3"]:
        o, pr, n = cells[f"P{k}_obs"], cells[f"P{k}_pred"], cells.n
        out[f"DG{k}_rmse"] = float(np.sqrt(np.average((o-pr)**2, weights=n)))
        out[f"DG{k}_r2"] = float(1 - np.sum(n*(o-pr)**2)/np.sum(n*(o-np.average(o, weights=n))**2))
    return out

# ------------------------------------------------------------------ logistic variant
def logistic_fragility(df, regions_tbl):
    """Per-stratum logistic regression of P(DG>=k) on ln(PGA_r) using the inferred regional PGA."""
    import statsmodels.api as sm
    m = df.merge(regions_tbl[["geo_level_1_id", "pga_g"]], on="geo_level_1_id")
    m["lnpga"] = np.log(m.pga_g); rows = []
    for s, g in m.groupby("stratum"):
        for k, col in [("DG2plus", "dg2plus"), ("DG3", "dg3")]:
            X = sm.add_constant(g[["lnpga"]]); r = sm.Logit(g[col], X).fit(disp=0)
            a, b = r.params["const"], r.params["lnpga"]
            rows.append(dict(stratum=s, ds=k, median_g=float(np.exp(-a/b)), slope=float(b),
                             beta_equiv=float(np.pi/(np.sqrt(3)*b)), n=len(g)))
    return pd.DataFrame(rows)

def logit_odds_ratios(df):
    """Building-level logit with region fixed effects -> odds ratios of class / floors / age."""
    import statsmodels.formula.api as smf
    d = df.copy(); d["age10"] = d.age_c.fillna(d.age_c.median())/10
    out = []
    for k, col in [("DG>=2", "dg2plus"), ("DG=3", "dg3")]:
        r = smf.logit(f"{col} ~ C(bclass, Treatment('CM_BRICK')) + floors + age10 + age_unknown "
                      f"+ area_percentage + height_percentage + C(geo_level_1_id)", d).fit(disp=0, maxiter=200)
        ci = r.conf_int()
        t = pd.DataFrame({"outcome": k, "term": r.params.index, "odds_ratio": np.exp(r.params.values),
                          "or_lo": np.exp(np.clip(ci[0].values, -20, 20)), "or_hi": np.exp(np.clip(ci[1].values, -20, 20)), "p": r.pvalues.values})
        out.append(t[~t.term.str.contains("geo_level_1_id|Intercept")])
    return pd.concat(out)
