"""Run the whole pipeline in order.   python scripts/run_all.py [--skip-ml] [--skip-matlab]"""
import subprocess, sys, shutil, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
def run(*a): print("\n>>>", " ".join(a)); subprocess.run(a, cwd=ROOT, check=True)
py = sys.executable
run(py, "scripts/01_extract_osm.py")
run(py, "scripts/make_synthetic_records.py")
run(py, "scripts/02_clean_explore.py")
run(py, "scripts/03_empirical_fragility.py")
run(py, "scripts/03b_anchor_sensitivity.py")
if "--skip-ml" not in sys.argv: run(py, "scripts/04_ml_model.py")
if "--skip-matlab" not in sys.argv:
    if shutil.which("matlab") or shutil.which("octave-cli"): run("bash", "scripts/run_matlab.sh")
    else: print("!! MATLAB/Octave not found - using the shipped results/matlab/*.csv")
run(py, "scripts/06_validation.py")
run(py, "scripts/07_community_scenario.py")
run(py, "scripts/08_decision_support.py")
print("\nAll done. Figures: results/figures   Tables: results/tables")
