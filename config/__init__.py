from pathlib import Path
import yaml
import os

CONFIG_DIR = Path(__file__).resolve().parent
MODEL_CONFIG_FILE = CONFIG_DIR / "model_config.yml"
SECRETS_FILE = CONFIG_DIR / "secrets.yml"

_config = None

def _load_yaml(path: Path):
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def get_config():
    global _config
    if _config is not None:
        return _config

    config = {}

    # Load model config
    config.update(_load_yaml(MODEL_CONFIG_FILE))

    # Load secrets (optional, local only)
    secrets = _load_yaml(SECRETS_FILE)
    if secrets:
        config.update(secrets)

    # Resolve env vars like ${VAR_NAME}
    for section in config.values():
        if isinstance(section, dict):
            for k, v in section.items():
                if isinstance(v, str) and v.startswith("${") and v.endswith("}"):
                    section[k] = os.getenv(v[2:-1])

    _config = config
    return config
