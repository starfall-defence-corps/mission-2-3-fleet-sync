# Mission 2.3: Fleet-Wide Operations — Hints

## Troubleshooting

**SSH issues**: Run `make setup` first. Check `docker ps` to verify all 6 containers are running.

**HAProxy not serving**: Check `docker exec sdc-lb systemctl status haproxy`. The stats page at `http://localhost:8404/stats` shows backend health.

**socat not found on LB**: socat is pre-installed on sdc-lb. If using delegation, make sure your `delegate_to` points to `sdc-lb`.

**HAProxy admin socket**: The socket is at `/var/run/haproxy/admin.sock`. HAProxy must be configured with `stats socket` for this to work. If it doesn't exist, you may need to add the socket config to haproxy.cfg.

**serial not working**: Make sure `serial` is at the play level, not the task level. It's a play keyword, not a task keyword.

**delegate_to vs run_once**: `delegate_to` runs the task on another host but in the context of the current host. `run_once` runs the task only once regardless of how many hosts are in the play.

**max_fail_percentage math**: With 4 hosts and `max_fail_percentage: 25`, one host can fail. With `serial: 1`, each host is its own batch, so the percentage is calculated per batch.

**Need a clean slate**: Run `make reset` to rebuild all containers. Your workspace files are preserved.

## The Planted Failure

sdc-app-4 has a file at `/etc/nginx/conf.d/broken.flag`. Your role should:
1. Check if this file exists
2. If it does, fail the task (triggering the rescue block)
3. The rescue block drains the server from the LB
4. The deployment continues on remaining servers
