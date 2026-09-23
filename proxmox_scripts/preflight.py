#!/usr/bin/env python3
"""Read-only checks shared by the small Proxmox provisioning scripts."""
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys


class PreflightError(Exception):
    pass


def require(condition, message):
    if not condition:
        raise PreflightError(message)


def read_command(*args):
    try:
        return subprocess.run(args, text=True, capture_output=True, check=True, timeout=30).stdout
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise PreflightError(f"Inspection failed: {shlex.join(args)}; inspect the host before retrying") from exc


def valid_id(value):
    return bool(re.fullmatch(r"[1-9][0-9]{2,8}", value))


def validate_arguments(kind, template, vmid, octet, name):
    require(kind in ("vm", "lxc"), "Guest type must be vm or lxc")
    require(valid_id(vmid), "VMID must be 100..999999999 without leading zeros")
    require(bool(re.fullmatch(r"[1-9][0-9]{0,2}", octet)) and 2 <= int(octet) <= 254,
            "Address octet must be 2..254; gateway/network/broadcast are reserved")
    require(bool(re.fullmatch(r"[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?", name)),
            "Use a hostname of 1..63 letters, digits or hyphens, with no leading/trailing hyphen")
    if kind == "vm":
        require(valid_id(template), "Template VMID must be 100..999999999")
        require(template != vmid, "Template and destination VMID must differ")
    else:
        require(bool(re.fullmatch(r"[a-zA-Z0-9_.+-]+\.tar\.(?:zst|xz|gz)", template)),
                "LXC template must be a template archive basename")


def check_inventory(inventory, address, name):
    require(inventory.is_file(), f"Inventory missing: {inventory}; copy the whole repository")
    for line in inventory.read_text().splitlines():
        tokens = shlex.split(line, comments=True)
        if not tokens or tokens[0].startswith("[") or "=" in tokens[0]:
            continue
        attrs = dict(token.split("=", 1) for token in tokens[1:] if "=" in token)
        assigned = attrs.get("ansible_host")
        require(assigned != address or tokens[0] == name,
                f"{address} is reserved for {tokens[0]} in inventory")
        require(tokens[0] != name or assigned in (None, address),
                f"{name} has a different inventory address: {assigned}")


def check_resources(resources, vmid, name):
    require(isinstance(resources, list), "Unexpected cluster resource response")
    for guest in resources:
        require(str(guest.get("vmid")) != vmid, f"VMID {vmid} already exists in the cluster")
        require(guest.get("name") != name, f"Guest name {name} already exists in the cluster")


def check_config_addresses(paths, address):
    for path in paths:
        for line in path.read_text().splitlines():
            if re.match(r"(?:ipconfig|net)\d+:", line):
                require(not re.search(r"(?:^|[\s,])ip=" + re.escape(address) + r"(?:/|,|$)", line),
                        f"{address} is already configured in {path}")


def check_storage(storage, content):
    status = read_command("pvesm", "status", "--storage", storage, "--content", content, "--enabled", "1")
    rows = [line.split() for line in status.splitlines() if line.split() and line.split()[0] == storage]
    require(len(rows) == 1 and len(rows[0]) >= 6 and rows[0][2] == "active",
            f"Storage {storage} is not active/enabled for {content}")
    require(int(rows[0][5]) > 0, f"Storage {storage} has no available space")


def preflight(kind, template, vmid, octet, name, key):
    validate_arguments(kind, template, vmid, octet, name)
    require(os.geteuid() == 0, "Run provisioning on the Proxmox host as root")
    commands = ["qm" if kind == "vm" else "pct", "pvesh", "pvesm", "ssh-keygen"]
    if kind == "lxc":
        commands += ["timeout", "sleep"]
    for command in commands:
        require(shutil.which(command) is not None, f"Required command missing: {command}")
    require(Path(key).is_file() and os.access(key, os.R_OK), f"Public key is not readable: {key}")
    read_command("ssh-keygen", "-l", "-f", key)
    require(Path("/sys/class/net/vmbr1/bridge").is_dir(), "Bridge vmbr1 is missing")
    address = f"10.10.10.{octet}"
    check_inventory(Path(__file__).resolve().parents[1] / "inventory.ini", address, name)
    resources = json.loads(read_command("pvesh", "get", "/cluster/resources", "--type", "vm", "--output-format", "json"))
    check_resources(resources, vmid, name)
    node_dir = Path("/etc/pve/nodes")
    require(node_dir.is_dir(), "Proxmox cluster configuration is unavailable")
    paths = [*node_dir.glob("*/qemu-server/*.conf"), *node_dir.glob("*/lxc/*.conf")]
    check_config_addresses(paths, address)
    check_storage("raid-lvm", "images" if kind == "vm" else "rootdir")
    if kind == "vm":
        config = read_command("qm", "config", template)
        require(re.search(r"^template:\s*1\s*$", config, re.M), "Source VM is not a template")
        require(re.search(r"^net0:.*\bbridge=vmbr1(?:,|$)", config, re.M), "Template net0 must use vmbr1")
        require(re.search(r"^(?:ide|scsi|sata)\d+:.*cloudinit", config, re.M), "Template has no cloud-init drive")
    else:
        check_storage("local", "vztmpl")
        archive = read_command("pvesm", "path", f"local:vztmpl/{template}").strip()
        require(Path(archive).is_file(), f"LXC template archive is missing: {archive}")
    print(f"Preflight passed: {kind} {vmid} ({name}), {address}, vmbr1, raid-lvm")
    print("Address checks cover inventory and Proxmox configuration, not manually configured/unmanaged guests.")


if __name__ == "__main__":
    try:
        require(len(sys.argv) == 7, "Internal usage: preflight.py vm|lxc template vmid octet name public-key")
        preflight(*sys.argv[1:])
    except (PreflightError, OSError, ValueError) as error:
        print(f"Preflight failed: {error}", file=sys.stderr)
        sys.exit(1)
