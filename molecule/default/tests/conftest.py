"""
ARIA Custom Test Reporter
Provides color-coded, phase-grouped output for Fleet Sync verification.
"""
import os
import pytest
import sys

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

# The phase-oriented summary is rendered by the shared `aria-reporter`
# pytest plugin (installed via requirements.txt); this file only declares
# the mission's phases + friendly objective names.
from aria_reporter import configure  # noqa: E402

configure(phases=PHASES, friendly=FRIENDLY, mission_id="2-3")
