"""Preflight safety tests; all Proxmox command results are synthetic."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("preflight", REPO / "proxmox_scripts/preflight.py")
pf = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pf)


class ProxmoxPreflight(unittest.TestCase):
    def test_invalid_arguments_never_inspect_or_mutate_host(self):
        for args in [
            ("vm", "102", "102", "201", "smoke"),
            ("vm", "bad", "901", "201", "smoke"),
            ("vm", "102", "0901", "201", "smoke"),
            ("vm", "102", "901", "1", "smoke"),
            ("vm", "102", "901", "255", "smoke"),
            ("vm", "102", "901", "201", "-option"),
            ("lxc", "../../archive.tar.zst", "901", "201", "smoke"),
        ]:
            with self.subTest(args=args), patch.object(pf, "read_command") as command:
                with self.assertRaises(pf.PreflightError):
                    pf.preflight(*args, "/unused/key.pub")
                command.assert_not_called()

    def test_valid_arguments(self):
        pf.validate_arguments("vm", "102", "901", "201", "smoke-fs")
        pf.validate_arguments("lxc", "debian-13-standard_13.6-1_amd64.tar.zst", "902", "202", "smoke-dev")

    def test_shared_id_namespace_and_name_collision(self):
        for resource in [{"type": "lxc", "vmid": 901}, {"type": "qemu", "vmid": 901},
                         {"type": "qemu", "vmid": 903, "name": "smoke-fs"}]:
            with self.subTest(resource=resource), self.assertRaises(pf.PreflightError):
                pf.check_resources([resource], "901", "smoke-fs")
        pf.check_resources([], "901", "smoke-fs")

    def test_inventory_reservations(self):
        with tempfile.TemporaryDirectory() as tmp:
            inventory = Path(tmp) / "inventory.ini"
            inventory.write_text('[fileservers]\nsmoke-fs ansible_host=10.10.10.201 # reserved\n')
            pf.check_inventory(inventory, "10.10.10.201", "smoke-fs")
            pf.check_inventory(inventory, "10.10.10.202", "smoke-dev")
            for address, name in [("10.10.10.201", "wrong"), ("10.10.10.202", "smoke-fs")]:
                with self.subTest(address=address, name=name), self.assertRaises(pf.PreflightError):
                    pf.check_inventory(inventory, address, name)

    def test_vm_and_container_address_collisions(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "901.conf"
            for line in ["ipconfig0: ip=10.10.10.201/24,gw=10.10.10.1",
                         "net0: name=eth0,bridge=vmbr1,ip=10.10.10.201/24"]:
                with self.subTest(line=line):
                    config.write_text(line)
                    with self.assertRaises(pf.PreflightError):
                        pf.check_config_addresses([config], "10.10.10.201")
                    pf.check_config_addresses([config], "10.10.10.20")

    def test_storage_refuses_inactive_or_full(self):
        for row in ["raid-lvm lvmthin inactive 100 0 100 0%", "raid-lvm lvmthin active 100 100 0 100%", ""]:
            with self.subTest(row=row), patch.object(pf, "read_command", return_value=row):
                with self.assertRaises(pf.PreflightError):
                    pf.check_storage("raid-lvm", "images")
        with patch.object(pf, "read_command", return_value="raid-lvm lvmthin active 100 20 80 20%") as command:
            pf.check_storage("raid-lvm", "images")
            self.assertEqual(command.call_args.args[:2], ("pvesm", "status"))


if __name__ == "__main__":
    unittest.main()
