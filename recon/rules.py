import os

RULES = {}
HAS_YAML = False

try:
    import yaml
    HAS_YAML = True
except ImportError:
    pass

def load_rules():
    global HAS_YAML
    if not HAS_YAML:
        return
    path = os.path.expanduser("~/.recon/rules.yaml")
    if os.path.exists(path):
        with open(path) as f:
            RULES.update(yaml.safe_load(f) or {})

def rule(key, default="", **kwargs):
    parts = key.split(".")
    val = RULES
    for p in parts:
        if isinstance(val, dict):
            val = val.get(p, "")
        else:
            text = default
            break
    else:
        text = val if isinstance(val, str) else default
    if kwargs and text:
        try:
            text = text.format(**kwargs)
        except KeyError:
            pass
    return text
