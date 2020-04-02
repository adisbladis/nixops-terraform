from typing import Optional, Dict, List, Generator, Callable
from contextlib import contextmanager
import nixops.resources
import subprocess
import tempfile
import os.path
import json
import sys


def write_stderr(msg: str) -> None:
    sys.stderr.write(msg + "\n")
    sys.stderr.flush()


@contextmanager
def tf_state_file(
    tf_state: Dict, callback: Callable[[Dict], None]
) -> Generator[str, None, None]:
    # TODO: Either create directory or also unlink backup file
    with tempfile.NamedTemporaryFile(
        prefix="nixops-tf-state-", suffix=".json", mode="w"
    ) as statefile:
        if tf_state:
            json.dump(tf_state, statefile, indent=2)
        statefile.seek(0)

        yield statefile.name

        with open(statefile.name) as f:
            state = json.load(f)
            callback(state)


class TerraformResourceDefinition(nixops.resources.ResourceDefinition):
    """Definition of terraform resources"""

    terraform_resources: Optional[Dict]

    @classmethod
    def get_type(cls):
        return "terraform"

    @classmethod
    def get_resource_type(cls):
        return "terraform"

    def __init__(self, name: str, config: Dict):
        super().__init__(name, config)
        # Drop all other attrs
        self.terraform_resources = {"resource": config["resource"]}

    def show_type(self):
        return "Terraform Resources"


class TerraformState(nixops.resources.ResourceState):

    _tf_temp_dir: tempfile.TemporaryDirectory

    tf_config = nixops.util.attr_property("tf.config", {}, "json")
    tf_state = nixops.util.attr_property("tf.state", {}, "json")

    def __init__(self, *args, **kwargs):
        self._tf_temp_dir = tempfile.TemporaryDirectory(prefix="nixops-tf-")
        super().__init__(*args, **kwargs)
        self._init_tf()
        self._dump_tf_config()

    @classmethod
    def get_type(cls):
        return "terraform"

    # TODO: Make ResourceState a context manager
    def __del__(self):
        temp_dir = self._tf_temp_dir
        if temp_dir:
            temp_dir.cleanup()

    def _init_tf(self):
        self._run_tf_command("init")
        # stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def _dump_tf_config(self):
        """Dump current terraform config to file in temp directory"""
        with open(os.path.join(self._tf_temp_dir.name, "config.tf.json"), "w") as f:
            json.dump(self.tf_config, f, indent=2)

        subprocess.run(["cat", os.path.join(self._tf_temp_dir.name, "config.tf.json")])

        self._init_tf()  # Re-init post reconfiguration

    def _run_tf_command(
        self, action: str, flags: Optional[Dict[str, Optional[str]]] = None, **kwargs
    ) -> None:
        command: List[str] = ["terraform", action]
        for k, v in (flags or {}).items():
            command.append("-" + k)
            if v is not None and v:
                command.append(v)
        subprocess.run(command, check=True, cwd=self._tf_temp_dir.name, **kwargs)

    def _refresh_state(self, state: Dict) -> None:
        self.tf_state = state

    def create(self, defn, check: bool, allow_reboot: bool, allow_recreate: bool):
        if not allow_recreate:
            write_stderr(
                "allow_recreate is False, but terraform implies allow_recreate"
            )
        if not allow_reboot:
            write_stderr("allow_reboot is False, but terraform implies allow_reboot")

        self.tf_config = defn.terraform_resources
        self._dump_tf_config()

        with tf_state_file(self.tf_state, self._refresh_state) as statefile:
            self._run_tf_command("apply", {"auto-approve": None, "state": statefile})

    def destroy(self, wipe: bool = False):
        with tf_state_file(self.tf_state, self._refresh_state) as statefile:
            self._run_tf_command("destroy", {"auto-approve": None, "state": statefile})
