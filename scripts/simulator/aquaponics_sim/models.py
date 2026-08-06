"""
Sensor models — produce realistic telemetry values.

Each model is a plain object with a ``.read(elapsed_s)`` (or ``.read(now)``)
method that returns a float (or bool).  Faults are injected by calling
the model's ``fault_*`` methods.
"""

from __future__ import annotations

import math
import random
from datetime import datetime, timezone


# ── helpers ───────────────────────────────────────────────────────────

def _hour_of(now: datetime) -> float:
    """Return fractional hour (0–24) from a datetime."""
    return now.hour + now.minute / 60.0 + now.second / 3600.0


def _diurnal(hour: float, peak_hour: float) -> float:
    """Normalised diurnal factor in [0, 1]; peaks at *peak_hour*."""
    phase = 2 * math.pi * (hour - peak_hour) / 24.0
    return (math.sin(phase) + 1.0) / 2.0          # 0 at trough, 1 at peak


# ── water temperature ─────────────────────────────────────────────────

class WaterTempModel:
    """Diurnal sine wave around *base* ± *amplitude*."""

    def __init__(self, base: float = 28.0, amplitude: float = 3.0,
                 peak_hour: float = 14.0):
        self.base = base
        self.amplitude = amplitude
        self.peak_hour = peak_hour
        self._offset = 0.0          # fault: high_temp

    def read(self, now: datetime) -> float:
        h = _hour_of(now)
        val = self.base + self.amplitude * math.sin(
            2 * math.pi * (h - self.peak_hour) / 24.0
        )
        val += self._offset
        val += random.gauss(0, 0.15)        # sensor noise
        return round(val, 2)

    def fault_high_temp(self, delta: float = 5.0):
        """Inject a temperature offset (e.g. heatwave)."""
        self._offset = delta


# ── pH ────────────────────────────────────────────────────────────────

class PhModel:
    """Slow bounded random walk."""

    def __init__(self, initial: float = 7.6, lo: float = 6.5, hi: float = 8.5):
        self.value = initial
        self.lo = lo
        self.hi = hi
        self._drift = 0.0          # fault: sensor_drift

    def read(self, _now: datetime | None = None) -> float:
        self.value += random.gauss(0, 0.02) + self._drift
        self.value = max(self.lo, min(self.hi, self.value))
        return round(self.value, 2)

    def fault_drift(self, rate: float = 0.05):
        """Inject a persistent pH drift."""
        self._drift = rate


# ── nitrogen cycle (ammonia → nitrite → nitrate) ──────────────────────

class NitrogenCycle:
    """
    Models the aquarium nitrogen cycle:

        Day 0-3   — ammonia spike (from fish waste / ammonification)
        Day 3-10  — nitrite rises as Nitrosomonas colonise
        Day 7-14  — nitrate rises as Nitrobacter colonise
        Day 14+   — ammonia & nitrite → 0, nitrate stable

    The curve is compressed to *cycle_duration* seconds for demo.
    """

    def __init__(self, cycle_duration: float = 1800.0):
        self.duration = cycle_duration
        self._started = False
        self._start_elapsed: float = 0.0

    def start(self, elapsed_s: float):
        """Begin the cycle at *elapsed_s* (usually 0)."""
        self._started = True
        self._start_elapsed = elapsed_s

    def read(self, elapsed_s: float) -> tuple[float, float, float]:
        """Return (ammonia, nitrite, nitrate) in mg/L."""
        if not self._started:
            return 0.0, 0.0, 5.0

        t = (elapsed_s - self._start_elapsed) / self.duration   # 0 → 1+
        if t < 0:
            t = 0.0

        # Ammonia: sharp rise, slow decay (gaussian-ish)
        ammonia = 5.0 * t * math.exp(-3.0 * t)

        # Nitrite: delayed rise, peak ~40%, then decay
        nitrite = 0.0
        if t > 0.05:
            nt = t - 0.05
            nitrite = 3.0 * nt * math.exp(-2.5 * nt) * 8.0
            nitrite = min(nitrite, 3.0)

        # Nitrate: monotonic rise, plateau
        nitrate = 5.0 + 80.0 * (1.0 - math.exp(-2.0 * t))

        # noise + clamp
        ammonia = max(0.0, ammonia + random.gauss(0, 0.03))
        nitrite = max(0.0, nitrite + random.gauss(0, 0.08))
        nitrate = max(0.0, nitrate + random.gauss(0, 0.3))

        return round(ammonia, 2), round(nitrite, 2), round(nitrate, 2)


# ── pump (220 V AC side) ──────────────────────────────────────────────

class PumpModel:
    """
    Pump metrics measured on the 220 V AC side (via SSR / current sensor).

    Per ADR-0004 the main water pump is on mains power, not the 12 V DC
    domain.  ``pump_current`` reflects AC-side draw; ``flow`` is L/min.
    """

    def __init__(self, nominal_current: float = 0.52, nominal_flow: float = 8.0):
        self.nominal_current = nominal_current
        self.nominal_flow = nominal_flow
        self._failed = False
        self._blocked = False

    def read(self) -> tuple[float, float]:
        """Return (current_A, flow_L_per_min)."""
        if self._failed:
            return self.fault_fail()
        if self._blocked:
            return self.fault_block()

        c = self.nominal_current + random.gauss(0, 0.01)
        f = self.nominal_flow + random.gauss(0, 0.1)
        return round(c, 3), round(f, 2)

    def fault_fail(self) -> tuple[float, float]:
        """Pump stopped: zero current, zero flow."""
        return 0.0, 0.0

    def fault_block(self) -> tuple[float, float]:
        """Pump blocked: high current, zero flow."""
        c = self.nominal_current * 1.8 + random.gauss(0, 0.02)
        return round(c, 3), 0.0

    def set_failed(self, v: bool = True):
        self._failed = v

    def set_blocked(self, v: bool = True):
        self._blocked = v


# ── power (12 V DC domain — solar + battery) ──────────────────────────

class PowerModel:
    """
    12 V DC control-domain power: battery voltage + solar charge current.

    Per ADR-0004 the solar panel + battery only powers the control system
    (ESP32, sensors, small actuators).  The main pump is on 220 V AC.
    """

    def __init__(self, battery_base: float = 12.8,
                 battery_amplitude: float = 0.4,
                 solar_peak_current: float = 1.5,
                 solar_peak_hour: float = 12.0):
        self.battery_base = battery_base
        self.battery_amplitude = battery_amplitude
        self.solar_peak_current = solar_peak_current
        self.solar_peak_hour = solar_peak_hour

    def read_battery(self, now: datetime) -> float:
        """Battery voltage — rises during solar hours, dips at night."""
        h = _hour_of(now)
        # Charging during day → battery rises; night → slowly drops
        charging = _diurnal(h, self.solar_peak_hour)
        val = self.battery_base + self.battery_amplitude * (charging - 0.3)
        val += random.gauss(0, 0.02)
        return round(val, 2)

    def read_solar_current(self, now: datetime) -> float:
        """Solar panel output current (A) — zero at night."""
        h = _hour_of(now)
        val = self.solar_peak_current * _diurnal(h, self.solar_peak_hour) ** 2
        val += random.gauss(0, 0.01)
        return round(max(0.0, val), 3)


# ── low water (boolean) ───────────────────────────────────────────────

class LowWaterModel:
    """Normally False; can be fault-injected to True."""

    def __init__(self):
        self._forced = False

    def read(self) -> bool:
        return self._forced

    def fault_trigger(self):
        self._forced = True

    def clear(self):
        self._forced = False


# ── node model bundle ─────────────────────────────────────────────────

class NodeModels:
    """Bundles all sensor models for a single node."""

    def __init__(self, node_cfg: dict):
        self.node_id: str = node_cfg["id"]
        self.water_temp = WaterTempModel(
            base=node_cfg["water_temp_base"],
            amplitude=node_cfg["water_temp_amplitude"],
            peak_hour=node_cfg["water_temp_peak_hour"],
        )
        self.ph = PhModel(
            initial=node_cfg["ph_initial"],
            lo=node_cfg["ph_min"],
            hi=node_cfg["ph_max"],
        )
        self.nitrogen = NitrogenCycle(
            cycle_duration=node_cfg["nitrogen_cycle_duration"],
        )
        self.pump = PumpModel(
            nominal_current=node_cfg["pump_nominal_current"],
            nominal_flow=node_cfg["pump_nominal_flow"],
        )
        self.power = PowerModel(
            battery_base=node_cfg["battery_base"],
            battery_amplitude=node_cfg["battery_amplitude"],
            solar_peak_current=node_cfg["solar_peak_current"],
            solar_peak_hour=node_cfg.get("solar_peak_hour", 12),
        )
        self.low_water = LowWaterModel()

    def apply_fault(self, fault: dict):
        """Apply a fault injection spec."""
        kind = fault.get("type", "")
        target = fault.get("target", self.node_id)

        if target != self.node_id:
            return

        if kind == "pump_fail":
            self.pump.set_failed(True)
        elif kind == "pump_block":
            self.pump.set_blocked(True)
        elif kind == "high_temp":
            self.water_temp.fault_high_temp(fault.get("delta", 5.0))
        elif kind == "low_water":
            self.low_water.fault_trigger()
        elif kind == "sensor_drift":
            self.ph.fault_drift(fault.get("rate", 0.05))
