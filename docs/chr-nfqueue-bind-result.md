# NFQUEUE registration result — 2026-11-05

User-tested on MikroTik CHR RouterOS 7.24.6, kernel `5.6.3-64`, container `mikrotik-zapret2-nfqueue-probe`.

Log:

```
=== NFQUEUE bind-only probe; NO firewall changes, NO traffic redirect ===
library=libnetfilter_queue.so.1; queue=49152
RESULT NFQ_QUEUE_BIND_OK (kernel accepted queue registration only)
RESULT NFQ_QUEUE_RELEASED
*** exited with status 0
```

The Docker v2s2 image was imported and executed successfully. Queue 49152 was created and destroyed. This confirms that libnetfilter_queue can register a queue with the CHR kernel from a container. **It does not confirm** that iptables/nftables queue rules can be installed or that any packets traverse the queue. The next test should first inspect netfilter support read-only and only then use a dedicated isolated network namespace with cleanup to test packet interception; no production RouterOS firewall changes.
