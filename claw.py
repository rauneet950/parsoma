"""
Claw agent — publishes a soul fragment via GossipSub.

Usage:
  python3 claw.py --id claw-a --port 9012 --dimension communication_style \
      --content "Short punchy sentences." --wallet 0xABC
"""
import argparse
import base64
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent / "examples/python-client/gossipsub"))
from gossipsub import GossipSub, GossipConfig  # noqa: E402

TOPIC = "soul-elon-musk"
TICK_SECONDS = 8  # time to let mesh form + message propagate


def make_send_fn(api_port):
    def send_fn(dest_key, data):
        requests.post(
            f"http://127.0.0.1:{api_port}/send",
            headers={"X-Destination-Peer-Id": dest_key, "Content-Type": "application/octet-stream"},
            data=data,
            timeout=5,
        )
    return send_fn


def make_recv_fn(api_port):
    def recv_fn():
        resp = requests.get(f"http://127.0.0.1:{api_port}/recv", timeout=5)
        if resp.status_code == 200:
            from_id = resp.headers.get("X-From-Peer-Id", "")
            return from_id, resp.content
        return None
    return recv_fn


def get_topology(api_port):
    resp = requests.get(f"http://127.0.0.1:{api_port}/topology", timeout=5)
    resp.raise_for_status()
    return resp.json()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--id", required=True, help="claw-a / claw-b / claw-c")
    parser.add_argument("--port", type=int, default=9012)
    parser.add_argument("--dimension", required=True,
                        choices=["communication_style", "knowledge_depth", "stance_on_ai",
                                 "decision_patterns", "relationships", "timeline"])
    parser.add_argument("--content", required=True)
    parser.add_argument("--wallet", default="0x0000000000000000000000000000000000000000")
    args = parser.parse_args()

    topo = get_topology(args.port)
    my_id = topo["our_public_key"]
    peers = [p["public_key"] for p in topo.get("peers", [])]

    if not peers:
        print("[CLAW] No peers connected yet. Is the curator node running?")
        sys.exit(1)

    gs = GossipSub(GossipConfig(), my_id, make_send_fn(args.port), make_recv_fn(args.port))
    for peer in peers:
        gs.add_peer(peer)
    gs.subscribe(TOPIC)

    fragment = {
        "soul_id": "soul-elon-musk",
        "claw_id": args.id,
        "claw_wallet": args.wallet,
        "dimension": args.dimension,
        "content": args.content,
        "source": "public_data",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "signature": "demo",
    }

    # Let mesh form first
    deadline = time.time() + TICK_SECONDS
    published = False
    while time.time() < deadline:
        gs.tick()
        if not published and gs.mesh.get(TOPIC):
            gs.publish(TOPIC, json.dumps(fragment).encode())
            print(f"[{args.id}] Published fragment: {args.dimension}")
            published = True
        time.sleep(0.2)

    if not published:
        # Publish even without mesh — sends to all known peers
        gs.publish(TOPIC, json.dumps(fragment).encode())
        print(f"[{args.id}] Published fragment (no mesh formed): {args.dimension}")

    # Keep ticking to handle IWANT responses
    for _ in range(10):
        gs.tick()
        time.sleep(0.2)

    print(f"[{args.id}] Done.")


if __name__ == "__main__":
    main()
