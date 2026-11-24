"""Download the data that could NOT be fetched while this project was generated (network-restricted sandbox).
Run on your own machine:   python scripts/fetch_external_data.py [--all]

1. USGS ShakeMap grid for the 2015 Gorkha mainshock (event us20002926)  -> data/external/shakemap_grid.xml
2. Fresh OpenStreetMap buildings for Pokhara via Overpass               -> data/external/pokhara_buildings_overpass.json
3. Instructions for the full NPC / Open Data Nepal damage survey (district-named, ~762k buildings)

Licences: USGS products are public domain; OSM data is (c) OpenStreetMap contributors, ODbL 1.0.
Please check the DrivenData / Open Data Nepal terms before redistributing the survey data."""
import sys, json, urllib.request, urllib.parse, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]; EXT = ROOT/"data"/"external"; EXT.mkdir(parents=True, exist_ok=True)

def get(url, dest, data=None):
    print("GET", url[:110]); req = urllib.request.Request(url, data=data, headers={"User-Agent": "gorkha-fragility-project/1.0"})
    with urllib.request.urlopen(req, timeout=180) as r: dest.write_bytes(r.read())
    print("  ->", dest, dest.stat().st_size, "bytes")

def shakemap():
    # 1) Ask the USGS ComCat API for the event detail, 2) follow the shakemap grid.xml product link
    det = json.load(urllib.request.urlopen("https://earthquake.usgs.gov/fdsnws/event/1/query?eventid=us20002926&format=geojson", timeout=60))
    prod = det["properties"]["products"]["shakemap"][0]["contents"]
    key = next(k for k in prod if k.endswith("grid.xml")); get(prod[key]["url"], EXT/"shakemap_grid.xml")

def overpass(south=28.20, west=83.96, north=28.25, east=84.02):
    q = f'[out:json][timeout:120];(way["building"]({south},{west},{north},{east}););out geom;'
    get("https://overpass-api.de/api/interpreter", EXT/"pokhara_buildings_overpass.json", data=urllib.parse.urlencode({"data": q}).encode())

if __name__ == "__main__":
    shakemap(); overpass()
    print("\nFull survey: https://eq2015.npc.gov.np (csv_building_structure.csv, csv_building_damage_assessment.csv, csv_building_ownership_and_use.csv)")
    print("or DrivenData competition page 'Richter's Predictor' for the labelled subset (already included in data/raw/gorkha).")
    print("Next: see docs/upgrade_to_real_pga.md to turn the ShakeMap into data/external/region_pga.csv")
