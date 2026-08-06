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


# ── EC / TDS (nutrient conductivity) ─────────────────────────────────

class EcTdsModel:
    """
    Electrical conductivity + TDS — correlates with nutrient (nitrate) level.

    EC is temperature-compensated to 25 °C (standard hydroponic convention).
    TDS is derived from EC via a conversion factor (0.5 / 0.7 typical).
    Fault: sensor_drift causes slow reading deviation.
    """

    def __init__(self, base_ec: float = 1.2, tds_factor: float = 0.5):
        self.base_ec = base_ec      # mS/cm at 25°C
        self.tds_factor = tds_factor
        self._drift = 0.0           # fault: sensor_drift

    def read(self, water_temp: float, nitrate: float) -> tuple[float, float]:
        """Return (ec_mS_cm, tds_ppm), compensated to 25°C."""
        # EC rises with nitrate (nutrient load)
        nutrient_effect = nitrate * 0.008     # ~0.8 mS per 100 mg/L nitrate
        ec = self.base_ec + nutrient_effect + self._drift
        # Temperature compensation (2%/°C from 25°C)
        ec_compensated = ec / (1.0 + 0.02 * (water_temp - 25.0))
        ec_compensated += random.gauss(0, 0.02)
        ec_compensated = max(0.0, ec_compensated)
        tds = ec_compensated * self.tds_factor * 1000   # ppm
        return round(ec_compensated, 3), round(tds, 1)

    def fault_drift(self, rate: float = 0.05):
        """Inject a persistent EC drift."""
        self._drift = rate


# ── turbidity ────────────────────────────────────────────────────────

class TurbidityModel:
    """
    Water turbidity in NTU — baseline drift + feeding spikes + noise.

    Turbidity slowly increases over time (particulate accumulation) and
    spikes briefly after feeding events.  Fault: dirty_sensor offsets
    the baseline upward.
    """

    def __init__(self, baseline: float = 3.0, drift_rate: float = 0.002):
        self.baseline = baseline
        self.drift_rate = drift_rate
        self._elapsed = 0.0
        self._spike = 0.0           # transient feeding spike
        self._dirty_offset = 0.0    # fault: dirty_sensor

    def read(self, dt: float) -> float:
        """Return turbidity (NTU). *dt* is seconds since last read."""
        self._elapsed += dt
        # Slow drift from particulate accumulation
        drift = self.drift_rate * self._elapsed
        # Spike decays exponentially
        self._spike *= 0.95
        val = self.baseline + drift + self._spike + self._dirty_offset
        val += random.gauss(0, 0.15)
        return round(max(0.0, val), 2)

    def trigger_feed_spike(self, magnitude: float = 8.0):
        """Simulate a turbidity spike from feeding."""
        self._spike += magnitude

    def fault_dirty(self, offset: float = 15.0):
        """Simulate a dirty/fouled sensor."""
        self._dirty_offset = offset


# ── light (lux) ──────────────────────────────────────────────────────

class LightModel:
    """
    Ambient light intensity (lux) from BH1750 sensor.

    Follows a diurnal curve: zero at night, peaks at solar noon.
    Cloud cover variation adds realistic noise.  Fault: sensor_fault
    forces an implausible reading.
    """

    def __init__(self, peak_lux: float = 45000.0, peak_hour: float = 12.0):
        self.peak_lux = peak_lux
        self.peak_hour = peak_hour
        self._fault = False

    def read(self, now: datetime) -> float:
        """Return light level (lux)."""
        if self._fault:
            return round(max(0.0, self.peak_lux * 0.01 + random.gauss(0, 5)), 1)

        h = _hour_of(now)
        factor = _diurnal(h, self.peak_hour)
        # Only daylight produces lux; use a sharper curve
        daylight = max(0.0, math.sin(math.pi * factor))
        # Random cloud cover (0 = clear, 1 = overcast)
        cloud = random.random() * 0.4
        val = self.peak_lux * daylight * (1.0 - cloud)
        val += random.gauss(0, 50)
        return round(max(0.0, val), 1)

    def fault_sensor(self):
        """Simulate a faulty (under-reading) sensor."""
        self._fault = True


# ── air temperature + humidity (AHT20) ───────────────────────────────

class AirTempHumidityModel:
    """
    Air temperature (°C) and relative humidity (%RH) from AHT20.

    Air temp leads water temp by ~1–2h and swings wider.
    Humidity is inversely correlated with temperature
    (warm air holds more moisture → lower RH at same absolute humidity).
    """

    def __init__(self, temp_base: float = 30.0, temp_amplitude: float = 6.0,
                 temp_peak_hour: float = 13.0,
                 humidity_base: float = 65.0, humidity_amplitude: float = 20.0):
        self.temp_base = temp_base
        self.temp_amplitude = temp_amplitude
        self.temp_peak_hour = temp_peak_hour
        self.humidity_base = humidity_base
        self.humidity_amplitude = humidity_amplitude

    def read(self, now: datetime) -> tuple[float, float]:
        """Return (air_temp_C, humidity_pct)."""
        h = _hour_of(now)
        # Air temp: sine wave, peaks ~1h before water temp
        temp = self.temp_base + self.temp_amplitude * math.sin(
            2 * math.pi * (h - self.temp_peak_hour) / 24.0
        )
        temp += random.gauss(0, 0.2)

        # Humidity: inverse sine — lowest at peak temp, highest at night
        humidity = self.humidity_base - self.humidity_amplitude * math.sin(
            2 * math.pi * (h - self.temp_peak_hour) / 24.0
        )
        humidity += random.gauss(0, 1.5)
        humidity = max(20.0, min(99.0, humidity))

        return round(temp, 2), round(humidity, 1)


# ── air pressure (BMP280) ────────────────────────────────────────────

class AirPressureModel:
    """
    Barometric pressure (hPa) from BMP280.

    Slow random walk around sea-level baseline with minor diurnal
    variation.  Guangzhou is near sea level → ~1010 hPa typical.
    """

    def __init__(self, baseline: float = 1010.0):
        self.baseline = baseline
        self._value = baseline

    def read(self, now: datetime) -> float:
        """Return pressure (hPa)."""
        h = _hour_of(now)
        # Semi-diurnal pressure tide (small ±1 hPa)
        diurnal = 1.0 * math.sin(2 * math.pi * h / 12.0)
        # Slow random walk
        self._value += random.gauss(0, 0.3)
        # Pull back toward baseline
        self._value += (self.baseline - self._value) * 0.01
        val = self._value + diurnal
        return round(val, 1)


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


# ── actuator state (simulated readback) ──────────────────────────────

class ActuatorStateModel:
    """
    Tracks an actuator's ON/OFF state for /state topic readback.

    Listens to commands on aqua/<node>/<actuator>/set and publishes
    state on aqua/<node>/<actuator>/state.  Includes optional timeout
    (auto-off after *timeout* seconds) for safety actuators like
    auto-refill.
    """

    def __init__(self, initial: str = "OFF", timeout: float | None = None):
        self.state = initial
        self.timeout = timeout       # seconds; None = no auto-off
        self._activated_at: float | None = None

    def set(self, payload: str, elapsed: float):
        """Handle a /set command."""
        payload = payload.strip().upper()
        if payload in ("ON", "OFF"):
            self.state = payload
            if payload == "ON" and self.timeout is not None:
                self._activated_at = elapsed
        # Ignore unrecognized payloads

    def check_timeout(self, elapsed: float) -> bool:
        """Return True if the actuator was auto-off'd by timeout."""
        if (self.timeout is not None and self.state == "ON"
                and self._activated_at is not None
                and elapsed - self._activated_at >= self.timeout):
            self.state = "OFF"
            self._activated_at = None
            return True
        return False

    def read(self) -> str:
        return self.state


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

        # ── New sensors (Task B) ────────────────────────────────────
        self.ec_tds = EcTdsModel(
            base_ec=node_cfg.get("ec_base", 1.2),
            tds_factor=node_cfg.get("tds_factor", 0.5),
        )
        self.turbidity = TurbidityModel(
            baseline=node_cfg.get("turbidity_baseline", 3.0),
            drift_rate=node_cfg.get("turbidity_drift_rate", 0.002),
        )
        self.light = LightModel(
            peak_lux=node_cfg.get("light_peak_lux", 45000.0),
            peak_hour=node_cfg.get("solar_peak_hour", 12),
        )
        self.air_th = AirTempHumidityModel(
            temp_base=node_cfg.get("air_temp_base", 30.0),
            temp_amplitude=node_cfg.get("air_temp_amplitude", 6.0),
            temp_peak_hour=node_cfg.get("air_temp_peak_hour", 13),
            humidity_base=node_cfg.get("air_humidity_base", 65.0),
            humidity_amplitude=node_cfg.get("air_humidity_amplitude", 20.0),
        )
        self.air_pressure = AirPressureModel(
            baseline=node_cfg.get("air_pressure_base", 1010.0),
        )

        # ── Actuator state readback (Task C) ────────────────────────
        self.feeder = ActuatorStateModel()
        self.grow_light = ActuatorStateModel()
        self.refill = ActuatorStateModel(timeout=120.0)   # 2 min safety limit

    def apply_fault(self, fault: dict):
        """Apply a fault injection spec."""
        kind = fault.get("type", "")
        target = fault.get("target", self.node_id)

        # "*" is a wildcard for all nodes (simulator dispatches it per-node).
        if target != "*" and target != self.node_id:
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
        elif kind == "ec_drift":
            self.ec_tds.fault_drift(fault.get("rate", 0.1))
        elif kind == "dirty_turbidity":
            self.turbidity.fault_dirty(fault.get("offset", 15.0))
        elif kind == "light_fault":
            self.light.fault_sensor()
