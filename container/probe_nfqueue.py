#!/usr/bin/env python3
"""One-shot, non-traffic NFQUEUE availability probe for an isolated CHR lab."""
import ctypes
import ctypes.util
import os
import sys

QUEUE = 49152  # reserved for this lab; must not be used by other consumers
name = ctypes.util.find_library("netfilter_queue") or "libnetfilter_queue.so.1"
lib = ctypes.CDLL(name, use_errno=True)
lib.nfq_open.restype = ctypes.c_void_p
lib.nfq_close.argtypes = [ctypes.c_void_p]
lib.nfq_close.restype = ctypes.c_int
CALLBACK = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p)
lib.nfq_create_queue.argtypes = [ctypes.c_void_p, ctypes.c_uint16, CALLBACK, ctypes.c_void_p]
lib.nfq_create_queue.restype = ctypes.c_void_p
lib.nfq_destroy_queue.argtypes = [ctypes.c_void_p]
lib.nfq_destroy_queue.restype = ctypes.c_int

@CALLBACK
def callback(_queue, _nfmsg, _packet, _data):
    # No packets should reach this queue: no firewall rules are installed.
    return 0

print("=== NFQUEUE bind-only probe; NO firewall changes, NO traffic redirect ===", flush=True)
print(f"library={name}; queue={QUEUE}", flush=True)
handle = lib.nfq_open()
if not handle:
    err = ctypes.get_errno()
    print(f"RESULT NFQ_OPEN_FAILED errno={err} ({os.strerror(err)})", flush=True)
    sys.exit(10)
try:
    ctypes.set_errno(0)
    queue = lib.nfq_create_queue(handle, QUEUE, callback, None)
    if not queue:
        err = ctypes.get_errno()
        print(f"RESULT NFQ_CREATE_QUEUE_FAILED errno={err} ({os.strerror(err)})", flush=True)
        sys.exit(11)
    try:
        print("RESULT NFQ_QUEUE_BIND_OK (kernel accepted queue registration only)", flush=True)
    finally:
        lib.nfq_destroy_queue(queue)
finally:
    lib.nfq_close(handle)
print("RESULT NFQ_QUEUE_RELEASED", flush=True)
