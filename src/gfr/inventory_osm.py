"""Extract building footprints from the OpenStreetMap Pokhara extract (.pbf)."""
import numpy as np, pandas as pd, osmium
import shapely.wkb as wkb
from pyproj import Transformer
from .config import p

_TO_UTM = Transformer.from_crs(4326, 32644, always_xy=True)   # UTM 44N covers Pokhara

class _H(osmium.SimpleHandler):
    def __init__(self):
        super().__init__(); self.rows = []; self.wf = osmium.geom.WKBFactory()
    def area(self, a):
        t = a.tags
        if "building" not in t: return
        try:
            g = wkb.loads(self.wf.create_multipolygon(a), hex=True)
        except Exception:
            return
        c = g.centroid
        xs, ys = _TO_UTM.transform(*zip(*g.exterior.coords)) if g.geom_type == "Polygon" else (None, None)
        if xs is None:      # multipolygon: use largest part
            gg = max(g.geoms, key=lambda q: q.area); xs, ys = _TO_UTM.transform(*zip(*gg.exterior.coords))
        from shapely.geometry import Polygon
        area_m2 = Polygon(zip(xs, ys)).area
        self.rows.append(dict(osm_id=a.orig_id(), lon=c.x, lat=c.y, area_m2=area_m2,
                              building=t.get("building"), levels=t.get("building:levels"),
                              amenity=t.get("amenity"), name=t.get("name")))

def extract(pbf=None, out=None):
    pbf = pbf or p("data", "raw", "osm", "pokhara.osm.pbf")
    out = out or p("data", "processed", "osm_buildings.csv")
    h = _H(); h.apply_file(str(pbf), locations=True)
    df = pd.DataFrame(h.rows)
    df["levels"] = pd.to_numeric(df["levels"], errors="coerce")
    df.to_csv(out, index=False)
    return df

if __name__ == "__main__":
    d = extract(); print(len(d), d.area_m2.describe())
