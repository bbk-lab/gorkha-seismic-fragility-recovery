"""Convert the FULL 2015 Nepal building survey (csv_building_structure.csv, ~762k buildings, district-named IDs)
into the same cleaned format the rest of the pipeline uses.

    python scripts/10_build_full_survey_table.py --structure path/to/csv_building_structure.csv

Output: data/processed/gorkha_clean_full.csv.gz   (geo_level_1_id = district_id, geo_level_2_id = vdcmun_id)

ASSUMPTIONS to verify against the portal's data dictionary:
  * damage grades 'Grade 1'..'Grade 5' -> 3 classes as DrivenData did:  1 -> 1,  2-3 -> 2,  4-5 -> 3
    (check: the printed shares should be close to the subset: 9.6 % / 56.9 % / 33.5 %)
  * column names as in csv_building_structure.csv. The script stops and lists the columns if one is missing."""
import argparse, sys, pathlib
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT/"src"))
from gfr.data_prep import assign_class

NEED = ["building_id","district_id","vdcmun_id","ward_id","count_floors_pre_eq","age_building","plinth_area_sq_ft","height_ft_pre_eq",
        "damage_grade","land_surface_condition","foundation_type","roof_type","ground_floor_type","other_floor_type","position","plan_configuration",
        "has_superstructure_adobe_mud","has_superstructure_mud_mortar_stone","has_superstructure_stone_flag","has_superstructure_cement_mortar_stone",
        "has_superstructure_mud_mortar_brick","has_superstructure_cement_mortar_brick","has_superstructure_timber","has_superstructure_bamboo",
        "has_superstructure_rc_non_engineered","has_superstructure_rc_engineered","has_superstructure_other"]

def main(a):
    df = pd.read_csv(a.structure, low_memory=False)
    miss = [c for c in NEED if c not in df.columns]
    if miss: sys.exit(f"Missing columns: {miss}\nColumns found: {list(df.columns)}\n-> adapt NEED / the renames in this script.")
    g = pd.to_numeric(df.damage_grade.astype(str).str.extract(r"(\d)")[0], errors="coerce")
    df = df.assign(g5=g).dropna(subset=["g5", "count_floors_pre_eq"])
    df["damage_grade"] = df.g5.map({1: 1, 2: 2, 3: 2, 4: 3, 5: 3}).astype(int)
    out = pd.DataFrame({"building_id": df.building_id, "geo_level_1_id": df.district_id.astype(int), "geo_level_2_id": df.vdcmun_id, "geo_level_3_id": df.ward_id,
                        "count_floors_pre_eq": df.count_floors_pre_eq.astype(int), "age": df.age_building, "damage_grade": df.damage_grade, "grade5": df.g5.astype(int)})
    for c in ["land_surface_condition","foundation_type","roof_type","ground_floor_type","other_floor_type","position","plan_configuration"] + [c for c in NEED if c.startswith("has_superstructure")]:
        out[c] = df[c].values
    out["area_percentage"] = (100*df.plinth_area_sq_ft/df.plinth_area_sq_ft.quantile(0.99)).clip(upper=100).round(1)    # approximate rescaling
    out["height_percentage"] = (100*df.height_ft_pre_eq/df.height_ft_pre_eq.quantile(0.99)).clip(upper=100).round(1)
    out["age_unknown"] = (out.age >= 995).astype(int); out.loc[out.age >= 995, "age"] = np.nan; out["age_c"] = out.age.clip(upper=100)
    out["floors"] = out.count_floors_pre_eq.clip(upper=6); out["count_families"] = 1
    out["bclass"] = out.apply(assign_class, axis=1)
    out["dg2plus"] = (out.damage_grade >= 2).astype(int); out["dg3"] = (out.damage_grade == 3).astype(int)
    out["floor_band"] = pd.cut(out.floors, [0, 2, 4, 99], labels=["1-2", "3-4", "5+"])
    path = ROOT/"data"/"processed"/"gorkha_clean_full.csv.gz"; out.to_csv(path, index=False)
    print(f"{len(out):,} buildings, {out.geo_level_1_id.nunique()} districts -> {path}")
    print("damage-grade shares (subset reference 0.096 / 0.569 / 0.335):", out.damage_grade.value_counts(normalize=True).sort_index().round(3).to_dict())
    print(out.bclass.value_counts().to_dict()); print("district ids:", sorted(out.geo_level_1_id.unique()))

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--structure", required=True); main(ap.parse_args())
