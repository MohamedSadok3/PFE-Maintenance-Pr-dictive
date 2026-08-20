"""Helpers for loading flat-layout microservices in one pytest process."""

import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).parent.parent
SERVICE_NAMES = ("alertes", "auth", "iot", "ml", "gateway")
AMBIGUOUS_PACKAGES = ("services", "models", "engines", "routes", "queries")


def activate_service(name: str) -> Path:
    """Select one flat-layout service and discard modules cached from another."""
    if name not in SERVICE_NAMES:
        raise ValueError(f"Unknown backend service: {name}")
    for module_name in list(sys.modules):
        if module_name in AMBIGUOUS_PACKAGES or module_name.startswith(
            tuple(f"{package}." for package in AMBIGUOUS_PACKAGES)
        ):
            sys.modules.pop(module_name, None)
    service_paths = {str(BACKEND_DIR / service) for service in SERVICE_NAMES}
    sys.path[:] = [path for path in sys.path if path not in service_paths]
    sys.path.insert(0, str(BACKEND_DIR / name))
    if str(BACKEND_DIR) not in sys.path:
        sys.path.insert(1, str(BACKEND_DIR))
    return BACKEND_DIR / name
