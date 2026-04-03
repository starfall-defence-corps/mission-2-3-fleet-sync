"""
ARIA Custom Test Reporter
Provides color-coded, phase-grouped output for Fleet Sync verification.
"""
import os
import pytest
import sys

_COLOR = (
    os.environ.get("ARIA_COLOR") == "1"
    or (hasattr(sys.stderr, "isatty") and sys.stderr.isatty())
)


def _c(code):
    return code if _COLOR else ""


GREEN = _c("\033[32m")
RED = _c("\033[31m")
YELLOW = _c("\033[33m")
CYAN = _c("\033[36m")
DIM = _c("\033[2m")
BOLD = _c("\033[1m")
RESET = _c("\033[0m")

PHASES = {
    "TestRollingUpdate":     ("1", "Rolling Update Basics"),
    "TestOrchestration":     ("2", "Orchestrated Deployment"),
    "TestFailureHandling":   ("3", "Failure Handling"),
}

FRIENDLY = {
    "test_rolling_playbook_exists":        "rolling-update.yml exists",
    "test_rolling_uses_serial":            "Playbook uses serial",
    "test_rolling_deploys_content":        "App servers have updated content",
    "test_lb_is_serving":                  "Load balancer is serving traffic",
    "test_role_exists":                    "fleet_deploy role exists",
    "test_role_has_delegation":            "Role uses delegate_to",
    "test_site_yml_exists":                "site.yml calls fleet_deploy role",
    "test_role_has_serial":                "Playbook uses serial for orchestration",
    "test_role_has_health_check":          "Role includes health check tasks",
    "test_role_has_block_rescue":          "Role uses block/rescue/always",
    "test_role_has_max_fail":              "Playbook uses max_fail_percentage",
    "test_deployment_handles_failure":     "Deployment handles app-4 failure",
    "test_healthy_servers_still_serving":  "Healthy servers still serve traffic",
}


class _ARIAReporter:
    def __init__(self):
        self._current_class = None
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self._phase_results = {}
        self._current_phase_passed = True

    @staticmethod
    def _out(text):
        sys.stderr.write(text)
        sys.stderr.flush()

    def record(self, nodeid, outcome, longrepr):
        parts = nodeid.split("::")
        cls = parts[1] if len(parts) > 1 else ""
        test = parts[-1]

        num, label = PHASES.get(cls, ("?", "Unknown"))
        name = FRIENDLY.get(test, test)

        if cls != self._current_class:
            if self._current_class is not None:
                self._phase_results[self._current_class] = self._current_phase_passed
            self._current_phase_passed = True
            self._current_class = cls
            self._out(f"\n  {CYAN}{BOLD}Phase {num}: {label}{RESET}\n")

        if outcome != "passed":
            self._current_phase_passed = False

        if outcome == "passed":
            self.passed += 1
            self._out(f"    {GREEN}\u2713{RESET} {name}\n")
        elif outcome == "skipped":
            self.skipped += 1
            self._out(f"    {YELLOW}\u25cb{RESET} {DIM}{name} \u2014 skipped{RESET}\n")
        else:
            self.failed += 1
            hint = _extract_hint(longrepr)
            if hint:
                self._out(f"    {YELLOW}\u2717{RESET} {name}\n")
                self._out(f"      {DIM}\u21b3 {hint}{RESET}\n")
            else:
                self._out(f"    {RED}\u2717{RESET} {name}\n")

    def summary(self):
        if self._current_class is not None:
            self._phase_results[self._current_class] = self._current_phase_passed

        total = self.passed + self.failed + self.skipped
        self._out(f"\n  {'\u2500' * 44}\n")

        phases_complete = sum(1 for v in self._phase_results.values() if v)
        total_phases = len(PHASES)
        self._out(f"  {BOLD}Progress:{RESET} {phases_complete} of {total_phases} phases complete\n")

        parts = []
        if self.passed:
            parts.append(f"{GREEN}{self.passed} verified{RESET}")
        if self.failed:
            parts.append(f"{RED}{self.failed} deficient{RESET}")
        if self.skipped:
            parts.append(f"{YELLOW}{self.skipped} skipped{RESET}")
        self._out(
            f"  {BOLD}Results:{RESET} {' \u00b7 '.join(parts)}"
            f"  {DIM}({total} checks){RESET}\n"
        )


def _extract_hint(longrepr):
    if longrepr is None:
        return None
    crash = getattr(longrepr, "reprcrash", None)
    if crash:
        msg = getattr(crash, "message", "")
        if "ARIA:" in msg:
            return msg.split("ARIA:", 1)[-1].strip()
    text = str(longrepr)
    if "ARIA:" in text:
        raw = text.split("ARIA:")[-1].splitlines()[0].strip()
        return raw.rstrip("'\"")
    return None


_reporter = _ARIAReporter()


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_logreport(report):
    if report.when == "call":
        _reporter.record(report.nodeid, report.outcome, report.longrepr)
        report.longrepr = None
    elif report.when == "setup" and report.skipped:
        _reporter.record(report.nodeid, "skipped", report.longrepr)
        report.longrepr = None


def pytest_report_teststatus(report, config):
    if report.when == "call":
        return report.outcome, "", ""
    if report.when == "setup" and report.skipped:
        return "skipped", "", ""


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    _reporter.summary()
    terminalreporter.stats.pop("failed", None)
    terminalreporter.stats.pop("error", None)
