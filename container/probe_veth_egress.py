#!/usr/bin/env python3
"""Persistent, read-only VETH connectivity probe for the CHR lab.

The probe deliberately performs no sysctl, routing, nftables or iptables changes.
HTTP is only bound to the configured container VETH address.
"""
import http.server
import json
import os
import socket
import subprocess
import sys
import time

HOST = os.environ.get("PROBE_HOST", "172.29.250.2")
PORT = int(os.environ.get("PROBE_PORT", "49330"))

def cmd(*args):
    try:
        p = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           text=True, timeout=4, errors="replace")
        return {"rc": p.returncode, "output": p.stdout.strip()[:3000]}
    except Exception as exc:
        return {"error": repr(exc)}

def egress():
    results = []
    for host, port in (("1.1.1.1", 443), ("9.9.9.9", 443)):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        start = time.monotonic()
        try:
            s.connect((host, port))
            results.append({"endpoint": f"{host}:{port}", "ok": True,
                            "local": str(s.getsockname()), "elapsed_ms": round((time.monotonic()-start)*1000)})
        except Exception as exc:
            results.append({"endpoint": f"{host}:{port}", "ok": False, "error": str(exc)})
        finally:
            s.close()
    return results

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/health":
            data = {"probe": "veth-egress", "status": "alive", "bind": f"{HOST}:{PORT}",
                    "addresses": cmd("ip", "-4", "-brief", "address"),
                    "routes": cmd("ip", "-4", "route")}
            status = 200
        elif path == "/egress":
            data = {"probe": "veth-egress", "tcp_connect": egress()}
            status = 200
        else:
            data = {"error": "not found", "paths": ["/health", "/egress"]}
            status = 404
        output = (json.dumps(data, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(output)))
        self.end_headers()
        self.wfile.write(output)
        print(f"RESULT HTTP_REQUEST path={path} status={status}", flush=True)

    def log_message(self, format, *args):
        print("HTTP " + (format % args), flush=True)

def main():
    print("=== CHR VETH reachability and outbound TCP probe ===", flush=True)
    print("RESULT NETWORK_MUTATIONS=NONE", flush=True)
    print("RESULT IP_ADDR=" + json.dumps(cmd("ip", "-4", "address", "show"), ensure_ascii=False), flush=True)
    print("RESULT IP_ROUTE=" + json.dumps(cmd("ip", "-4", "route"), ensure_ascii=False), flush=True)
    server = http.server.ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"RESULT VETH_HTTP_LISTENING={HOST}:{PORT}", flush=True)
    server.serve_forever(poll_interval=0.5)

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("RESULT PROBE_FATAL=" + repr(exc), flush=True)
        sys.exit(1)
