import sys; sys.path.insert(0, "src")
import pandas as pd
from gfr import config, ml_model as M, viz
from gfr.config import p
cfg = config.load(); df = pd.read_csv(p("data","processed","gorkha_clean.csv.gz"))
r = M.run(df, cfg)
rows = [dict(model=k, micro_f1=v["micro_f1"], macro_f1=v["macro_f1"], quadratic_kappa=v["qwk"], boosting_iterations=v["n_iter"]) for k, v in r.items() if isinstance(v, dict)]
rows.append(dict(model="majority_class_baseline", micro_f1=r["majority_baseline"]))
pd.DataFrame(rows).round(4).to_csv(p("results","tables","ml_performance.csv"), index=False)
for k in ["structure_only", "structure_plus_location"]:
    r[k]["importance"].round(5).to_csv(p("results","tables",f"ml_importance_{k}.csv"), index=False)
g = M.group_importance(r["structure_plus_location"]["importance"]); g.round(5).to_csv(p("results","tables","ml_importance_groups.csv"), index=False)
print(pd.DataFrame(rows).round(3)); print(g.round(4)); viz.ml(r, g)
