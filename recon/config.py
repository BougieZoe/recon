import os

CONFIG = {}

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

def load_config():
    if not HAS_YAML:
        return
    path = os.path.expanduser("~/.recon/config.yaml")
    if os.path.exists(path):
        with open(path) as f:
            CONFIG.update(yaml.safe_load(f) or {})

def get_api(key):
    return CONFIG.get("api", {}).get(key, "")

def get_config(key, default=None):
    parts = key.split(".")
    val = CONFIG
    for p in parts:
        if isinstance(val, dict):
            val = val.get(p, {})
        else:
            return default
    return val if val else default
