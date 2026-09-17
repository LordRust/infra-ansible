# Proxmox host

## Host overview

Host: `mtcmdpgm02`

External network:

```text
vmbr0
10.231.229.23/24
gateway 10.231.229.1
```

Private VM network:

```text
vmbr1
10.10.10.1/24
```

## Guest access

VMs are normally administered over their private addresses from `infra-admin-01`.

Selected ports are forwarded from the Proxmox host for access from the external/laptop network.

Current SSH mapping:

| Host port | Guest | Guest address | Guest port |
|---:|---|---|---:|
| 8801 | `infra-admin-01` | `10.10.10.10` | 22 |
| 8802 | `dev01` | `10.10.10.101` | 22 |

Add further mappings explicitly as needed.

## Applying bridge hook changes

Ordinary interface configuration changes can normally be processed with `ifreload -a`.

However, arbitrary changed `post-up`/`post-down` iptables commands are not declaratively reconciled by `ifreload`.

To force the `vmbr1` hooks to execute:

```bash
ifup -f vmbr1
```

If the syntax of an existing iptables rule has been changed, remove the old running rule first if necessary. The `-C ... || -A ...` pattern prevents duplicate additions, but it does not remove a differently-shaped old rule.

## Verification

Useful checks:

```bash
ip link show type bridge
ip addr show vmbr1

iptables -t nat -S PREROUTING
iptables -t nat -S POSTROUTING
iptables -S FORWARD
```

`bridge link` lists bridge ports, not bridge devices. A bridge with `bridge-ports none` may therefore not appear in `bridge link`.
