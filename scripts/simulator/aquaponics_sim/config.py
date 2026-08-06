"""
Configuration loader — reads YAML config and provides sensible defaults.
"""

from __future__ import annotations

import copy
from pathlib import Path

import yaml

# ── defaults ──────────────────────────────────────────────────────────

_DEFAULT_BROKER = {
    "host": "localhost",
    "port": 1883,
    "username": None,
    "password": None,
}

_DEFAULT_SIM = {
    "interval": 5,          # seconds between publishes
    "random_seed": None,    # None = system entropy; int = reproducible
    "time_scale": 1.0,      # >1 speeds up nitrogen cycle for demo
}

_DEFAULT_NODE = {
    "id": "tank01",
    "water_temp_base": 28.0,     # °C
    "water_temp_amplitude": 3.0,  # diurnal swing ±
    "water_temp_peak_hour": 14,   # hottest at 2 PM
    "ph_initial": 7.6,
    "ph_min": 6.5,
    "ph_max": 8.5,
    "nitrogen_cycle_duration": 1800,  # seconds (compressed for demo)
    "pump_nominal_current": 0.52,     # A (220V AC side via SSR sensor)
    "pump_nominal_flow": 8.0,         # L/min
    "battery_base": 12.8,            # V (12V DC domain)
    "battery_amplitude": 0.4,
    "solar_peak_current": 1.5,       # A
    "solar_peak_hour": 12,
    # ── New sensors (Task B) ──────────────────────────────────────
    "ec_base": 1.2,                  # mS/cm at 25°C (nutrient baseline)
    "tds_factor": 0.5,               # EC→TDS conversion factor
    "turbidity_baseline": 3.0,       # NTU
    "turbidity_drift_rate": 0.002,   # NTU/s particulate accumulation
    "light_peak_lux": 45000.0,       # lux at solar noon
    "air_temp_base": 30.0,           # °C (Guangzhou balcony)
    "air_temp_amplitude": 6.0,       # diurnal swing ±
    "air_temp_peak_hour": 13,        # peaks 1h before water
    "air_humidity_base": 65.0,       # %RH
    "air_humidity_amplitude": 20.0,  # diurnal swing ±
    "air_pressure_base": 1010.0,     # hPa (near sea level)
}

_DEFAULT_FAULTS: list[dict] = []

_DEFAULT_CONFIG = {
    "broker": _DEFAULT_BROKER,
    "sim": _DEFAULT_SIM,
    "nodes": [copy.deepcopy(_DEFAULT_NODE)],
    "faults": _DEFAULT_FAULTS,
}


def load_config(path: str | Path | None = None) -> dict:
    """Load config from YAML file, or return defaults if *path* is None."""
    if path is None:
        return copy.deepcopy(_DEFAULT_CONFIG)

    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        user = yaml.safe_load(f) or {}

    cfg = copy.deepcopy(_DEFAULT_CONFIG)

    # shallow-merge top-level keys
    for key in ("broker", "sim"):
        if key in user:
            cfg[key].update(user[key])

    if "nodes" in user:
        merged = []
        for n in user["nodes"]:
            node = copy.deepcopy(_DEFAULT_NODE)
            node.update(n)
            merged.append(node)
        cfg["nodes"] = merged

    if "faults" in user:
        cfg["faults"] = user["faults"]

    return cfg
