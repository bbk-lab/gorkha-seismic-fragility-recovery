import yaml
from . import ROOT

def load(path=None):
    path = path or ROOT / "config" / "params.yaml"
    with open(path) as f:
        return yaml.safe_load(f)

def p(*parts):
    """Resolve a path relative to the project root."""
    return ROOT.joinpath(*parts)
