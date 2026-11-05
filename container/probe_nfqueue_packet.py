#!/usr/bin/env python3
"""Bounded loopback UDP -> nft queue -> NFQUEUE verdict test. Lab only."""
import ctypes as C
import os
import select
import socket
import subprocess
import sys
import time

TABLE = "zapret2_probe"
PORT = 49321
QUEUE = 49153

def run(*args):
    p = subprocess.run(args, text=True, capture_output=True, timeout=5)
    print("CMD", " ".join(args), "rc", p.returncode, flush=True)
    if p.stdout.strip(): print("STDOUT", p.stdout.strip(), flush=True)
    if p.stderr.strip(): print("STDERR", p.stderr.strip(), flush=True)
    return p.returncode == 0

def cleanup():
    run("nft", "delete", "table", "ip", TABLE)

lib = C.CDLL("libnetfilter_queue.so.1", use_errno=True)
ptr = C.c_void_p
lib.nfq_open.restype = ptr
lib.nfq_close.argtypes = [ptr]
lib.nfq_create_queue.restype = ptr
CB = C.CFUNCTYPE(C.c_int, ptr, ptr, ptr, ptr)
lib.nfq_create_queue.argtypes = [ptr, C.c_uint16, CB, ptr]
lib.nfq_destroy_queue.argtypes = [ptr]
lib.nfq_set_mode.argtypes = [ptr, C.c_uint8, C.c_uint32]
lib.nfq_set_mode.restype = C.c_int
lib.nfq_fd.argtypes = [ptr]
lib.nfq_fd.restype = C.c_int
lib.nfq_handle_packet.argtypes = [ptr, ptr, C.c_int]
lib.nfq_get_msg_packet_hdr.argtypes = [ptr]
lib.nfq_get_msg_packet_hdr.restype = ptr
lib.nfq_set_verdict.argtypes = [ptr, C.c_uint32, C.c_uint32, C.c_uint32, ptr]
lib.nfq_set_verdict.restype = C.c_int

class Header(C.Structure):
    _pack_ = 1
    _fields_ = [("packet_id", C.c_uint32), ("hw_protocol", C.c_uint16), ("hook", C.c_uint8)]

seen = [0]
@CB
def cb(qh, _msg, pkt, _ctx):
    header = lib.nfq_get_msg_packet_hdr(pkt)
    if not header:
        print("RESULT PACKET_HEADER_MISSING", flush=True)
        return -1
    packet_id = socket.ntohl(C.cast(header, C.POINTER(Header)).contents.packet_id)
    seen[0] += 1
    print("RESULT NFQUEUE_PACKET_RECEIVED id=%s" % packet_id, flush=True)
    return lib.nfq_set_verdict(qh, packet_id, 1, 0, None)

print("=== isolated loopback NFQUEUE test ===", flush=True)
print("No RouterOS firewall or VETH rules changed", flush=True)
# Fail closed on stale test table: never delete an unknown table.
if not run("nft", "add", "table", "ip", TABLE):
    print("RESULT NFT_TABLE_CREATE_FAILED", flush=True)
    sys.exit(20)
handle = None
queue = None
try:
    if not run("nft", "add", "chain", "ip", TABLE, "out", "{ type filter hook output priority -100; policy accept; }"):
        print("RESULT NFT_CHAIN_CREATE_FAILED", flush=True)
        sys.exit(21)
    if not run("nft", "add", "rule", "ip", TABLE, "out", "ip", "daddr", "127.0.0.1", "udp", "dport", str(PORT), "counter", "queue", "num", str(QUEUE)):
        print("RESULT NFT_QUEUE_RULE_FAILED", flush=True)
        sys.exit(22)
    handle = lib.nfq_open()
    if not handle:
        print("RESULT NFQ_OPEN_FAILED errno=%d" % C.get_errno(), flush=True)
        sys.exit(23)
    queue = lib.nfq_create_queue(handle, QUEUE, cb, None)
    if not queue:
        print("RESULT NFQ_BIND_FAILED errno=%d" % C.get_errno(), flush=True)
        sys.exit(24)
    mode_rc = lib.nfq_set_mode(queue, 2, 65535)
    print(f"RESULT NFQ_SET_COPY_PACKET_MODE_RC={mode_rc} errno={C.get_errno()}", flush=True)
    if mode_rc < 0:
        sys.exit(27)
    receiver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    receiver.bind(("127.0.0.1", PORT))
    receiver.setblocking(False)
    sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    print("RESULT UDP_SEND_BEGIN", flush=True)
    sent = sender.sendto(b"zapret2-nfq-probe", ("127.0.0.1", PORT))
    print(f"RESULT UDP_SEND_RETURNED bytes={sent}", flush=True)
    fd = lib.nfq_fd(handle)
    print(f"RESULT NFQ_FD={fd}", flush=True)
    try:
        with open("/proc/net/netfilter/nfnetlink_queue", encoding="ascii") as q:
            print("RESULT KERNEL_NFQUEUE_STATE=" + repr(q.read().strip()), flush=True)
    except OSError as e:
        print(f"RESULT KERNEL_NFQUEUE_STATE_ERROR={e}", flush=True)
    print("RESULT NFT_RULE_BEFORE_WAIT", flush=True)
    run("nft", "-a", "list", "chain", "ip", TABLE, "out")
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline and not seen[0]:
        ready, _, _ = select.select([fd], [], [], max(0, deadline - time.monotonic()))
        if ready:
            print("RESULT NFQ_FD_READABLE", flush=True)
            buf = os.read(fd, 65535)
            print(f"RESULT NFQ_NETLINK_BYTES={len(buf)}", flush=True)
            data = C.create_string_buffer(buf)
            lib.nfq_handle_packet(handle, data, len(buf))
    if not seen[0]:
        print("=== nft rule and counters at timeout ===", flush=True)
        run("nft", "-a", "list", "chain", "ip", TABLE, "out")
        ready, _, _ = select.select([receiver], [], [], 0)
        print(f"RESULT RECEIVER_READABLE={bool(ready)}", flush=True)
        try:
            with open("/proc/net/netfilter/nfnetlink_queue", encoding="ascii") as q:
                print("RESULT KERNEL_NFQUEUE_STATE_TIMEOUT=" + repr(q.read().strip()), flush=True)
        except OSError as e:
            print(f"RESULT KERNEL_NFQUEUE_STATE_ERROR={e}", flush=True)
        print("RESULT NFQUEUE_PACKET_TIMEOUT", flush=True)
        sys.exit(25)
    ready, _, _ = select.select([receiver], [], [], 2)
    if ready and receiver.recv(4096) == b"zapret2-nfq-probe":
        print("RESULT LOOPBACK_PACKET_ACCEPTED", flush=True)
    else:
        print("RESULT LOOPBACK_DELIVERY_FAILED", flush=True)
        sys.exit(26)
finally:
    if queue: lib.nfq_destroy_queue(queue)
    if handle: lib.nfq_close(handle)
    cleanup()
print("RESULT TEST_SUCCESS", flush=True)
