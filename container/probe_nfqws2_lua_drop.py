#!/usr/bin/env python3
"""Safely test custom Lua invocation via local UDP -> NFQUEUE -> nfqws2 -> receiver.
Lab-only, one-shot, no RouterOS or VETH configuration changes.
"""
import ctypes
import os
import select
import signal
import socket
import subprocess
import sys
import time

BIN = "/usr/local/bin/nfqws2"
TABLE = "zapret2_lua_drop_probe"
PORT = 49324
QUEUE = 49157
PAYLOAD = b"zapret2-lua-drop-probe"
LUA = "/usr/local/share/zapret2/probe_drop.lua"
MARKER = "ZAPRET2_LUA_DROP_INVOKED"
PR_CAPBSET_DROP = 24
CAP_SETGID = 6
CAP_SETUID = 7

def run(*args):
    try:
        p = subprocess.run(args, capture_output=True, text=True, timeout=5)
    except Exception as exc:
        print(f"RESULT CMD_ERROR={type(exc).__name__}: {exc}", flush=True)
        return False
    print(f"CMD {' '.join(args)} rc={p.returncode}", flush=True)
    if p.stdout.strip():
        for line in p.stdout.splitlines():
            print("STDOUT " + line[:350], flush=True)
    if p.stderr.strip():
        for line in p.stderr.splitlines():
            print("STDERR " + line[:350], flush=True)
    return p.returncode == 0

def limit_child_caps():
    libc = ctypes.CDLL(None, use_errno=True)
    libc.prctl.argtypes = [ctypes.c_int, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong]
    libc.prctl.restype = ctypes.c_int
    for cap in (CAP_SETGID, CAP_SETUID):
        if libc.prctl(PR_CAPBSET_DROP, cap, 0, 0, 0) != 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))

def report_process(proc):
    if proc is None:
        return
    print(f"RESULT NFQWS2_EXIT_RC={proc.poll()}", flush=True)

def main():
    print("=== native nfqws2 Lua DROP local UDP probe ===", flush=True)
    print("RESULT ISOLATION=loopback-only, no RouterOS firewall/VETH changes", flush=True)
    if not os.path.isfile(BIN):
        print("RESULT NFQWS2_MISSING", flush=True)
        return 20

    # Refuse to touch an existing table that did not originate with this run.
    if run("nft", "list", "table", "ip", TABLE):
        print("RESULT TABLE_ALREADY_EXISTS_ABORT", flush=True)
        return 21

    proc = None
    receiver = None
    sender = None
    table_created = False
    result = 29
    marker_seen = False
    drop_seen = False
    counter_seen = False
    try:
        receiver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        receiver.bind(("127.0.0.1", PORT))
        receiver.setblocking(False)
        sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        cmd = [BIN, f"--qnum={QUEUE}", "--debug=1",
               f"--lua-init=@{LUA}", "--lua-desync=zapret2_probe_drop"]
        print("RESULT NFQWS2_START=" + " ".join(cmd), flush=True)
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, errors="replace", start_new_session=True,
                                preexec_fn=limit_child_caps)
        time.sleep(1)
        if proc.poll() is not None:
            print(f"RESULT NFQWS2_EARLY_EXIT_RC={proc.returncode}", flush=True)
            result = 22
        elif not run("nft", "add", "table", "ip", TABLE):
            result = 23
        else:
            table_created = True
            if not run("nft", "add", "chain", "ip", TABLE, "out",
                       "{ type filter hook output priority -100; policy accept; }"):
                result = 24
            elif not run("nft", "add", "rule", "ip", TABLE, "out",
                         "ip", "daddr", "127.0.0.1", "udp", "dport", str(PORT),
                         "counter", "queue", "num", str(QUEUE)):
                result = 25
            else:
                sent = sender.sendto(PAYLOAD, ("127.0.0.1", PORT))
                print(f"RESULT UDP_SEND_RETURNED={sent}", flush=True)
                readable, _, _ = select.select([receiver], [], [], 3)
                if readable:
                    packet, peer = receiver.recvfrom(2048)
                    print(f"RESULT UNEXPECTED_UDP_RECEIVED={len(packet)} FROM={peer}", flush=True)
                    result = 26
                else:
                    print("RESULT UDP_NOT_DELIVERED_AS_EXPECTED", flush=True)
                    result = 0
                # Counter is useful but absence of delivery alone does not prove Lua DROP.
                counter = subprocess.run(["nft", "-a", "list", "chain", "ip", TABLE, "out"],
                                         capture_output=True, text=True, timeout=5)
                print(f"RESULT NFT_COUNTER_QUERY_RC={counter.returncode}", flush=True)
                for line in counter.stdout.splitlines():
                    print("NFT " + line[:350], flush=True)
                    if "counter packets 1 " in line and f"queue to {QUEUE}" in line:
                        counter_seen = True
                print(f"RESULT QUEUED_ONE_PACKET={counter_seen}", flush=True)
                if result == 0 and not counter_seen:
                    result = 32
                if proc.poll() is not None:
                    print(f"RESULT NFQWS2_EXITED_DURING_TEST={proc.returncode}", flush=True)
                    if result == 0:
                        result = 28
    except Exception as exc:
        print(f"RESULT PROBE_ERROR={type(exc).__name__}: {exc}", flush=True)
        result = 29
    finally:
        # Delete narrow rule before terminating nfqws2 to avoid queued packets.
        if table_created:
            if not run("nft", "delete", "table", "ip", TABLE):
                print("RESULT WARNING_TABLE_CLEANUP_FAILED", flush=True)
                result = 30
        if proc is not None:
            if proc.poll() is None:
                proc.terminate()
            try:
                output, _ = proc.communicate(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
                output, _ = proc.communicate(timeout=3)
            marker_seen = MARKER in output
            drop_seen = "packet: id=1 drop" in output
            for line in output.splitlines()[-100:]:
                print("NFQWS2 " + line[:350], flush=True)
            print(f"RESULT NFQWS2_FINAL_RC={proc.returncode}", flush=True)
            print(f"RESULT LUA_FUNCTION_INVOKED={marker_seen}", flush=True)
            print(f"RESULT NFQWS2_DROP_VERDICT_LOGGED={drop_seen}", flush=True)
            if result == 0 and not marker_seen:
                result = 31
            if result == 0 and not drop_seen:
                result = 33
        if sender is not None:
            sender.close()
        if receiver is not None:
            receiver.close()

    if result == 0:
        print("RESULT NATIVE_NFQWS2_LUA_DROP_TEST_SUCCESS", flush=True)
    else:
        print(f"RESULT NATIVE_NFQWS2_LUA_DROP_TEST_FAILED code={result}", flush=True)
    return result

if __name__ == "__main__":
    sys.exit(main())
