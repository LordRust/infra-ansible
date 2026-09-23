"""Exercise the actual role assertions with probe results; never touch disks."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

import yaml

REPO = Path(__file__).resolve().parents[2]


class FilesystemGuards(unittest.TestCase):
    def test_probe_results(self):
        cases = [
            ("existing", 0, "ext4", 0, "data", True),
            ("blank", 2, "", 2, "", True),
            ("wrong type", 0, "xfs", 0, "data", False),
            ("wrong label", 0, "ext4", 0, "other", False),
            ("missing label", 0, "ext4", 2, "", False),
            ("type probe error", 4, "", 2, "", False),
            ("label probe error", 0, "ext4", 4, "", False),
        ]
        for name, type_rc, fs_type, label_rc, label, expected in cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                device = {"device": "/dev/never-accessed", "fstype": "ext4", "label": "data"}
                play = [{
                    "name": "Validate synthetic probe results without device access",
                    "hosts": "localhost",
                    "gather_facts": False,
                    "vars": {
                        "local_filesystem_types": {"results": [
                            {"rc": type_rc, "stdout": fs_type, "item": device}]},
                        "local_filesystem_labels": {"results": [
                            {"rc": label_rc, "stdout": label, "item": device}]},
                    },
                    "tasks": [{"ansible.builtin.import_tasks": str(
                        REPO / "roles/local-filesystem/tasks/validate.yml")}],
                }]
                playbook = Path(tmp) / "guards.yml"
                playbook.write_text(yaml.safe_dump(play))
                env = dict(os.environ, ANSIBLE_LOCAL_TEMP=str(Path(tmp) / "ansible"))
                result = subprocess.run(
                    ["ansible-playbook", "-i", "localhost,", "-c", "local", str(playbook), "--check"],
                    env=env, capture_output=True, text=True, check=False,
                )
                self.assertEqual(result.returncode == 0, expected, result.stdout + result.stderr)
                if not expected:
                    self.assertIn('"evaluated_to": false', result.stdout)


if __name__ == "__main__":
    unittest.main()
