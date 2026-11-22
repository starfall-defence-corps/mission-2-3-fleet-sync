# Starfall Defence Corps Academy

> 🧭 [← 2.2 Compliance as Code](https://github.com/starfall-defence-corps/mission-2-2-compliance-as-code) · **You are here: 2.3 Fleet Sync** · [2.4 Defence in Depth →](https://github.com/starfall-defence-corps/mission-2-4-defence-in-depth) · [🏠 Academy Hub](https://github.com/starfall-defence-corps/sdc-academy) · [📚 Field Manuals](https://github.com/starfall-defence-corps/sdc-academy/tree/main/field-manuals)

> ☁️ **No Docker on your machine?** Create your own copy first (Use this template), then on **your** repo: **Code → Codespaces → Create codespace** — everything is preinstalled. First boot takes ~5 min (one-time); after that it starts fast.

## Mission 2.3: Fleet Sync

> *"Deploy to all 4 at once and the fleet goes dark. Deploy one at a time, handle failures, keep the load balancer green. That's fleet operations."*

You are a Lieutenant at the Starfall Defence Corps Academy. You can harden systems, test them, and measure compliance. Now prove you can deploy to a live fleet with zero downtime — and handle it when things go wrong.

## Briefing

The fleet runs four application servers behind an HAProxy load balancer. A critical update must reach all four: it changes the application page and restarts nginx. Deploy to all four at once and availability drops to zero. And when one server fails mid-deploy, the old answer — abort everything and roll back by hand for three hours — is no longer acceptable.

Intelligence reports a planted issue on `sdc-app-4`: a flag file at `/etc/nginx/conf.d/broken.flag` that should make your deployment fail on that node. Your rollout has to detect it, contain it, and finish the job on the rest of the fleet. Full orders, the key Ansible concepts and the HAProxy commands are in the [Mission Briefing](docs/BRIEFING.md).

## Objectives

`make test` verifies three phases. Phases 1 and 3 run your playbooks against the live fleet.

| Phase | ARIA checks |
|-------|-------------|
| 1 — Rolling Update Basics | `workspace/rolling-update.yml` exists and sets `serial` at play level; it runs without errors; `sdc-app-1` serves the updated page; and the load balancer on `localhost:8080` still returns HTTP 200 |
| 2 — Orchestrated Deployment | A `fleet_deploy` role exists at `workspace/roles/fleet_deploy/`; its `tasks/main.yml` uses `delegate_to` and includes a health check (`uri`, `curl`, `wait_for` or similar); `workspace/site.yml` calls the role and sets `serial` |
| 3 — Failure Handling | The role uses `block`/`rescue`; `site.yml` sets `max_fail_percentage`; `ansible-playbook site.yml` completes successfully despite the failure on `sdc-app-4`; and the load balancer still returns HTTP 200 afterwards |

## What You'll Learn

- Rolling updates with `serial` (one host at a time, percentages, canary batches)
- Delegation with `delegate_to`: running a task on the load balancer on behalf of each app server
- `run_once` for fleet-level steps such as a pre-deploy health check from the monitor node
- Draining and re-enabling HAProxy backends through the admin socket with `socat`
- Health checks with `ansible.builtin.uri` before a server rejoins the pool
- Error handling with `block`/`rescue`/`always`, and failing deliberately with `ansible.builtin.fail`
- Tolerating partial failure with `max_fail_percentage`

## Prerequisites

- Completed Module 1 (Missions 1.1–1.6 + Gateway Simulation)
- Completed Missions 2.1–2.2
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (with Docker Compose v2)
- [GNU Make](https://www.gnu.org/software/make/)
- **Ansible**: provided by the lab — `make setup` builds a local venv with `ansible-core`; no host install needed
- Python 3.10+ (with `python3-venv`)
- Git

> **Windows users**: Install [WSL2](https://learn.microsoft.com/en-us/windows/wsl/install) and run all commands from within your WSL terminal.

## Quick Start

```bash
# 1. Use this template on GitHub (green button, top right) to create YOUR OWN
#    copy. Set it Public, then clone it:
git clone https://github.com/YOUR-USERNAME/mission-2-3-fleet-sync.git
cd mission-2-3-fleet-sync

# 2. Check your machine is mission-ready
make doctor

# 3. Launch the fleet + load balancer (6 containers)
make setup

# 4. Activate the virtual environment
source venv/bin/activate
```

5. **Read your orders**: [Mission Briefing](docs/BRIEFING.md) — this mission has no separate exercises file; the phased walkthrough is in the briefing
6. **Stuck?** [Hints & Troubleshooting](docs/HINTS.md)
7. **Track progress**: [Checklist](CHECKLIST.md)
8. **Ready?** `make test`, then `make submit`

All your work goes in `workspace/`, but run `ansible-playbook` and `make` from the **project root** — a root `ansible.cfg` points Ansible at `workspace/inventory/hosts.yml` and `workspace/roles/`.

## Lab Architecture

```
 Your Machine
+--------------------------------------------------------------+
|  workspace/                                                  |
|    ansible.cfg                                               |
|    inventory/hosts.yml        (provided: groups + LB names)  |
|    inventory/group_vars/app_servers.yml  (provided)          |
|    templates/index.html.j2    (provided: the update)         |
|    rolling-update.yml         (you write — Phase 1)          |
|    site.yml                   (you write — Phases 2–3)       |
|    roles/fleet_deploy/        (you build — Phases 2–3)       |
|                                                              |
|  Docker Network: 172.34.0.0/24                               |
|                    +-----------+                             |
|                    |  sdc-lb   |  HAProxy                    |
|                    | :8080 LB  |  :8404 stats · :2265 SSH    |
|                    +-----+-----+                             |
|        +-----------+-----+-----+-----------+                 |
|  +-----------+ +-----------+ +-----------+ +-----------+     |
|  | sdc-app-1 | | sdc-app-2 | | sdc-app-3 | | sdc-app-4 |     |
|  |  :2261    | |  :2262    | |  :2263    | |  :2264    |     |
|  +-----------+ +-----------+ +-----------+ +-----------+     |
|  +-------------+                                             |
|  | sdc-monitor |  Rocky Linux 9, :2266                       |
|  +-------------+                                             |
+--------------------------------------------------------------+
```

| Node | Inventory group | OS | SSH port | Role in the mission |
|------|-----------------|----|----------|---------------------|
| `sdc-app-1` … `sdc-app-4` | `app_servers` | Ubuntu 22.04 | 2261–2264 | nginx on :80, behind the load balancer (HAProxy backends `app1`–`app4`) |
| `sdc-lb` | `load_balancers` | Ubuntu 22.04 | 2265 | HAProxy: traffic on `localhost:8080`, stats on `localhost:8404/stats`, admin socket at `/var/run/haproxy/admin.sock` |
| `sdc-monitor` | `monitoring` | Rocky Linux 9 | 2266 | Target for `run_once` checks and deployment logging |

HAProxy health-checks each app server every 2 seconds. Watch the stats page while your rollout runs — servers go red and green as you drain and re-enable them.

## Mission Structure

| Phase | Description | Deliverable |
|-------|-------------|-------------|
| 1 | Rolling Update Basics — serial deploy to app servers | `workspace/rolling-update.yml` |
| 2 | Orchestrated Deployment — delegation, health checks, role | `workspace/roles/fleet_deploy/`, `workspace/site.yml` |
| 3 | Failure Handling — `block`/`rescue`/`always`, `max_fail_percentage` | the same role and `site.yml`, extended |

## Available Commands

```
make help          Show available commands
make doctor        Check your machine is mission-ready (Docker, ports, tools)
make setup         Launch fleet + load balancer (6 containers)
make test          Ask ARIA to verify your work
make submit        Submit your work for ARIA review (branch, commit, push, PR)
make reset         Destroy and rebuild all nodes
make destroy       Tear down everything
make ssh-app-1     SSH into sdc-app-1 (port 2261)
make ssh-app-2     SSH into sdc-app-2 (port 2262)
make ssh-app-3     SSH into sdc-app-3 (port 2263)
make ssh-app-4     SSH into sdc-app-4 (port 2264)
make ssh-lb        SSH into sdc-lb (HAProxy, port 2265)
make ssh-monitor   SSH into sdc-monitor (Rocky Linux, port 2266)
```

> **Note:** `make submit` uses the [GitHub CLI](https://cli.github.com/) — install `gh` and run `gh auth login` once before your first submission.

## Useful URLs

- Load balancer: `http://localhost:8080`
- HAProxy stats: `http://localhost:8404/stats`

## Mission Files

| File | Purpose |
|------|---------|
| [BRIEFING.md](docs/BRIEFING.md) | Mission briefing, phase requirements, key concepts and HAProxy management — **read this first** |
| [HINTS.md](docs/HINTS.md) | Troubleshooting and hints |
| [CHECKLIST.md](CHECKLIST.md) | Progress tracker |

There is deliberately no `EXERCISES.md`: at Lieutenant rank the briefing carries the phased walkthrough.

## Checking Your Work: `make test`

`make test` runs ARIA's grader (`molecule/default/tests/test_fleet_sync.py`) against the running lab and reports each objective, phase by phase. It runs `rolling-update.yml` and `site.yml` against the fleet and checks the load balancer over HTTP, so the lab must be up (`make setup`). It needs no API key and works offline.

- Each run deploys to the fleet again, so expect it to take a few minutes.
- If the fleet gets into a state you can't explain, `make reset` rebuilds every container (including the planted flag on `sdc-app-4`); your `workspace/` files are preserved.
- The mission is complete when all three phases are green.

## Submission and ARIA Review

When `make test` is green, `make submit` creates a `mission-submission` branch (or uses your current branch if you are not on `main`), commits `workspace/` and `CHECKLIST.md`, pushes, and opens a pull request to `main` in **your own** copy. You can also do this by hand with `git` and the GitHub web UI.

Opening or updating the pull request runs the **ARIA Review** workflow (`.github/workflows/aria-review.yml`). It does not re-run the grader — the deterministic checks need the Docker lab, so your local `make test` is the verdict. Instead, ARIA reads your submitted playbooks and inventory and posts a qualitative, in-character code review as a PR comment. Each new push updates the same comment.

To enable PR reviews, add an API key to your repo:
1. Get a key from [platform.claude.com](https://platform.claude.com/)
2. In your repo: **Settings** > **Secrets and variables** > **Actions** > **New repository secret**
3. Name: `ANTHROPIC_API_KEY`, Value: your key

Without a key, the comment says the review was skipped and the check still passes; `make test` works locally either way.

## Hints Policy

At Lieutenant rank you get a mission briefing and a pass/fail verdict, not a step-by-step guide. The briefing already shows the building blocks (`serial`, `delegate_to`, `run_once`, `block`/`rescue`/`always`, `max_fail_percentage`, and how to detect the broken flag); putting them together is the mission. [HINTS.md](docs/HINTS.md) covers troubleshooting, a few common pitfalls (such as `serial` belonging at play level, and how a rescued host counts against `max_fail_percentage`), and what your role should do with the planted failure. Read ARIA's messages in `make test` before reaching for the hints. For module reference, see [FM-1 — Ansible Module Reference](https://github.com/starfall-defence-corps/sdc-academy/blob/main/field-manuals/FM-1-ansible-reference.md).

## Troubleshooting

**SSH issues**: Run `make setup` first, then check `docker ps` shows all 6 containers.

**HAProxy not serving**: Check `docker exec sdc-lb systemctl status haproxy`, and the stats page at `http://localhost:8404/stats` for backend health.

**`serial` has no effect**: It is a play keyword, not a task keyword.

**`make test` fails with "No module named pytest"**: Run `make setup` first — it creates the Python virtual environment.

**Need a clean slate**: `make reset` destroys and rebuilds all nodes; `make destroy` tears everything down.
