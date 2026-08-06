"""
Simulator orchestrator — ties models + MQTT publisher together.

Each tick:
  1. For every node, read all sensor models.
  2. Publish values to aqua/<node>/<metric> topics.
  3. Sleep *interval* seconds, repeat.
"""

from __future__ import annotations

import logging
import random
import signal
import time
from datetime import datetime, timezone

from .config import load_config
from .models import NodeModels
from .mqtt_publisher import MqttPublisher

logger = logging.getLogger(__name__)


class AquaponicsSimulator:
    """Main simulator loop."""

    def __init__(self, config_path: str | None = None):
        self.cfg = load_config(config_path)

        seed = self.cfg["sim"].get("random_seed")
        if seed is not None:
            random.seed(seed)

        self.interval: float = self.cfg["sim"]["interval"]
        self.time_scale: float = self.cfg["sim"].get("time_scale", 1.0)

        # Build node model bundles
        self._models: dict[str, NodeModels] = {}
        for ncfg in self.cfg["nodes"]:
            nm = NodeModels(ncfg)
            self._models[nm.node_id] = nm
            # Start nitrogen cycle
            nm.nitrogen.start(0.0)

        # Apply fault injections from config
        self.faults = self.cfg.get("faults", [])
        for fault in self.faults:
            target = fault.get("target")
            if target in self._models:
                self._models[target].apply_fault(fault)
            else:
                # Apply to all nodes if target is "*"
                if target == "*":
                    for nm in self._models.values():
                        nm.apply_fault(fault)

        # Create MQTT publisher
        node_ids = list(self._models.keys())
        self._publisher = MqttPublisher(self.cfg["broker"], node_ids)

        self._running = False

    # ── metrics per tick ──────────────────────────────────────────────

    def _read_and_publish(self, node_id: str, nm: NodeModels,
                          elapsed: float):
        """Read all models for a node and publish to MQTT."""
        now = datetime.now(timezone.utc)

        # Water temp
        wt = nm.water_temp.read(now)
        self._publisher.publish_metric(node_id, "water_temp", wt)

        # pH
        ph = nm.ph.read(now)
        self._publisher.publish_metric(node_id, "ph", ph)

        # Nitrogen cycle
        nh3, no2, no3 = nm.nitrogen.read(elapsed * self.time_scale)
        self._publisher.publish_metric(node_id, "ammonia", nh3)
        self._publisher.publish_metric(node_id, "nitrite", no2)
        self._publisher.publish_metric(node_id, "nitrate", no3)

        # Pump (220 V AC side)
        pump_current, flow = nm.pump.read()
        self._publisher.publish_metric(node_id, "pump_current", pump_current)
        self._publisher.publish_metric(node_id, "flow", flow)

        # Power (12 V DC domain)
        battery_v = nm.power.read_battery(now)
        solar_current = nm.power.read_solar_current(now)
        self._publisher.publish_metric(node_id, "battery_v", battery_v)
        self._publisher.publish_metric(node_id, "solar_current", solar_current)

        # Low water (boolean)
        low_water = nm.low_water.read()
        self._publisher.publish_metric(node_id, "low_water", low_water)

    # ── main loop ─────────────────────────────────────────────────────

    def run(self):
        """Run the simulation loop until interrupted."""
        self._publisher.connect()
        self._running = True

        def _stop(*_):
            self._running = False

        signal.signal(signal.SIGINT, _stop)
        signal.signal(signal.SIGTERM, _stop)

        start = time.monotonic()
        tick = 0

        logger.info("Simulator started — %d nodes, %ds interval, time_scale=%.1f",
                     len(self._models), self.interval, self.time_scale)

        try:
            while self._running:
                elapsed = time.monotonic() - start
                for node_id, nm in self._models.items():
                    self._read_and_publish(node_id, nm, elapsed)

                tick += 1
                if tick % 12 == 0:  # log every ~1 min at 5s interval
                    logger.info("tick %d, elapsed %.0fs", tick, elapsed)

                time.sleep(self.interval)
        finally:
            self._publisher.disconnect()
            logger.info("Simulator stopped after %d ticks.", tick)
