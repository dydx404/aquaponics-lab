#!/usr/bin/env python3
"""
Entry point for the aquaponics MQTT sensor simulator.

Usage:
    python run.py                              # defaults
    python run.py --config config.example.yaml # with config
    python run.py --broker 192.168.1.100       # override broker
    python run.py --interval 2                 # 2s publish interval
    python run.py --fault pump_fail:tank01     # inject fault at startup
"""

from __future__ import annotations

import argparse
import logging
import sys

# Allow running directly: `python run.py`
sys.path.insert(0, ".")

from aquaponics_sim.simulator import AquaponicsSimulator


def parse_args():
    p = argparse.ArgumentParser(
        description="Aquaponics MQTT sensor simulator",
    )
    p.add_argument(
        "--config", "-c",
        default=None,
        help="Path to YAML config file (default: built-in defaults)",
    )
    p.add_argument(
        "--broker",
        default=None,
        help="MQTT broker host (overrides config)",
    )
    p.add_argument(
        "--port",
        type=int,
        default=None,
        help="MQTT broker port (overrides config)",
    )
    p.add_argument(
        "--interval",
        type=float,
        default=None,
        help="Publish interval in seconds (overrides config)",
    )
    p.add_argument(
        "--time-scale",
        type=float,
        default=None,
        help="Time scale factor for nitrogen cycle (e.g. 10 = 10x speed)",
    )
    p.add_argument(
        "--fault",
        action="append",
        default=[],
        help="Inject fault: TYPE[:TARGET] (e.g. pump_fail:tank01, high_temp:*, low_water)",
    )
    p.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable debug logging",
    )
    return p.parse_args()


def main():
    args = parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    sim = AquaponicsSimulator(args.config)

    # CLI overrides
    if args.broker:
        sim.cfg["broker"]["host"] = args.broker
    if args.port:
        sim.cfg["broker"]["port"] = args.port
    if args.interval:
        sim.interval = args.interval
    if args.time_scale:
        sim.time_scale = args.time_scale

    # CLI fault injection
    for spec in args.fault:
        parts = spec.split(":")
        fault_type = parts[0]
        target = parts[1] if len(parts) > 1 else "*"

        fault = {"type": fault_type, "target": target}
        sim.faults.append(fault)

        if target == "*":
            for nm in sim._models.values():
                nm.apply_fault(fault)
        elif target in sim._models:
            sim._models[target].apply_fault(fault)
        else:
            logging.warning("Unknown node '%s' for fault '%s'", target, fault_type)

    sim.run()


if __name__ == "__main__":
    main()
