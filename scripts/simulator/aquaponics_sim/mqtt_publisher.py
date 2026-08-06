"""
MQTT publisher — wraps paho-mqtt with LWT and topic helpers.

All topics follow the aqua/<node>/<metric> contract:
  - Telemetry:  aqua/<node>/<metric>
  - Commands:   aqua/<node>/<actuator>/set
  - LWT status: aqua/<node>/status  ("online" / "offline")
"""

from __future__ import annotations

import json
import logging
from typing import Any

import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)


class MqttPublisher:
    """Thin wrapper around paho-mqtt with LWT and JSON payloads."""

    def __init__(self, broker: dict, nodes: list[str]):
        host = broker.get("host", "localhost")
        port = broker.get("port", 1883)
        username = broker.get("username")
        password = broker.get("password")

        client_id = f"aquaponics-sim-{nodes[0]}" if nodes else "aquaponics-sim"

        # Build LWT topics for all nodes
        wills = []
        for node_id in nodes:
            topic = f"aqua/{node_id}/status"
            wills.append({
                "topic": topic,
                "payload": "offline",
                "qos": 1,
                "retain": True,
            })

        self._client = mqtt.Client(
            client_id=client_id,
            clean_session=True,
        )

        if username:
            self._client.username_pw_set(username, password or "")

        # Set the first will via paho's built-in LWT (single will supported natively)
        if wills:
            w = wills[0]
            self._client.will_set(
                topic=w["topic"],
                payload=w["payload"],
                qos=w["qos"],
                retain=w["retain"],
            )

        self._all_wills = wills  # we'll publish the rest manually on connect
        self._host = host
        self._port = port

    def connect(self):
        """Connect and publish online status for all nodes."""
        self._client.connect(self._host, self._port, keepalive=60)
        self._client.loop_start()

        # Publish online for all nodes (first node is covered by LWT,
        # but we publish explicitly anyway for clarity)
        for w in self._all_wills:
            self._client.publish(
                topic=w["topic"],
                payload="online",
                qos=1,
                retain=True,
            )

        logger.info("Connected to %s:%d, %d nodes online",
                     self._host, self._port, len(self._all_wills))

    def publish_metric(self, node_id: str, metric: str, value: Any,
                       retain: bool = False, qos: int = 0):
        """Publish a telemetry value to aqua/<node>/<metric>."""
        topic = f"aqua/{node_id}/{metric}"
        if isinstance(value, bool):
            payload = "ON" if value else "OFF"
        elif isinstance(value, float):
            payload = str(value)
        elif isinstance(value, int):
            payload = str(value)
        else:
            payload = str(value)

        self._client.publish(topic, payload, qos=qos, retain=retain)

    def publish_status(self, node_id: str, status: str = "online"):
        """Publish LWT status for a node."""
        topic = f"aqua/{node_id}/status"
        self._client.publish(topic, status, qos=1, retain=True)

    def disconnect(self):
        """Publish offline for all nodes, then disconnect."""
        for w in self._all_wills:
            self._client.publish(
                topic=w["topic"],
                payload="offline",
                qos=1,
                retain=True,
            )
        self._client.loop_stop()
        self._client.disconnect()
        logger.info("Disconnected, all nodes offline.")
