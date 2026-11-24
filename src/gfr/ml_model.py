"""Gradient-boosting damage-grade model (scikit-learn) + feature importance."""
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score, cohen_kappa_score, confusion_matrix
from sklearn.inspection import permutation_importance

CAT = ["land_surface_condition","foundation_type","roof_type","ground_floor_type","other_floor_type",
       "position","plan_configuration","legal_ownership_status"]

def feature_sets(df):
    sup = [c for c in df.columns if c.startswith("has_superstructure_")]
    sec = [c for c in df.columns if c.startswith("has_secondary_use")]
    struct = ["floors","age_c","age_unknown","area_percentage","height_percentage","count_families"] + sup + sec + CAT
    return struct, struct + ["geo_level_1_id", "geo_level_2_id", "geo_level_3_id"]

def _prep(df, cols):
    X = df[cols].copy()
    for c in CAT:
        if c in X: X[c] = X[c].astype("category")
    return X

def run(df, cfg, seed=0):
    mcfg = cfg["ml"]; struct, full = feature_sets(df)
    y = df.damage_grade.values
    tr, te = train_test_split(df.index, test_size=mcfg["test_size"], stratify=y, random_state=seed)
    out = {}
    for name, cols in [("structure_only", struct), ("structure_plus_location", full)]:
        X = _prep(df, cols)
        cats = [c for c in cols if c in CAT]
        m = HistGradientBoostingClassifier(max_iter=200, learning_rate=0.12, max_leaf_nodes=48,
                                           l2_regularization=1.0, categorical_features=cats or None,
                                           early_stopping=True, validation_fraction=0.1, random_state=seed)
        m.fit(X.loc[tr], y[tr]); pr = m.predict(X.loc[te])
        res = dict(model=m, cols=cols, X=X, pred=pr,
                   micro_f1=f1_score(y[te], pr, average="micro"), macro_f1=f1_score(y[te], pr, average="macro"),
                   qwk=cohen_kappa_score(y[te], pr, weights="quadratic"),
                   cm=confusion_matrix(y[te], pr, labels=[1,2,3]), n_iter=m.n_iter_)
        rs = np.random.RandomState(seed); idx = rs.choice(te, size=min(mcfg["perm_sample"], len(te)), replace=False)
        pi = permutation_importance(m, X.loc[idx], y[idx], n_repeats=mcfg["perm_repeats"], random_state=seed,
                                    scoring="accuracy", n_jobs=1)
        res["importance"] = pd.DataFrame({"feature": cols, "mean_drop": pi.importances_mean,
                                          "std": pi.importances_std}).sort_values("mean_drop", ascending=False)
        out[name] = res
    out["te_index"] = te
    base = (pd.Series(y[te]).value_counts(normalize=True).max())
    out["majority_baseline"] = float(base)
    return out

def group_importance(imp):
    """Roll feature importances into engineering-meaningful groups."""
    def grp(f):
        if f.startswith("geo_level"): return "location (geo IDs)"
        if f.startswith("has_superstructure"): return "superstructure material"
        if f.startswith("has_secondary_use") or f in ("count_families",): return "use / occupancy"
        if f in ("floors","height_percentage","area_percentage"): return "geometry (floors, height, plan area)"
        if f in ("age_c","age_unknown"): return "age"
        if f in ("foundation_type","roof_type","ground_floor_type","other_floor_type"): return "foundation / floors / roof"
        return "site & plan (position, configuration, slope, ownership)"
    g = imp.assign(group=imp.feature.map(grp)).groupby("group").mean_drop.sum().sort_values(ascending=False)
    return g.reset_index()
