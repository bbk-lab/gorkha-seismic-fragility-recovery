"""Clean the Gorkha (Richter's Predictor) building-damage table and assign building classes."""
import numpy as np, pandas as pd
from .config import p

SUPER = ["adobe_mud","mud_mortar_stone","stone_flag","cement_mortar_stone","mud_mortar_brick",
         "cement_mortar_brick","timber","bamboo","rc_non_engineered","rc_engineered","other"]
CLASS_ORDER = ["MM_STONE","MM_BRICK","CM_STONE","CM_BRICK","RC_NE","RC_E","RC_MIX","TIM_OTH"]
MASONRY_FLAGS = ["adobe_mud","mud_mortar_stone","stone_flag","cement_mortar_stone","mud_mortar_brick","cement_mortar_brick"]

def assign_class(r):
    """Primary structural class. Pure RC frames are separated from RC+masonry hybrids because the
    survey shows the hybrids behave very differently (see notebook 01)."""
    rc_e, rc_ne = r.has_superstructure_rc_engineered, r.has_superstructure_rc_non_engineered
    has_mas = any(getattr(r, f"has_superstructure_{m}") for m in MASONRY_FLAGS)
    if (rc_e or rc_ne) and has_mas: return "RC_MIX"      # RC flagged together with masonry walls
    if rc_e: return "RC_E"                               # pure RC frame, engineered
    if rc_ne: return "RC_NE"                             # pure RC frame, non-engineered
    if r.has_superstructure_cement_mortar_brick: return "CM_BRICK"
    if r.has_superstructure_cement_mortar_stone: return "CM_STONE"
    if r.has_superstructure_mud_mortar_brick: return "MM_BRICK"
    if (r.has_superstructure_mud_mortar_stone or r.has_superstructure_adobe_mud
            or r.has_superstructure_stone_flag): return "MM_STONE"
    return "TIM_OTH"

def load_clean(save=True):
    v = pd.read_csv(p("data","raw","gorkha","train_values.csv"))
    l = pd.read_csv(p("data","raw","gorkha","train_labels.csv"))
    df = v.merge(l, on="building_id", validate="1:1")
    n0 = len(df)
    # --- cleaning -----------------------------------------------------------
    df["age_unknown"] = (df.age >= 995).astype(int)        # 995 = survey code for "unknown/very old"
    df.loc[df.age >= 995, "age"] = np.nan
    df["age_c"] = df.age.clip(upper=100)                    # long tail of implausible ages
    df["floors"] = df.count_floors_pre_eq.clip(upper=6)
    df["bclass"] = df.apply(assign_class, axis=1)
    df["n_materials"] = df[[f"has_superstructure_{s}" for s in SUPER]].sum(axis=1)
    df["dg2plus"] = (df.damage_grade >= 2).astype(int)
    df["dg3"] = (df.damage_grade == 3).astype(int)
    df["floor_band"] = pd.cut(df.floors, [0,2,4,99], labels=["1-2","3-4","5+"])
    assert df.building_id.is_unique
    if save:
        df.to_csv(p("data","processed","gorkha_clean.csv.gz"), index=False)
    return df

def summary(df):
    t = df.groupby("bclass").agg(n=("damage_grade","size"),
            dg1=("damage_grade", lambda s:(s==1).mean()),
            dg2=("damage_grade", lambda s:(s==2).mean()),
            dg3=("damage_grade", lambda s:(s==3).mean()),
            mean_floors=("floors","mean"), median_age=("age","median")).reindex(CLASS_ORDER)
    return t

if __name__ == "__main__":
    d = load_clean(); print(summary(d).round(3))
