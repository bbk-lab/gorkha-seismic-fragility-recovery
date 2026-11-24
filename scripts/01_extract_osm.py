import sys; sys.path.insert(0, "src")
from gfr.inventory_osm import extract
d = extract(); print(f"{len(d):,} OSM building polygons extracted")
