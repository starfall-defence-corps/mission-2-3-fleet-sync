# Mission 2.3: Fleet-Wide Operations — Checklist

## Phase 1: Rolling Update Basics
- [ ] rolling-update.yml exists with serial: 1
- [ ] Deploys index.html.j2 to app servers
- [ ] Restarts nginx after deploy
- [ ] Load balancer continues serving throughout

## Phase 2: Orchestrated Deployment
- [ ] fleet_deploy role created
- [ ] Role uses delegate_to for LB drain/enable
- [ ] Role includes health check tasks
- [ ] site.yml calls role with serial

## Phase 3: Failure Handling
- [ ] Role uses block/rescue/always
- [ ] max_fail_percentage set in site.yml
- [ ] Deployment handles app-4 failure gracefully
- [ ] Healthy servers remain in LB pool
- [ ] `make test` — all phases pass
