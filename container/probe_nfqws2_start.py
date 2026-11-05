#!/usr/bin/env python3
"""Bounded nfqws2 startup probe. No packet rules or traffic changes."""
import os
import subprocess
import sys
import time

BIN = "/usr/local/bin/nfqws2"
QUEUE = "49154"
print("=== nfqws2 startup-only probe; no nft/iptables rules ===", flush=True)
print("RESULT BINARY_EXISTS=%s" % os.path.isfile(BIN), flush=True)
if not os.path.isfile(BIN):
    sys.exit(20)
try:
    help_run = subprocess.run([BIN, "--version"], stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, timeout=5, text=True, errors="replace")
    print("RESULT NFQWS2_VERSION_RC=%s" % help_run.returncode, flush=True)
    for line in help_run.stdout.splitlines()[:30]:
        print("VERSION " + line[:220], flush=True)
except Exception as exc:
    print("RESULT HELP_ERROR=%r" % exc, flush=True)
    sys.exit(21)

# Linux root exec gets capabilities from bounding set. Remove just SETUID/SETGID
# in the child before exec: upstream can_drop_root() then stays false.
PR_CAPBSET_DROP = 24
CAP_SETGID = 6
CAP_SETUID = 7

def limit_child_caps():
    libc = ctypes.CDLL(None, use_errno=True)
    for cap in (CAP_SETGID, CAP_SETUID):
        if libc.prctl(PR_CAPBSET_DROP, cap, 0, 0, 0) != 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))

cmd = [BIN, "--qnum=" + QUEUE, "--debug=1"]
print("RESULT START_COMMAND=" + " ".join(cmd), flush=True)
print("RESULT CHILD_BOUNDING_CAPS_DROP=CAP_SETUID,CAP_SETGID", flush=True)
try:
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, errors="replace", start_new_session=True,
                            preexec_fn=limit_child_caps)
except Exception as exc:
    print("RESULT START_ERROR=%r" % exc, flush=True)
    sys.exit(22)
try:
    time.sleep(2)
    rc = proc.poll()
    if rc is None:
        print("RESULT NFQWS2_RUNNING_AFTER_2S", flush=True)
    else:
        print("RESULT NFQWS2_EARLY_EXIT_RC=%s" % rc, flush=True)
finally:
    if proc.poll() is None:
        proc.terminate()
    try:
        output, _ = proc.communicate(timeout=3)
    except subprocess.TimeoutExpired:
        proc.kill()
        output, _ = proc.communicate(timeout=3)
    for line in output.splitlines()[-45:]:
        print("NFQWS2 " + line[:300], flush=True)
    print("RESULT NFQWS2_PROCESS_STOPPED", flush=True)
if rc is not None:
    sys.exit(23)
print("RESULT STARTUP_PROBE_SUCCESS", flush=True)
