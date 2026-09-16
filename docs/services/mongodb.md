# MongoDB

## Environment model

MongoDB is treated as a dedicated server function rather than as part of the generic development-host role.

Current test host:

```text
mongodb01
10.10.10.12
VMID 202
```

It is cloned from the Debian 12 cloud-init template.

Production MongoDB will reside on dedicated database machines.

## Inventory

Example:

```ini
[mongodb]
mongodb01 ansible_host=10.10.10.12
```

Keep MongoDB-specific variables under:

```text
group_vars/mongodb/
```

and implementation under:

```text
roles/mongodb/
```

## Playbook

Use a dedicated playbook rather than adding MongoDB to `dev-base.yml`.

Example:

```yaml
- name: Configure MongoDB servers
  hosts: mongodb
  become: true

  roles:
    - base
    - mongodb
```

Run with:

```bash
ansible-playbook -i inventory.ini mongodb.yml
```

## Installation policy

Use MongoDB's official repository/packages for supported guest operating systems rather than an unrelated distribution package.

Before changing the MongoDB guest OS version, verify current MongoDB vendor support for that Debian/Ubuntu release.

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
