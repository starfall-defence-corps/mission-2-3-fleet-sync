# Starfall Defence Corps Academy

## Mission 2.3: Fleet-Wide Operations

> *"Deploy to all 4 at once and the fleet goes dark. Deploy one at a time, handle failures, keep the load balancer green. That's fleet operations."*

You are a Lieutenant at the Starfall Defence Corps Academy. You can harden systems, test them, and measure compliance. Now prove you can deploy to a live fleet with zero downtime — and handle it when things go wrong.

## Prerequisites

- Completed Module 1 (Missions 1.1–1.5 + Gateway Simulation)
- Completed Missions 2.1–2.2
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (with Docker Compose v2)
- [GNU Make](https://www.gnu.org/software/make/)
- Python 3.10+ (with `python3-venv`)
- Git

> **Windows users**: Install [WSL2](https://learn.microsoft.com/en-us/windows/wsl/install) and run all commands from within your WSL terminal.

## Quick Start

```bash
git clone https://github.com/YOUR-USERNAME/mission-2-3-fleet-sync.git
cd mission-2-3-fleet-sync
make setup
source venv/bin/activate
```

Read your orders: [Mission Briefing](docs/BRIEFING.md)

## Lab Architecture

```
                    ┌──────────┐
                    │  sdc-lb  │
                    │ HAProxy  │
                    │ :8080 LB │
                    └────┬─────┘
         ┌──────────┬────┴────┬──────────┐
    ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
    │sdc-app-1│ │sdc-app-2│ │sdc-app-3│ │sdc-app-4│
    │ :2261   │ │ :2262   │ │ :2263   │ │ :2264   │
    └─────────┘ └─────────┘ └─────────┘ └─────────┘
    ┌────────────┐
    │sdc-monitor │ (Rocky Linux 9, :2266)
    └────────────┘
```

## Mission Structure

| Phase | Description |
|-------|-------------|
| 1 | Rolling Update Basics — serial deploy to app servers |
| 2 | Orchestrated Deployment — delegation, health checks, role |
| 3 | Failure Handling — block/rescue/always, max_fail_percentage |

## Available Commands

```
make help          Show available commands
make setup         Launch fleet + load balancer (6 containers)
make test          Ask ARIA to verify your work
make reset         Destroy and rebuild all nodes
make destroy       Tear down everything
make ssh-app-1     SSH into sdc-app-1 (port 2261)
make ssh-app-2     SSH into sdc-app-2 (port 2262)
make ssh-app-3     SSH into sdc-app-3 (port 2263)
make ssh-app-4     SSH into sdc-app-4 (port 2264)
make ssh-lb        SSH into sdc-lb (HAProxy, port 2265)
make ssh-monitor   SSH into sdc-monitor (port 2266)
```

## Useful URLs

- Load balancer: `http://localhost:8080`
- HAProxy stats: `http://localhost:8404/stats`

## ARIA Review (Pull Request Workflow)

**Locally** — run `make test` for instant verification.

**On Pull Request** — push your work, open a PR, ARIA reviews automatically.

To enable PR reviews, add `ANTHROPIC_API_KEY` to your repo's Secrets.
