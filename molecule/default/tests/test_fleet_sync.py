"""
=== STARFALL DEFENCE CORPS ACADEMY ===
ARIA Automated Verification — Mission 2.3: Fleet-Wide Operations
================================================================
"""
import os
import re
import subprocess
import yaml
import pytest


def _root_dir():
    tests_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(tests_dir, "..", "..", ".."))


def _workspace_dir():
    return os.path.join(_root_dir(), "workspace")


def _run_cmd(*args, cwd=None, timeout=90):
    return subprocess.run(
        list(args),
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=cwd or _workspace_dir(),
    )


def _run_ansible(*args, cwd=None, timeout=120):
    return _run_cmd(*args, cwd=cwd, timeout=timeout)


def _read_yaml(path):
    try:
        with open(path) as f:
            return yaml.safe_load(f)
    except (FileNotFoundError, yaml.YAMLError):
        return None


def _file_contains(path, pattern):
    """Check if a file contains a regex pattern."""
    try:
        with open(path) as f:
            content = f.read()
        return bool(re.search(pattern, content))
    except FileNotFoundError:
        return False


def _search_yaml_tree(data, key):
    """Recursively search YAML structure for a key."""
    if isinstance(data, dict):
        if key in data:
            return True
        return any(_search_yaml_tree(v, key) for v in data.values())
    if isinstance(data, list):
        return any(_search_yaml_tree(item, key) for item in data)
    return False


# -------------------------------------------------------------------
# Phase 1: Rolling Update Basics
# -------------------------------------------------------------------

class TestRollingUpdate:
    """ARIA verifies: Can the cadet perform a basic rolling deploy?"""

    def test_rolling_playbook_exists(self):
        """rolling-update.yml must exist"""
        path = os.path.join(_workspace_dir(), "rolling-update.yml")
        assert os.path.isfile(path), (
            "ARIA: No rolling-update.yml found. "
            "Write a playbook that deploys to app servers one at a time."
        )

    def test_rolling_uses_serial(self):
        """Playbook must use serial for rolling deploys"""
        path = os.path.join(_workspace_dir(), "rolling-update.yml")
        if not os.path.isfile(path):
            pytest.skip("rolling-update.yml does not exist yet")
        data = _read_yaml(path)
        assert data and isinstance(data, list), (
            "ARIA: rolling-update.yml is empty or invalid."
        )
        has_serial = any(
            isinstance(play, dict) and "serial" in play
            for play in data
        )
        assert has_serial, (
            "ARIA: rolling-update.yml must use 'serial' for rolling deploys. "
            "Add 'serial: 1' at the play level."
        )

    def test_rolling_deploys_content(self):
        """App servers must have updated content after rolling deploy"""
        path = os.path.join(_workspace_dir(), "rolling-update.yml")
        if not os.path.isfile(path):
            pytest.skip("rolling-update.yml does not exist yet")
        # Run the rolling update playbook
        result = _run_ansible(
            "ansible-playbook", "rolling-update.yml",
            cwd=_workspace_dir(),
            timeout=180,
        )
        assert result.returncode == 0, (
            f"ARIA: Rolling update playbook failed:\n{result.stderr[:500]}"
        )
        # Verify at least one app server has updated content
        ssh_key = os.path.join(_workspace_dir(), ".ssh", "cadet_key")
        check = _run_cmd(
            "ssh", "-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null",
            "-i", ssh_key, "cadet@localhost", "-p", "2261",
            "curl", "-s", "http://localhost/",
            timeout=15,
        )
        assert "Version" in check.stdout or "sdc-app" in check.stdout.lower(), (
            "ARIA: App servers don't appear to have updated content. "
            "Deploy templates/index.html.j2 to the nginx document root."
        )

    def test_lb_is_serving(self):
        """Load balancer must still be serving traffic"""
        result = _run_cmd("curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
                         "http://localhost:8080/", timeout=10)
        assert result.stdout.strip() == "200", (
            "ARIA: Load balancer is not serving (HTTP status: {}). "
            "The LB must remain available throughout the deploy."
            .format(result.stdout.strip())
        )


# -------------------------------------------------------------------
# Phase 2: Orchestrated Deployment
# -------------------------------------------------------------------

class TestOrchestration:
    """ARIA verifies: Has the cadet built an orchestrated deploy role?"""

    def test_role_exists(self):
        """fleet_deploy role must exist"""
        role_dir = os.path.join(_workspace_dir(), "roles", "fleet_deploy")
        assert os.path.isdir(role_dir), (
            "ARIA: No role at roles/fleet_deploy/. "
            "Create it with: ansible-galaxy init roles/fleet_deploy"
        )

    def test_role_has_delegation(self):
        """Role must use delegate_to for LB operations"""
        role_dir = os.path.join(_workspace_dir(), "roles", "fleet_deploy")
        if not os.path.isdir(role_dir):
            pytest.skip("Role does not exist yet")
        tasks = os.path.join(role_dir, "tasks", "main.yml")
        assert os.path.isfile(tasks), (
            "ARIA: tasks/main.yml not found in fleet_deploy role."
        )
        assert _file_contains(tasks, r'delegate_to'), (
            "ARIA: Role must use 'delegate_to' for load balancer operations. "
            "Delegate drain/enable commands to sdc-lb."
        )

    def test_site_yml_exists(self):
        """site.yml must call the fleet_deploy role"""
        path = os.path.join(_workspace_dir(), "site.yml")
        assert os.path.isfile(path), (
            "ARIA: site.yml not found. Write a playbook that calls fleet_deploy."
        )
        data = _read_yaml(path)
        assert data and isinstance(data, list), (
            "ARIA: site.yml is empty or invalid."
        )
        content = open(path).read()
        assert "fleet_deploy" in content, (
            "ARIA: site.yml must reference the fleet_deploy role."
        )

    def test_role_has_serial(self):
        """site.yml must use serial for the orchestrated deploy"""
        path = os.path.join(_workspace_dir(), "site.yml")
        if not os.path.isfile(path):
            pytest.skip("site.yml does not exist yet")
        data = _read_yaml(path)
        if not data:
            pytest.skip("site.yml is empty")
        has_serial = any(
            isinstance(play, dict) and "serial" in play
            for play in data
        )
        assert has_serial, (
            "ARIA: site.yml must use 'serial' for orchestrated rolling deploys."
        )

    def test_role_has_health_check(self):
        """Role must include health check tasks"""
        role_dir = os.path.join(_workspace_dir(), "roles", "fleet_deploy")
        if not os.path.isdir(role_dir):
            pytest.skip("Role does not exist yet")
        tasks = os.path.join(role_dir, "tasks", "main.yml")
        if not os.path.isfile(tasks):
            pytest.skip("tasks/main.yml not found")
        has_health = (
            _file_contains(tasks, r'uri') or
            _file_contains(tasks, r'curl') or
            _file_contains(tasks, r'wait_for') or
            _file_contains(tasks, r'health')
        )
        assert has_health, (
            "ARIA: Role should include health check tasks. "
            "Use ansible.builtin.uri, curl, or wait_for to verify server health."
        )


# -------------------------------------------------------------------
# Phase 3: Failure Handling
# -------------------------------------------------------------------

class TestFailureHandling:
    """ARIA verifies: Does the deployment handle failures gracefully?"""

    def test_role_has_block_rescue(self):
        """Role must use block/rescue/always for error handling"""
        role_dir = os.path.join(_workspace_dir(), "roles", "fleet_deploy")
        if not os.path.isdir(role_dir):
            pytest.skip("Role does not exist yet")
        tasks = os.path.join(role_dir, "tasks", "main.yml")
        if not os.path.isfile(tasks):
            pytest.skip("tasks/main.yml not found")
        has_block = _file_contains(tasks, r'\bblock\b')
        has_rescue = _file_contains(tasks, r'\brescue\b')
        assert has_block and has_rescue, (
            "ARIA: Role must use block/rescue for error handling. "
            "Wrap the deploy tasks in a block with a rescue for failure recovery."
        )

    def test_role_has_max_fail(self):
        """Playbook must use max_fail_percentage"""
        path = os.path.join(_workspace_dir(), "site.yml")
        if not os.path.isfile(path):
            pytest.skip("site.yml does not exist yet")
        assert _file_contains(path, r'max_fail_percentage'), (
            "ARIA: site.yml must set max_fail_percentage to allow "
            "the deployment to continue when one server fails."
        )

    def test_deployment_handles_failure(self):
        """Deployment must handle the app-4 failure gracefully"""
        role_dir = os.path.join(_workspace_dir(), "roles", "fleet_deploy")
        if not os.path.isdir(role_dir):
            pytest.skip("Role does not exist yet")
        path = os.path.join(_workspace_dir(), "site.yml")
        if not os.path.isfile(path):
            pytest.skip("site.yml does not exist yet")
        # Run the deployment — it should succeed even though app-4 will fail
        result = _run_ansible(
            "ansible-playbook", "site.yml",
            cwd=_workspace_dir(),
            timeout=240,
        )
        # The playbook should complete (exit 0) despite app-4 failure
        # because max_fail_percentage allows it
        assert result.returncode == 0, (
            "ARIA: Deployment failed completely. With max_fail_percentage set, "
            "the deployment should continue even when one server fails. "
            f"Output:\n{result.stdout[-500:]}"
        )

    def test_healthy_servers_still_serving(self):
        """Healthy app servers must still serve traffic after deployment"""
        result = _run_cmd("curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
                         "http://localhost:8080/", timeout=10)
        assert result.stdout.strip() == "200", (
            "ARIA: Load balancer is not serving after deployment. "
            "Healthy servers must remain in the pool."
        )
