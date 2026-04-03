---
CLASSIFICATION: LIEUTENANT EYES ONLY
MISSION: 2.3 — FLEET-WIDE OPERATIONS
THEATRE: Starfall Defence Corps Academy
AUTHORITY: SDC Cyber Command, 2187
---

# MISSION 2.3 — FLEET-WIDE OPERATIONS

---

## 1. SITUATION

### 1a. The Problem

The fleet runs 4 application servers behind a load balancer. A critical update must be deployed to all 4 servers. The update changes the application configuration and restarts nginx.

If you deploy to all 4 at once, the fleet goes dark. Zero availability. Unacceptable.

If one server fails mid-deploy, the old approach was: abort everything, page the on-call team, spend 3 hours rolling back manually.

You will do better.

### 1b. Fleet Topology

```
                  ┌──────────────┐
                  │   sdc-lb     │
                  │  HAProxy     │
                  │  :8080 (LB)  │
                  │  :8404 (stats)│
                  │  :2265 (SSH) │
                  └──────┬───────┘
            ┌────────────┼────────────┐────────────┐
            ▼            ▼            ▼            ▼
     ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐
     │ sdc-app-1  │ │ sdc-app-2  │ │ sdc-app-3  │ │ sdc-app-4  │
     │ :2261 SSH  │ │ :2262 SSH  │ │ :2263 SSH  │ │ :2264 SSH  │
     │ nginx :80  │ │ nginx :80  │ │ nginx :80  │ │ nginx :80  │
     └────────────┘ └────────────┘ └────────────┘ └────────────┘

     ┌────────────┐
     │ sdc-monitor│
     │ :2266 SSH  │
     │ Rocky Linux│
     └────────────┘
```

**SSH user**: `cadet` (key-based auth, key at `.ssh/cadet_key`)

**Load balancer**: HAProxy at `http://localhost:8080`. Stats at `http://localhost:8404/stats`.

**Monitor node**: Rocky Linux 9. Use it for `run_once` tasks (pre-deploy checks, post-deploy reports).

### 1c. Intelligence

- All 4 app servers run nginx with a default page
- HAProxy health-checks each server every 2 seconds
- **sdc-app-4 has a planted issue**: a flag file at `/etc/nginx/conf.d/broken.flag` that will cause your deployment to fail if your role checks for it (simulating a real-world failure)
- The load balancer stats page shows real-time server status

---

## 2. MISSION

Deploy a rolling update to the fleet with zero downtime and graceful failure handling.

### Phase 1: Rolling Update Basics

Write a playbook that deploys a new application page to all app servers using `serial`. The load balancer must continue serving traffic throughout the deployment.

**Requirements**:
- Playbook uses `serial: 1` (one server at a time)
- Deploy the provided `templates/index.html.j2` to each server
- Restart nginx after deploying
- Verify the load balancer is still serving after each server update

### Phase 2: Orchestrated Deployment

Create a role that handles the full deployment lifecycle with delegation and health checks.

**Requirements**:
- `run_once` task on the monitor node: pre-deploy health check (verify LB is serving)
- `delegate_to` the load balancer: disable the current server before updating
- Deploy the update and restart nginx
- `delegate_to` the load balancer: re-enable the server after update
- Verify the server is back in the LB pool
- `serial` controls the batch size

### Phase 3: Failure Handling

Extend your role to handle failures gracefully using `block/rescue/always`.

**Requirements**:
- The update block should be wrapped in `block/rescue/always`
- If the update fails on a server: the `rescue` block must ensure the server is drained from the LB (so it stops receiving traffic)
- The `always` block should log the result to the monitor node
- `max_fail_percentage` should be set so the deployment continues even if one server fails
- After the full roll: the deployment must NOT be marked as failed if only one server had issues

**Test**: sdc-app-4 has a planted flag file. Your role should detect it (e.g., check for the broken flag, fail if present), handle the failure via rescue, and continue the roll on the remaining servers.

---

## 3. KEY ANSIBLE CONCEPTS

### serial

```yaml
- hosts: app_servers
  serial: 1           # One at a time
  # or: serial: "25%" # 25% of hosts at a time
  # or: serial: [1, 2, "100%"]  # Canary pattern
```

### delegate_to

```yaml
- name: Disable server in load balancer
  ansible.builtin.shell: |
    echo "disable server app_servers/{{ inventory_hostname }}" | socat stdio /var/run/haproxy/admin.sock
  delegate_to: sdc-lb
```

### run_once

```yaml
- name: Pre-deploy health check
  ansible.builtin.uri:
    url: http://localhost:8080/
    status_code: 200
  run_once: true
  delegate_to: sdc-monitor
```

### block/rescue/always

```yaml
- block:
    - name: Deploy update
      # ... tasks that might fail
  rescue:
    - name: Handle failure
      # ... drain from LB, log error
  always:
    - name: Log result
      # ... always runs
```

### max_fail_percentage

```yaml
- hosts: app_servers
  serial: 1
  max_fail_percentage: 25    # Allow 1 of 4 to fail
```

### Detecting Pre-deploy Issues

```yaml
- name: Check for broken config
  ansible.builtin.stat:
    path: /etc/nginx/conf.d/broken.flag
  register: broken_check

- name: Abort if config is broken
  ansible.builtin.fail:
    msg: "Server has a broken configuration — triggering rescue"
  when: broken_check.stat.exists
```

`ansible.builtin.stat` checks if a file exists. `ansible.builtin.fail` deliberately fails the task, which triggers the `rescue` block when used inside a `block`.

---

## 4. HAPROXY MANAGEMENT

The load balancer exposes a stats socket. Use `socat` to manage backends:

```bash
# Disable a server (drain it)
echo "disable server app_servers/app1" | socat stdio /var/run/haproxy/admin.sock

# Enable a server
echo "enable server app_servers/app1" | socat stdio /var/run/haproxy/admin.sock

# Show server status
echo "show servers state" | socat stdio /var/run/haproxy/admin.sock
```

**Via Ansible delegation**:

```yaml
- name: Drain server from LB
  ansible.builtin.shell: |
    echo "disable server app_servers/{{ haproxy_backend_name }}" | socat stdio /var/run/haproxy/admin.sock
  delegate_to: sdc-lb
```

The HAProxy backend names are: `app1`, `app2`, `app3`, `app4` (matching the server lines in haproxy.cfg).

**Stats dashboard**: `http://localhost:8404/stats` — watch servers go green/red during your rolling deploy.

---

## 5. VERIFICATION

ARIA verifies three phases:
1. **Rolling Update**: Playbook exists, uses serial, app servers have updated content
2. **Orchestration**: Role exists with delegation tasks, health checks, serial config
3. **Failure Handling**: block/rescue/always present, max_fail_percentage set, deployment handles app-4 failure gracefully

Run `make test` to verify.

---

## 6. DELIVERABLES

| File | Purpose |
|------|---------|
| `workspace/rolling-update.yml` | Phase 1 playbook (serial deploy) |
| `workspace/roles/fleet_deploy/` | Phase 2+3 role (orchestrated deploy with error handling) |
| `workspace/site.yml` | Phase 2+3 playbook calling the role |

---

## 7. GETTING STARTED

1. Activate your environment: `source venv/bin/activate`
2. All work goes in the `workspace/` directory — `cd workspace/`
3. Stuck? Consult [HINTS.md](HINTS.md)
4. Track your progress: [CHECKLIST.md](../CHECKLIST.md)

---

*SDC Cyber Command — 2187 — LIEUTENANT EYES ONLY*
