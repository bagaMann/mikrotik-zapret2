#!/usr/bin/env python3
"""Lab-only combined TCP TLS and UDP QUIC nfqws2 probe for CHR.
Only one explicitly configured IPv4 target:443 is queued. No RouterOS configuration is changed.
"""
import ctypes
import http.server
import ipaddress
import json
import os
import subprocess
import sys
import time

HOST = "172.29.250.2"
PORT = 49342
TABLE = "zapret2_combined_lab"
TARGET = "1.1.1.1"
SET = "targets"
BIN = "/usr/local/bin/nfqws2"
LUA = [
    "--lua-init=@/usr/local/share/zapret2/zapret-lib.lua",
    "--lua-init=@/usr/local/share/zapret2/zapret-antidpi.lua",
]
PROFILES = {
    "tcp": {
        "queue": 49170, "log": "/tmp/zapret2-combined-tcp.log",
        "args": ["--filter-tcp=443", "--payload=tls_client_hello",
                 "--lua-desync=fake:blob=fake_default_tls:badsum:ip_ttl=8"],
    },
    "udp": {
        "queue": 49171, "log": "/tmp/zapret2-combined-udp.log",
        "args": ["--filter-udp=443", "--payload=quic_initial",
                 "--lua-desync=fake:blob=fake_default_quic:ip_ttl=8"],
    },
}
children = {}
handles = {}
table_created = False

def run(*argv):
    p = subprocess.run(argv, capture_output=True, text=True, errors="replace", timeout=8)
    if p.returncode:
        print("CMD_FAILURE " + " ".join(argv) + " " + (p.stdout + p.stderr)[:500], flush=True)
    return p

def caps():
    libc = ctypes.CDLL(None, use_errno=True)
    libc.prctl.argtypes = [ctypes.c_int, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong]
    libc.prctl.restype = ctypes.c_int
    for cap in (6, 7):
        if libc.prctl(24, cap, 0, 0, 0):
            raise OSError(ctypes.get_errno(), "CAPBSET_DROP failed")

def stop_all():
    global table_created
    # Remove all NFQUEUE rules first, to avoid traffic stalling during shutdown.
    if table_created:
        run("nft", "delete", "table", "ip", TABLE)
        table_created = False
    for name, proc in list(children.items()):
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
        print("RESULT STOP_" + name + "_RC=" + str(proc.returncode), flush=True)
        del children[name]
    for handle in handles.values():
        handle.close()
    handles.clear()

def tail(path):
    try:
        with open(path, errors="replace") as f:
            lines = f.readlines()
        return {
            "clienthello": sum("TLS client hello is FULL" in x for x in lines),
            "quic_initial": sum("packet contains quic_initial" in x for x in lines),
            "fake": sum("LUA: fake: " in x and "not acting" not in x for x in lines),
            "rawsend": sum("rawsend_dissect" in x for x in lines),
            "recent": [x.strip()[:220] for x in lines[-12:]]
        }
    except OSError:
        return {"error": "log missing"}

def update_target(new_target):
    global TARGET
    addr = ipaddress.IPv4Address(new_target)
    if not addr.is_global:
        raise ValueError("target must be a public IPv4 address")
    # A temporary gap in interception is intentional and fail-open for this lab.
    if run("nft", "flush", "set", "ip", TABLE, SET).returncode:
        raise RuntimeError("failed to flush targets set")
    if run("nft", "add", "element", "ip", TABLE, SET, "{ " + str(addr) + " }").returncode:
        # restore the previous target on update failure
        run("nft", "add", "element", "ip", TABLE, SET, "{ " + TARGET + " }")
        raise RuntimeError("failed to add target to nft set")
    TARGET = str(addr)
    print("RESULT TARGET_CHANGED=" + TARGET, flush=True)

def status():
    p = run("nft", "-a", "list", "chain", "ip", TABLE, "forward")
    return {
        "probe": "combined-tcp-udp",
        "target": TARGET,
        "ip_forward": open("/proc/sys/net/ipv4/ip_forward").read().strip(),
        "nft": p.stdout.strip() if p.returncode == 0 else "not available",
        "profiles": {
            name: {
                "queue": data["queue"],
                "running": name in children and children[name].poll() is None,
                "log": tail(data["log"])
            } for name, data in PROFILES.items()
        }
    }

class Handler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/target":
            self.respond({"error": "use POST /target"}, 404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 1 <= length <= 64:
                raise ValueError("body must be ip=A.B.C.D")
            body = self.rfile.read(length).decode("ascii")
            if not body.startswith("ip="):
                raise ValueError("body must be ip=A.B.C.D")
            update_target(body[3:].strip())
            self.respond({"ok": True, "target": TARGET}, 200)
        except (ValueError, UnicodeError) as exc:
            self.respond({"error": str(exc)}, 400)
        except Exception as exc:
            self.respond({"error": str(exc)}, 500)

    def do_GET(self):
        if self.path not in ("/health", "/stats"):
            result, status_code = {"error": "use /health or /stats"}, 404
        else:
            result, status_code = status(), 200
            if self.path == "/health":
                for data in result["profiles"].values():
                    data.pop("log", None)
                result.pop("nft", None)
        self.respond(result, status_code)

    def respond(self, result, status_code):
        body = (json.dumps(result, ensure_ascii=False, sort_keys=True) + "\n").encode()
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def log_message(self, fmt, *args):
        print("HTTP " + fmt % args, flush=True)

def main():
    global table_created
    print("RESULT LAB_SCOPE=" + TARGET + ":443 TCP,UDP ONLY", flush=True)
    print("RESULT ROUTEROS_MUTATIONS=NONE", flush=True)
    if not os.path.isfile(BIN):
        raise RuntimeError("nfqws2 binary missing")
    with open("/proc/sys/net/ipv4/ip_forward", "w") as f:
        f.write("1\n")
    if run("nft", "list", "table", "ip", TABLE).returncode == 0:
        raise RuntimeError("refusing to replace existing nft table")
    try:
        for name, conf in PROFILES.items():
            handles[name] = open(conf["log"], "w", buffering=1)
            cmd = [BIN, "--qnum=" + str(conf["queue"]), "--debug=1", *LUA, *conf["args"]]
            children[name] = subprocess.Popen(cmd, stdout=handles[name], stderr=subprocess.STDOUT,
                                             start_new_session=True, preexec_fn=caps)
        time.sleep(1)
        if not all(p.poll() is None for p in children.values()):
            raise RuntimeError("nfqws2 worker exited during startup")
        if run("nft", "add", "table", "ip", TABLE).returncode:
            raise RuntimeError("nft add table failed")
        table_created = True
        if run("nft", "add", "chain", "ip", TABLE, "forward",
               "{ type filter hook forward priority -100; policy accept; }").returncode:
            raise RuntimeError("nft add chain failed")
        if run("nft", "add", "set", "ip", TABLE, SET,
               "{ type ipv4_addr; }").returncode:
            raise RuntimeError("nft add target set failed")
        if run("nft", "add", "element", "ip", TABLE, SET,
               "{ " + TARGET + " }").returncode:
            raise RuntimeError("nft initial target failed")
        for name, conf in PROFILES.items():
            if run("nft", "add", "rule", "ip", TABLE, "forward",
                   "ip", "daddr", "@"+ SET, name, "dport", "443",
                   "counter", "queue", "num", str(conf["queue"])).returncode:
                raise RuntimeError("nft add rule " + name + " failed")
        print("RESULT COMBINED_READY", flush=True)
        http.server.HTTPServer((HOST, PORT), Handler).serve_forever()
    finally:
        stop_all()

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print("RESULT FATAL=" + repr(exc), flush=True)
        stop_all()
        sys.exit(30)
