"""
Compatibility wrapper for shared root config.
"""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

ROOT_CONFIG = Path(__file__).resolve().parents[1] / "config.py"

spec = spec_from_file_location("root_config", ROOT_CONFIG)
if spec is None or spec.loader is None:
    raise ImportError(f"Cannot load shared config module from {ROOT_CONFIG}")

root_config = module_from_spec(spec)
spec.loader.exec_module(root_config)

REGION = root_config.REGION
BASE_URL = root_config.BASE_URL
