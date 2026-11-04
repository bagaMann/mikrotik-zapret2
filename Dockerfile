FROM debian:trixie-slim
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    libluajit-5.1-2 libz1 libnetfilter-queue1 libnfnetlink0 libmnl0 \
    ca-certificates iproute2 iptables nftables procps \
 && rm -rf /var/lib/apt/lists/*
COPY out/nfqws2 /usr/local/bin/nfqws2
COPY container/diagnose.sh /usr/local/bin/diagnose
RUN chmod 0755 /usr/local/bin/nfqws2 /usr/local/bin/diagnose
ENTRYPOINT ["/usr/local/bin/diagnose"]
