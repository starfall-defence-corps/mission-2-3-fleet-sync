.PHONY: help setup test reset destroy ssh-app-1 ssh-app-2 ssh-app-3 ssh-app-4 ssh-lb ssh-monitor

help: ## Show available commands
	@echo ""
	@echo "  STARFALL DEFENCE CORPS — Mission 2.3"
	@echo "  Fleet-Wide Operations"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'
	@echo ""

setup: ## Launch fleet + load balancer (6 containers)
	@bash scripts/setup-lab.sh

test: ## Run ARIA verification
	@bash scripts/check-work.sh

reset: ## Destroy and rebuild all nodes
	@bash scripts/reset-lab.sh

destroy: ## Tear down everything
	@bash scripts/destroy-lab.sh

ssh-app-1: ## SSH into sdc-app-1 (port 2261)
	@ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
		-i .docker/ssh-keys/cadet_key cadet@localhost -p 2261

ssh-app-2: ## SSH into sdc-app-2 (port 2262)
	@ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
		-i .docker/ssh-keys/cadet_key cadet@localhost -p 2262

ssh-app-3: ## SSH into sdc-app-3 (port 2263)
	@ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
		-i .docker/ssh-keys/cadet_key cadet@localhost -p 2263

ssh-app-4: ## SSH into sdc-app-4 (port 2264)
	@ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
		-i .docker/ssh-keys/cadet_key cadet@localhost -p 2264

ssh-lb: ## SSH into sdc-lb (HAProxy, port 2265)
	@ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
		-i .docker/ssh-keys/cadet_key cadet@localhost -p 2265

ssh-monitor: ## SSH into sdc-monitor (Rocky Linux, port 2266)
	@ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
		-i .docker/ssh-keys/cadet_key cadet@localhost -p 2266
