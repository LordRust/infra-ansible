# MongoDB

## Environment model

MongoDB is treated as a dedicated server function rather than as part of the generic development-host role.

Current test host:

```text
mongodb01
10.10.10.32
VMID 501
```

It is cloned from the Debian 12 cloud-init template.

The database is reached directly by other VMs on `vmbr1`; no Proxmox DNAT rule
is required for MongoDB traffic between the private VMs.

## Inventory

```ini
[dbhosts]
mongodb01 ansible_host=10.10.10.32
```

MongoDB-specific per-host settings belong under `host_vars/`, and the
implementation belongs under:

```text
roles/mongodb/
```

## Playbook

Use the dedicated database playbook:

```bash
ansible-playbook -i inventory.ini db-base.yml
```

The playbook applies both the generic `base` role and the `mongodb` role.

## Installation policy

Use MongoDB's official repository/packages for supported guest operating
systems rather than an unrelated distribution package.

The current role installs MongoDB 8.0 on Debian 12 (`bookworm`) and binds it to
loopback plus the host's private address.

Authentication is enabled by default in the role. The development-only
`mongodb01` host deliberately overrides this in `host_vars/mongodb01.yml`:

```yaml
mongodb_authorization: disabled
```

Do not use that override for production database hosts.

## Production-oriented variables

Keep service/environment choices outside the reusable role where practical, for example:

- bind addresses
- data path
- replica-set name
- authentication configuration
- backup configuration
- resource tuning

That allows the same role to be used for the test VM and later dedicated production database hosts.

## Storage

For larger or production-like deployments, prefer a separate virtual data disk rather than growing the generic root filesystem unnecessarily.
