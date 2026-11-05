#!/usr/bin/env python3
"""CHR lab: enable container forwarding, count transiting packets; no NFQUEUE yet.
A dedicated routing table on RouterOS must select traffic; never alter main route.
"""
import http.server
import json
import os
import subprocess
import sys

HOST = "172.29.250.2"
PORT = 49331
TABLE = "zapret2_forward_lab"

def command(*args):
    try:
        result = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, timeout=5)
        print("CMD " + " ".join(args) + " rc=" + str(result.returncode), flush=True)
        return {"rc": result.returncode, "output": result.stdout.strip()[:3000]}
    except Exception as exc:
        return {"rc": -1, "error": repr(exc)}

def read_sysctl(path):
    try:
        with open(path) as f:
            return f.read().strip()
    except OSError as exc:
        return "ERROR:" + str(exc)

def enable_forward():
    path = "/proc/sys/net/ipv4/ip_forward"
    before = read_sysctl(path)
    error = None
    if before != "1":
        try:
            with open(path, "w") as f:
                f.write("1\n")
        except OSError as exc:
            error = repr(exc)
    after = read_sysctl(path)
    print("RESULT IP_FORWARD_BEFORE=" + before, flush=True)
    print("RESULT IP_FORWARD_AFTER=" + after, flush=True)
    if error:
        print("RESULT IP_FORWARD_WRITE_ERROR=" + error, flush=True)
    return after == "1"

def setup_counter():
    check = subprocess.run(["nft", "list", "table", "ip", TABLE],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if check.returncode == 0:
        print("RESULT EXISTING_NFT_TABLE_ABORT", flush=True)
        return False
    steps = [
        ("nft", "add", "table", "ip", TABLE),
        ("nft", "add", "chain", "ip", TABLE, "forward",
         "{ type filter hook forward priority -100; policy accept; }"),
        ("nft", "add", "rule", "ip", TABLE, "forward",
         "ip", "daddr", "1.1.1.1", "counter"),
    ]
    for step in steps:
        result = command(*step)
        if result["rc"] != 0:
            command("nft", "delete", "table", "ip", TABLE)
            return False
    return True

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split("?", 1)[0]
        data = {"probe": "veth-forward", "ip_forward": read_sysctl("/proc/sys/net/ipv4/ip_forward")}
        if path == "/health":
            data["addresses"] = command("ip", "-4", "-brief", "address")
            data["routes"] = command("ip", "-4", "route")
        elif path == "/forward":
            data["counter"] = command("nft", "-a", "list", "chain", "ip", TABLE, "forward")
        else:
            data["error"] = "unknown endpoint"
        response = (json.dumps(data, sort_keys=True) + "\n").encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)

    def log_message(self, fmt, *args):
        print("HTTP " + fmt % args, flush=True)

if __name__ == "__main__":
    print("RESULT LAB_SCOPE=container Linux netns only", flush=True)
    if not enable_forward():
        print("RESULT FORWARD_PROBE_FAILED=ip_forward_unavailable", flush=True)
        sys.exit(20)
    if not setup_counter():
        print("RESULT FORWARD_PROBE_FAILED=nft_setup", flush=True)
        sys.exit(21)
    try:
        server = http.server.ThreadingHTTPServer((HOST, PORT), Handler)
        print("RESULT FORWARD_PROBE_READY=" + HOST + ":" + str(PORT), flush=True)
        server.serve_forever()
    finally:
        command("nft", "delete", "table", "ip", TABLE)
