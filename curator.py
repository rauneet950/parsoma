"""
Curator agent — subscribes to GossipSub topic and builds soul-elon.json.
Also serves GET /soul on port 8080 for Riya's chat CLI.

Run after all nodes are peered:
  python3 curator.py
"""
import base64
import hashlib
import json
import subprocess
import sys
import time
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent / "examples/python-client/gossipsub"))
from gossipsub import GossipSub, GossipConfig  # noqa: E402

CURATOR_API = "http://127.0.0.1:9002"
TOPIC = "soul-elon-musk"
SOUL_FILE = Path(__file__).parent / "soul-elon.json"
REQUIRED_FIELDS = {"soul_id", "claw_id", "dimension", "content"}

# ── Soul file helpers ────────────────────────────────────────────────────────

def load_soul():
    if SOUL_FILE.exists():
        return json.loads(SOUL_FILE.read_text())
    return {
        "soul_id": "soul-elon-musk",
        "ens_name": "soul-elon.eth",
        "stage": "embryo",
        "fingerprint": "",
        "fragments": [],
        "contributors": {},
    }


def save_soul(soul):
    fingerprint = hashlib.sha256(json.dumps(soul["fragments"], sort_keys=True).encode()).hexdigest()
    soul["fingerprint"] = fingerprint
    SOUL_FILE.write_text(json.dumps(soul, indent=2))
    return fingerprint


def accept_fragment(soul, fragment):
    soul["fragments"].append({
        "dimension": fragment["dimension"],
        "content": fragment["content"],
        "claw_id": fragment["claw_id"],
        "accepted_at": datetime.now(timezone.utc).isoformat(),
    })
    claw_id = fragment["claw_id"]
    contributors = soul.setdefault("contributors", {})
    if claw_id not in contributors:
        contributors[claw_id] = {"wallet": fragment.get("claw_wallet", ""), "accepted_count": 0}
    contributors[claw_id]["accepted_count"] += 1
    soul["stage"] = "growing"
    return save_soul(soul)

# ── GossipSub helpers ────────────────────────────────────────────────────────

def make_send_fn():
    def send_fn(dest_key, data):
        requests.post(
            f"{CURATOR_API}/send",
            headers={"X-Destination-Peer-Id": dest_key, "Content-Type": "application/octet-stream"},
            data=data,
            timeout=5,
        )
    return send_fn


def make_recv_fn():
    def recv_fn():
        resp = requests.get(f"{CURATOR_API}/recv", timeout=5)
        if resp.status_code == 200:
            from_id = resp.headers.get("X-From-Peer-Id", "")
            return from_id, resp.content
        return None
    return recv_fn


def get_topology():
    resp = requests.get(f"{CURATOR_API}/topology", timeout=5)
    resp.raise_for_status()
    return resp.json()

# ── GossipSub subclass with delivery callback ────────────────────────────────

class CuratorGossipSub(GossipSub):
    def __init__(self, *args, on_message=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._on_message = on_message

    def _handle_message(self, from_id, msg):
        msg_id = msg.get("msg_id", "")
        is_new = msg_id not in self.seen_msgs
        topic = msg.get("topic", "")
        super()._handle_message(from_id, msg)
        if is_new and topic in self.subscriptions and self._on_message:
            raw = base64.b64decode(msg.get("data", ""))
            self._on_message(topic, from_id, raw)

# ── Simple HTTP server to serve soul JSON ───────────────────────────────────

class SoulHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/soul":
            body = SOUL_FILE.read_bytes() if SOUL_FILE.exists() else b"{}"
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *args):  # silence access logs
        pass

# ── Main ─────────────────────────────────────────────────────────────────────

def on_fragment(topic, from_id, raw):
    try:
        fragment = json.loads(raw)
    except Exception:
        print("[CURATOR] Could not parse fragment JSON")
        return

    if not REQUIRED_FIELDS.issubset(fragment.keys()):
        print(f"[CURATOR] Rejected — missing fields: {REQUIRED_FIELDS - fragment.keys()}")
        return

    soul = load_soul()
    fingerprint = accept_fragment(soul, fragment)
    print(f"[CURATOR] Accepted fragment from {fragment['claw_id']}: {fragment['dimension']}")
    print(f"[CURATOR] Soul fingerprint: {fingerprint[:16]}...")

    # Update ENS text records on Sepolia (non-blocking)
    ens_script = Path(__file__).parent / "ens" / "ens_update.js"
    stage = soul.get("stage", "growing")
    subprocess.Popen(
        ["node", str(ens_script), fingerprint, stage],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )


def main():
    # Start soul HTTP server in background
    server = HTTPServer(("127.0.0.1", 8080), SoulHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    print("[CURATOR] Soul HTTP server on http://127.0.0.1:8080/soul")

    topo = get_topology()
    my_id = topo["our_public_key"]
    print(f"[CURATOR] Public key: {my_id}")
    print(f"[CURATOR] Waiting for fragments on topic '{TOPIC}'...")

    gs = CuratorGossipSub(GossipConfig(), my_id, make_send_fn(), make_recv_fn(),
                          on_message=on_fragment)
    gs.subscribe(TOPIC)

    known_peers = set()
    while True:
        try:
            topo = get_topology()
            current_peers = {p["public_key"] for p in topo.get("peers", [])}
            for peer in current_peers - known_peers:
                gs.add_peer(peer)
                known_peers.add(peer)
            gs.tick()
        except requests.exceptions.RequestException as e:
            print(f"[CURATOR] API error: {e}")
        time.sleep(0.2)


if __name__ == "__main__":
    main()
