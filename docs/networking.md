# Networking

## Bridges

`vmbr0` is the external bridge.

`vmbr1` is an isolated private bridge used by test VMs:

```ini
auto vmbr1
iface vmbr1 inet static
        address 10.10.10.1/24
        bridge-ports none
        bridge-stp off
        bridge-fd 0
```

## Outbound NAT

IPv4 forwarding and source NAT are configured as `vmbr1` interface hooks in `/etc/network/interfaces`.

Current pattern:

```ini
# NAT
post-up   echo 1 > /proc/sys/net/ipv4/ip_forward
post-up   iptables -t nat -C POSTROUTING -s 10.10.10.0/24 -o vmbr0 -j MASQUERADE || iptables -t nat -A POSTROUTING -s 10.10.10.0/24 -o vmbr0 -j MASQUERADE
post-down iptables -t nat -D POSTROUTING -s 10.10.10.0/24 -o vmbr0 -j MASQUERADE || true
```

This single rule covers all guests in `10.10.10.0/24`.

Externally, VM traffic therefore appears to originate from the Proxmox host address `10.231.229.23`.

## Inbound SSH forwarding

Each externally reachable guest requires a DNAT rule plus a matching forwarding rule.

Example for `infra-admin-01`:

```ini
# infra-admin-01
post-up   iptables -t nat -C PREROUTING -i vmbr0 -p tcp --dport 8801 -j DNAT --to-destination 10.10.10.10:22 || iptables -t nat -A PREROUTING -i vmbr0 -p tcp --dport 8801 -j DNAT --to-destination 10.10.10.10:22
post-down iptables -t nat -D PREROUTING -i vmbr0 -p tcp --dport 8801 -j DNAT --to-destination 10.10.10.10:22 || true

post-up   iptables -C FORWARD -i vmbr0 -p tcp -d 10.10.10.10 --dport 22 -j ACCEPT || iptables -A FORWARD -i vmbr0 -p tcp -d 10.10.10.10 --dport 22 -j ACCEPT
post-down iptables -D FORWARD -i vmbr0 -p tcp -d 10.10.10.10 --dport 22 -j ACCEPT || true
```

Example for `devvm01`:

```ini
# devvm01
post-up   iptables -t nat -C PREROUTING -i vmbr0 -p tcp --dport 8802 -j DNAT --to-destination 10.10.10.11:22 || iptables -t nat -A PREROUTING -i vmbr0 -p tcp --dport 8802 -j DNAT --to-destination 10.10.10.11:22
post-down iptables -t nat -D PREROUTING -i vmbr0 -p tcp --dport 8802 -j DNAT --to-destination 10.10.10.11:22 || true

post-up   iptables -C FORWARD -i vmbr0 -p tcp -d 10.10.10.11 --dport 22 -j ACCEPT || iptables -A FORWARD -i vmbr0 -p tcp -d 10.10.10.11 --dport 22 -j ACCEPT
post-down iptables -D FORWARD -i vmbr0 -p tcp -d 10.10.10.11 --dport 22 -j ACCEPT || true
```

The explicit FORWARD rules above are for inbound DNAT traffic. They are not per-VM outbound NAT rules.

## DNS

Use:

```text
10.212.226.10
10.212.226.11
```

Do not use `10.10.10.1` as a DNS server unless a resolver is explicitly installed there.

Current private test VMs have no DNS search domain.

Production machines are expected to be registered under `lund.skane.se`.

## Testing connectivity

Because external ICMP may be filtered, do not use Internet ping as the sole outbound connectivity test.

Useful checks inside a guest:

```bash
ip -br addr
ip route
ip route get 1.1.1.1

ping -c 2 10.10.10.1
getent hosts deb.debian.org
wget -S --spider https://deb.debian.org/
```

Useful checks on Proxmox:

```bash
iptables -t nat -L POSTROUTING -nv
iptables -L FORWARD -nv
```
