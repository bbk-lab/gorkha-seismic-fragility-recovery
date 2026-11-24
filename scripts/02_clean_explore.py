import sys; sys.path.insert(0, "src")
from gfr import data_prep as D, viz
from gfr.config import p
df = D.load_clean()
t = D.summary(df); t.round(4).to_csv(p("results","tables","damage_by_class.csv"))
print(t.round(3)); print("age unknown:", int(df.age_unknown.sum()), "| rows:", len(df))
viz.damage_by_class(df)
