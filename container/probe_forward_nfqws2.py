#!/usr/bin/env python3
"""CHR laboratory: forwarded ICMP to 1.1.1.1 -> nft NFQUEUE -> native nfqws2 PASS.

The RouterOS routing mark and dedicated route must already exist. This service
only modifies its own container network namespace. It deliberately does not
alter RouterOS routes, its firewall or any other nftables tables.
"""
import ctypes
import http.server
import json
import os
import signal
import subprocess
import sys
import time

HOST = "172.29.250.2"
PORT = 49332
TABLE = "zapret2_forward_nfqws2"
QUEUE = 49160
TARGET = "1.1.1.1"
LOG = "/tmp/zapret2-forward-nfqws2.log"
BIN = "/usr/local/bin/nfqws2"
PR_CAPBSET_DROP = 24
CAP_SETGID = 6
CAP_SETUID = 7
child = None
log_handle = None
table_created = False

def command(*args):
    try:
        p = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           timeout=5, text=True, errors="replace")
        print("CMD " + " ".join(args) + " rc=" + str(p.returncode), flush=True)
        if p.returncode != 0:
            print("CMD_ERROR " + p.stdout[:1000], flush=True)
        return {"rc": p.returncode, "output": p.stdout.strip()[:4000]}
    except Exception as exc:
        print("CMD_EXCEPTION " + repr(exc), flush=True)
        return {"rc": -1, "error": repr(exc)}

def sysctl(path):
    try:
        with open(path, "r") as f:
            return f.read().strip()
    except OSError as exc:
        return "ERROR:" + str(exc)

def enable_forward():
    path = "/proc/sys/net/ipv4/ip_forward"
    before = sysctl(path)
    if before != "1":
        try:
            with open(path, "w") as f:
                f.write("1\n")
        except OSError as exc:
            print("RESULT IP_FORWARD_ERROR=" + repr(exc), flush=True)
            return False
    after = sysctl(path)
    print("RESULT IP_FORWARD_BEFORE=" + before, flush=True)
    print("RESULT IP_FORWARD_AFTER=" + after, flush=True)
    return after == "1"

def limit_child_caps():
    libc = ctypes.CDLL(None, use_errno=True)
    libc.prctl.argtypes = [ctypes.c_int, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong]
    libc.prctl.restype = ctypes.c_int
    for cap in (CAP_SETGID, CAP_SETUID):
        if libc.prctl(PR_CAPBSET_DROP, cap, 0, 0, 0) != 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))

def log_tail():
    try:
        with open(LOG, "r", errors="replace") as f:
            return f.readlines()[-100:]
    except OSError:
        return []

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split("?", 1)[0]
        lines = log_tail()
        if path == "/health":
            data = {"probe": "forward-nfqws2", "ip_forward": sysctl("/proc/sys/net/ipv4/ip_forward"),
                    "nfqws2_running": child is not None and child.poll() is None,
                    "addresses": command("ip", "-4", "-brief", "address"),
                    "routes": command("ip", "-4", "route")}
        elif path == "/stats":
            data = {"probe": "forward-nfqws2", "ip_forward": sysctl("/proc/sys/net/ipv4/ip_forward"),
                    "nfqws2_running": child is not None and child.poll() is None,
                    "nft_chain": command("nft", "-a", "list", "chain", "ip", TABLE, "forward"),
                    "packet_log_count": sum("packet: id=" in l and " len=" in l for l in lines),
                    "nfqws2_received_target": sum("IP4:" in l and "=> " + TARGET in l for l in lines),
                    "nfqws2_pass_unmodified": sum("pass unmodified" in l for l in lines),
                    "nfqws2_log_tail": [l.strip()[:280] for l in lines[-35:]]}
        else:
            data = {"error": "not found", "paths": ["/health", "/stats"]}
        blob = (json.dumps(data, ensure_ascii=False, sort_keys=True) + "\n").encode()
        self.send_response(200 if "error" not in data else 404)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(blob)))
        self.end_headers()
        self.wfile.write(blob)
        print("RESULT HTTP_REQUEST=" + path, flush=True)

    def log_message(self, fmt, *args):
        print("HTTP " + (fmt % args), flush=True)

def cleanup():
    global child, log_handle, table_created
    if table_created:
        command("nft", "delete", "table", "ip", TABLE)
        table_created = False
    if child is not None:
        if child.poll() is None:
            child.terminate()
            try:
                child.wait(timeout=3)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait(timeout=3)
        print("RESULT NFQWS2_EXIT=" + str(child.returncode), flush=True)
        child = None
    if log_handle:
        log_handle.close()
        log_handle = None

def main():
    global child, log_handle, table_created
    print("=== CHR native nfqws2 forwarded ICMP test ===", flush=True)
    print("RESULT ROUTEROS_MUTATIONS=NONE", flush=True)
    print("RESULT TARGET=" + TARGET + " ICMP ONLY", flush=True)
    if not os.path.isfile(BIN) or not enable_forward():
        print("RESULT STARTUP_FAILED=prerequisite", flush=True)
        return 20

    present = subprocess.run(["nft", "list", "table", "ip", TABLE],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if present.returncode == 0:
        print("RESULT STARTUP_FAILED=existing_nft_table", flush=True)
        return 21
    log_handle = open(LOG, "w", buffering=1)
    try:
        cmd = [BIN, f"--qnum={QUEUE}", "--debug=1"]
        child = subprocess.Popen(cmd, stdout=log_handle, stderr=subprocess.STDOUT,
                                 start_new_session=True, preexec_fn=limit_child_caps)
        print("RESULT NFQWS2_STARTED_PID=" + str(child.pid), flush=True)
        time.sleep(1)
        if child.poll() is not None:
            print("RESULT STARTUP_FAILED=nfqws2_exit_" + str(child.returncode), flush=True)
            return 22
        if command("nft", "add", "table", "ip", TABLE)["rc"] != 0:
            return 23
        table_created = True
        if command("nft", "add", "chain", "ip", TABLE, "forward",
                   "{ type filter hook forward priority -100; policy accept; }")["rc"] != 0:
            return 24
        if command("nft", "add", "rule", "ip", TABLE, "forward",
                   "ip", "daddr", TARGET, "ip", "protocol", "icmp",
                   "counter", "queue", "num", str(QUEUE))["rc"] != 0:
            return 25
        print("RESULT FORWARD_NFQUEUE_READY=" + str(QUEUE), flush=True)
        http.server.ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
        return 0
    finally:
        cleanup()

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print("RESULT FATAL_ERROR=" + repr(exc), flush=True)
        cleanup()
        sys.exit(30)
