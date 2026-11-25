"""Turn a USGS ShakeMap grid.xml into one PGA value per survey region (district).

Two ways to say where each region is:
  --polygons districts.geojson|.shp --id-col district_id    (best: mean ln-PGA of all grid cells inside the polygon)
  --centroids district_centroids.csv                        (columns: geo_level_1_id,lat,lon  - one point per region)

Output: data/external/region_pga.csv  (geo_level_1_id, pga_g, ...)   -> picked up automatically by step 03.

ShakeMap PGA is stored in %g in grid.xml; this script converts to g.
Why average ln(PGA)? Ground motion is roughly lognormal, so the geometric mean is the natural 'typical' value."""
import argparse, io, re, sys, pathlib
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).resolve().parents[1]

def read_grid(path):
    txt = pathlib.Path(path).read_text()
    # parse every <grid_field .../> tag attribute by attribute (units can be '%g', 'cm/s', ... so do not assume \w)
    fields = {}
    for tag in re.findall(r"<grid_field\b([^>]*)>", txt):
        at = dict(re.findall(r'(\w+)="([^"]*)"', tag))
        if "index" in at and "name" in at: fields[int(at["index"])] = (at["name"], at.get("units", ""))
    if not fields: sys.exit("No <grid_field> tags found - is this really a ShakeMap grid.xml?  First 300 chars:\n" + txt[:300])
    m = re.search(r"<grid_data>(.*?)</grid_data>", txt, re.S)
    if not m: sys.exit("No <grid_data> block found in the file.")
    arr = np.loadtxt(io.StringIO(m.group(1).strip()))
    cols = {fields[i][0].upper(): arr[:, i-1] for i in sorted(fields)}
    units = {fields[i][0].upper(): fields[i][1] for i in fields}
    if "PGA" not in cols: sys.exit(f"No PGA field. Fields found: {[(fields[i][0], fields[i][1]) for i in sorted(fields)]}")
    unit = units["PGA"]
    pga_g = cols["PGA"]/100.0 if ("%" in unit or unit.lower().startswith("pct")) else cols["PGA"]     # ShakeMap stores PGA in %g
    return pd.DataFrame({"lon": cols["LON"], "lat": cols["LAT"], "pga_g": pga_g, "mmi": cols.get("MMI", np.nan)}), unit

def by_polygon(grid, poly_path, id_col):
    import geopandas as gpd
    pts = gpd.GeoDataFrame(grid, geometry=gpd.points_from_xy(grid.lon, grid.lat), crs=4326)
    pol = gpd.read_file(poly_path).to_crs(4326)[[id_col, "geometry"]]
    j = gpd.sjoin(pts, pol, how="inner", predicate="within")
    j = j.assign(lnp=np.log(j.pga_g.clip(lower=1e-4))); g = j.groupby(id_col)
    out = pd.DataFrame({"pga_g": np.exp(g.lnp.mean()), "n_grid_points": g.size(), "pga_min_g": g.pga_g.min(),
                        "pga_max_g": g.pga_g.max(), "mmi_mean": g.mmi.mean()}).reset_index()
    out = out.rename(columns={id_col: "geo_level_1_id"})
    return out

def by_centroid(grid, cent_path):
    from scipy.interpolate import LinearNDInterpolator, NearestNDInterpolator
    c = pd.read_csv(cent_path); xy = grid[["lon", "lat"]].values; z = np.log(grid.pga_g.clip(lower=1e-4).values)
    lin = LinearNDInterpolator(xy, z); near = NearestNDInterpolator(xy, z)
    v = lin(c.lon.values, c.lat.values); v = np.where(np.isnan(v), near(c.lon.values, c.lat.values), v)
    return pd.DataFrame({"geo_level_1_id": c.geo_level_1_id, "pga_g": np.exp(v)})

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--grid", default=str(ROOT/"data"/"external"/"shakemap_grid.xml"))
    ap.add_argument("--polygons"); ap.add_argument("--id-col", default="district_id"); ap.add_argument("--centroids")
    ap.add_argument("--out", default=str(ROOT/"data"/"external"/"region_pga.csv")); a = ap.parse_args()
    grid, unit = read_grid(a.grid); print(f"ShakeMap grid: {len(grid):,} cells, PGA unit in file: {unit}, "
        f"PGA range {grid.pga_g.min():.3f}-{grid.pga_g.max():.3f} g")
    if a.polygons: out = by_polygon(grid, a.polygons, a.id_col)
    elif a.centroids: out = by_centroid(grid, a.centroids)
    else: sys.exit("give --polygons or --centroids")
    out.round(4).to_csv(a.out, index=False); print(out.round(3).to_string()); print("wrote", a.out)