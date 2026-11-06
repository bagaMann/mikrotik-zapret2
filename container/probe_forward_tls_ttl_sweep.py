#!/usr/bin/env python3
"""CHR lab TTL sweep (2..8): controlled nfqws2 restart via HTTP POST.
Only container's Linux namespace is modified. RouterOS lab policy stays unchanged.
"""
import ctypes
import http.server
import json
import os
import subprocess
import sys
import time
from urllib.parse import parse_qs

HOST = "172.29.250.2"
PORT = 49339
TABLE = "zapret2_forward_tls_ttl_sweep"
QUEUE = 49167
TARGET = "1.1.1.1"
LOG = "/tmp/zapret2-ttl-sweep.log"
BIN = "/usr/local/bin/nfqws2"
current_ttl = 3
child = None
log_handle = None
table_created = False

def command(*args):
    p = subprocess.run(args, capture_output=True, text=True, errors="replace", timeout=5)
    if p.returncode:
        print("CMD_ERROR " + " ".join(args) + " " + p.stdout[:500] + p.stderr[:500], flush=True)
    return p.returncode

def limit_child_caps():
    libc = ctypes.CDLL(None, use_errno=True)
    libc.prctl.argtypes = [ctypes.c_int, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong]
    libc.prctl.restype = ctypes.c_int
    for cap in (6, 7):
        if libc.prctl(24, cap, 0, 0, 0):
            raise OSError(ctypes.get_errno(), "prctl CAPBSET_DROP")

def stop_worker():
    global child, log_handle, table_created
    # Remove queue rules before stopping the consumer to avoid stalling traffic.
    if table_created:
        command("nft", "delete", "table", "ip", TABLE)
        table_created = False
    if child:
        if child.poll() is None:
            child.terminate()
            try:
                child.wait(timeout=3)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()
        print("RESULT STOP_WORKER_RC=" + str(child.returncode), flush=True)
        child = None
    if log_handle:
        log_handle.close()
        log_handle = None

def start_worker(ttl):
    global child, log_handle, table_created, current_ttl
    stop_worker()
    current_ttl = ttl
    log_handle = open(LOG, "w", buffering=1)
    cmd = [
        BIN, "--qnum=" + str(QUEUE), "--debug=1",
        "--lua-init=@/usr/local/share/zapret2/zapret-lib.lua",
        "--lua-init=@/usr/local/share/zapret2/zapret-antidpi.lua",
        "--filter-tcp=443", "--payload=tls_client_hello",
        "--lua-desync=fake:blob=fake_default_tls:badsum:ip_ttl=" + str(ttl)
    ]
    child = subprocess.Popen(cmd, stdout=log_handle, stderr=subprocess.STDOUT,
                             preexec_fn=limit_child_caps)
    time.sleep(0.75)
    if child.poll() is not None:
        print("RESULT WORKER_FAILED=" + str(child.returncode), flush=True)
        stop_worker()
        return False
    cmds = [
        ("nft", "add", "table", "ip", TABLE),
        ("nft", "add", "chain", "ip", TABLE, "forward",
         "{ type filter hook forward priority -100; policy accept; }"),
        ("nft", "add", "rule", "ip", TABLE, "forward",
         "ip", "daddr", TARGET, "tcp", "dport", "443",
         "counter", "queue", "num", str(QUEUE))
    ]
    for i, cmd in enumerate(cmds):
        if command(*cmd):
            if i:
                table_created = True
            stop_worker()
            return False
        if i == 0:
            table_created = True
    print("RESULT TTL_SWEEP_READY ttl=" + str(ttl) + " queue=" + str(QUEUE), flush=True)
    return True

def stat():
    try:
        s = subprocess.run(["nft", "-a", "list", "chain", "ip", TABLE, "forward"],
                           capture_output=True, text=True, timeout=4)
        nft = s.stdout.strip() if s.returncode == 0 else "nft chain missing"
    except Exception as exc:
        nft = str(exc)
    try:
        with open(LOG, errors="replace") as f:
            lines = f.readlines()
    except OSError:
        lines = []
    return {
        "ttl": current_ttl, "queue": QUEUE,
        "nfqws2_running": child is not None and child.poll() is None,
        "nft_chain": nft,
        "fake_invocations": sum("LUA: fake:" in x for x in lines),
        "rawsend_attempts": sum("rawsend_dissect" in x for x in lines),
        "passed_unmodified": sum("pass unmodified" in x for x in lines),
        "clienthello": sum("TLS client hello is FULL" in x for x in lines),
        "log_tail": [x.strip()[:180] for x in lines[-8:]]
    }

class Handler(http.server.BaseHTTPRequestHandler):
    def send_json(self, result, status=200):
        data = (json.dumps(result, ensure_ascii=False, sort_keys=True) + "\n").encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)
    def do_GET(self):
        if self.path == "/health":
            return self.send_json({"probe": "ttl-sweep", "ttl": current_ttl, "queue": QUEUE,
               "nfqws2_running": child is not None and child.poll() is None})
        if self.path == "/stats":
            return self.send_json(stat())
        self.send_json({"error": "GET /health, GET /stats, POST /ttl body ttl=N (2..8)"}, 404)
    def do_POST(self):
        if self.path != "/ttl":
            return self.send_json({"error": "not found"}, 404)
        try:
            n = int(self.headers.get("Content-Length", "0"))
            if n < 1 or n > 32:
                raise ValueError("invalid length")
            params = parse_qs(self.rfile.read(n).decode("ascii"), strict_parsing=True)
            if sorted(params.keys()) != ["ttl"] or len(params["ttl"]) != 1:
                raise ValueError("expected ttl=N")
            ttl = int(params["ttl"][0])
            if not 2 <= ttl <= 8:
                raise ValueError("ttl must be 2..8")
        except (ValueError, UnicodeError) as exc:
            return self.send_json({"error": str(exc)}, 400)
        if ttl == current_ttl and child is not None and child.poll() is None:
            return self.send_json({"status": "unchanged", **stat()})
        ok = start_worker(ttl)
        self.send_json({"status": "ready" if ok else "failed", **stat()}, 200 if ok else 503)
    def log_message(self, fmt, *args):
        print("HTTP " + fmt % args, flush=True)

def main():
    if not os.path.isfile(BIN):
        print("RESULT FATAL=missing_nfqws2", flush=True)
        return 20
    try:
        with open("/proc/sys/net/ipv4/ip_forward", "w") as f:
            f.write("1\n")
    except OSError as exc:
        print("RESULT FORWARD_ERROR=" + repr(exc), flush=True)
        return 21
    if command("nft", "list", "table", "ip", TABLE) == 0:
        print("RESULT FATAL=table_already_exists", flush=True)
        return 22
    if not start_worker(current_ttl):
        return 23
    try:
        server = http.server.HTTPServer((HOST, PORT), Handler)
        print("RESULT CONTROL_READY=" + HOST + ":" + str(PORT), flush=True)
        server.serve_forever()
    finally:
        stop_worker()
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print("RESULT FATAL=" + repr(exc), flush=True)
        stop_worker()
        sys.exit(30)
