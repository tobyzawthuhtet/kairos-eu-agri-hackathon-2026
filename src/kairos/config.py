"""Load YAML configs (crops, regions) from the repo's configs/ directory."""
import os
from pathlib import Path

import yaml

CONFIG_DIR = Path(os.environ.get("KAIROS_CONFIG_DIR", Path(__file__).resolve().parents[2] / "configs"))


def load_crop(name: str) -> dict:
    with open(CONFIG_DIR / "crops" / f"{name}.yaml") as f:
        return yaml.safe_load(f)


def load_regions() -> list[dict]:
    with open(CONFIG_DIR / "regions.yaml") as f:
        return yaml.safe_load(f)["regions"]
