# aquaponics MQTT sensor simulator

Publishes realistic telemetry to `aqua/<node>/<metric>` MQTT topics so the
entire software stack (Home Assistant, Grafana, automation rules) can be
developed and demoed **before real sensors are online**.

## Quick start

```bash
# 1. Install dependencies (preferably in a venv)
pip install -r requirements.txt

# 2. Start a local MQTT broker (e.g. mosquitto)
#    docker run -d --name mosquitto -p 1883:1883 eclipse-mosquitto

# 3. Run the simulator with defaults
python run.py

# 4. Or with a config file
cp config.example.yaml config.yaml
# edit config.yaml ...
python run.py --config config.yaml
```

## CLI options

```
python run.py --help

  --config FILE         YAML config file (default: built-in defaults)
  --broker HOST         MQTT broker host (overrides config)
  --port PORT           MQTT broker port
  --interval SECONDS    Publish interval (default: 5)
  --time-scale N        Speed up nitrogen cycle (e.g. 10 = 10x)
  --fault TYPE[:NODE]   Inject fault at startup (repeatable)
  --verbose             Debug logging
```

### Fault injection via CLI

```bash
# Pump failure on tank01
python run.py --fault pump_fail:tank01

# High temp on all nodes + low water on tank01
python run.py --fault high_temp:* --fault low_water:tank01

# Pump blocked on tank02
python run.py --fault pump_block:tank02
```

## MQTT topics

| Topic | Payload | Type | Retain | Description |
|-------|---------|------|--------|-------------|
| `aqua/<node>/status` | `online` / `offline` | string | ✅ | LWT presence |
| `aqua/<node>/water_temp` | `28.35` | °C | — | Diurnal sine wave |
| `aqua/<node>/ph` | `7.62` | pH | — | Slow random walk |
| `aqua/<node>/ammonia` | `2.15` | mg/L | — | Nitrogen cycle: NH₃ |
| `aqua/<node>/nitrite` | `1.80` | mg/L | — | Nitrogen cycle: NO₂⁻ |
| `aqua/<node>/nitrate` | `45.3` | mg/L | — | Nitrogen cycle: NO₃⁻ |
| `aqua/<node>/pump_current` | `0.521` | A | — | 220V AC pump (via SSR) |
| `aqua/<node>/flow` | `8.02` | L/min | — | Pump flow rate |
| `aqua/<node>/battery_v` | `12.82` | V | — | 12V DC domain (solar+battery) |
| `aqua/<node>/solar_current` | `1.234` | A | — | Solar panel output |
| `aqua/<node>/low_water` | `OFF` | bool | — | Low water sensor |

### Topic contract

All topics follow the `aqua/<node>/<metric>` namespace defined in
[docs/handbook/13-interfaces.md](../../docs/handbook/13-interfaces.md).
Commands use `aqua/<node>/<actuator>/set`. LWT uses `aqua/<node>/status`.

## Sensor models

### Water temperature
Diurnal sine wave: `base + amplitude * sin(2π * (hour - peak_hour) / 24)`
with ±0.15°C Gaussian noise.

### pH
Bounded random walk between `ph_min` and `ph_max`, ±0.02 per tick.

### Nitrogen cycle
Models the aquarium cycling curve (compressed to `nitrogen_cycle_duration`
seconds for demo):

```
ammonia  ↗ spike then decay   (fish waste → NH₃)
nitrite  ↗ delayed spike       (Nitrosomonas: NH₃ → NO₂⁻)
nitrate  ↗ monotonic rise      (Nitrobacter: NO₂⁻ → NO₃⁻)
```

### Pump (220V AC)
Per [ADR-0004](../../docs/decisions/0004-power-domains.md), the main water
pump is on 220V mains power. `pump_current` is measured on the AC side via
SSR / current sensor. Nominal: 0.52A, 8.0 L/min.

- **pump_fail**: current → 0, flow → 0
- **pump_block**: current × 1.8, flow → 0

### Power (12V DC domain)
Solar panel charges a 12V battery that powers only the control system
(ESP32, sensors, small actuators). Battery voltage rises during solar
hours and dips at night. Solar current is zero at night.

### Low water
Boolean sensor; normally `OFF`. Fault `low_water` forces it `ON`.

## Multi-node support

Add multiple nodes in the config to simulate a multi-tank setup:

```yaml
nodes:
  - id: tank01
    water_temp_base: 28.0
  - id: tank02
    water_temp_base: 26.0
    pump_nominal_flow: 6.0
  - id: growbed01
    water_temp_base: 25.0
    nitrogen_cycle_duration: 3600
```

Each node gets its own LWT and telemetry topics.

## Integration with Home Assistant

The simulator publishes retained `online`/`offline` on
`aqua/<node>/status` — point HA's `mqtt:` integration at the same broker
and use the [home-assistant/packages/](../../home-assistant/packages/)
config to auto-discover all entities.

## Integration with Grafana

Use [Mosquitto → InfluxDB → Grafana] or HA's built-in recorder. The
[dashboard JSON](../../data/grafana/) is pre-configured for the topics
above.
