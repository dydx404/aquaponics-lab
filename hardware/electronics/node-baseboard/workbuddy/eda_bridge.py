#!/usr/bin/env python3
"""EasyEDA Pro Bridge helper.

Sends JS code to the local Bridge server (default port 49620) via HTTP POST
/execute and returns the parsed JSON result. All code runs inside EasyEDA as:

    async function(eda) { <code> }   // must `return` to get a value back

Usage:
    python eda_bridge.py "return await eda.dmt_Project.getCurrentProjectInfo();"
    python eda_bridge.py --file probe.js
"""
import argparse
import json
import sys
import urllib.request

BRIDGE_PORT = 49620
BRIDGE_URL = f"http://127.0.0.1:{BRIDGE_PORT}/execute"


def send(code, timeout=120, window_id=None):
    payload = {"code": code}
    if window_id:
        payload["windowId"] = window_id
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        BRIDGE_URL, data=data, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
    except Exception as e:  # noqa: BLE001
        return {"__error__": f"transport: {e}"}
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return {"__raw__": body}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("code", nargs="?", help="JS code to execute (or use --file)")
    ap.add_argument("--file", help="Read JS code from a file")
    ap.add_argument("--timeout", type=int, default=120)
    ap.add_argument("--window", help="Target EDA windowId")
    ap.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    args = ap.parse_args()

    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            code = f.read()
    elif args.code:
        code = args.code
    else:
        ap.error("provide code or --file")
        return

    result = send(code, timeout=args.timeout, window_id=args.window)
    if args.pretty:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
