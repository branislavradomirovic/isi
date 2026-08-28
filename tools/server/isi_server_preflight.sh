#!/usr/bin/env bash
set -euo pipefail

section() { printf '\n===== %s =====\n' "$1"; }
run_optional() {
  local label="$1"
  shift
  section "$label"
  "$@" 2>&1 || true
}

section "ISI TARGET SERVER PREFLIGHT - READ ONLY"
echo "timestamp_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "hostname=$(hostname)"
echo "user=$(id -un)"
echo "pwd=$(pwd)"

run_optional "OS" sh -c 'uname -a; echo; cat /etc/os-release 2>/dev/null || true'
run_optional "CPU AND MEMORY" sh -c 'echo "cpus=$(getconf _NPROCESSORS_ONLN 2>/dev/null || nproc 2>/dev/null || echo unknown)"; free -h 2>/dev/null || vmstat -s 2>/dev/null || true'
run_optional "FILESYSTEM" sh -c 'df -hT / /var/lib/docker /home 2>/dev/null || df -hT / 2>/dev/null || true'

if command -v docker >/dev/null 2>&1; then
  run_optional "DOCKER VERSION" docker version
  run_optional "DOCKER COMPOSE VERSION" docker compose version
  run_optional "DOCKER COMPOSE PROJECTS" docker compose ls
  run_optional "RUNNING CONTAINERS" docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
  run_optional "COMPOSE OWNERSHIP" sh -c 'docker ps -q | xargs -r docker inspect -f '\''{{.Name}} | project={{index .Config.Labels "com.docker.compose.project"}} | dir={{index .Config.Labels "com.docker.compose.project.working_dir"}} | compose={{index .Config.Labels "com.docker.compose.project.config_files"}}'\'''
  run_optional "DOCKER NETWORKS" docker network ls
  run_optional "DOCKER VOLUMES" docker volume ls
  run_optional "DOCKER STORAGE" docker system df
else
  section "DOCKER"
  echo "docker_not_found"
fi

run_optional "LISTENING TCP PORTS" sh -c 'ss -ltnp 2>/dev/null || netstat -ltnp 2>/dev/null || true'
run_optional "LISTENING UDP PORTS" sh -c 'ss -lunp 2>/dev/null || netstat -lunp 2>/dev/null || true'

section "REVERSE PROXY SERVICES"
for svc in caddy nginx traefik; do
  if command -v systemctl >/dev/null 2>&1; then
    state="$(systemctl is-active "$svc" 2>/dev/null || true)"
    enabled="$(systemctl is-enabled "$svc" 2>/dev/null || true)"
    echo "$svc active=${state:-unknown} enabled=${enabled:-unknown}"
  fi
done

section "CADDY ROUTE SUMMARY"
if [ -r /etc/caddy/Caddyfile ]; then
  grep -nE '(^|[[:space:]])(reverse_proxy|handle|route|redir|tls)([[:space:]]|$)|^[^#[:space:]][^\{]*\{' /etc/caddy/Caddyfile 2>/dev/null || true
elif command -v sudo >/dev/null 2>&1 && sudo -n test -r /etc/caddy/Caddyfile 2>/dev/null; then
  sudo -n grep -nE '(^|[[:space:]])(reverse_proxy|handle|route|redir|tls)([[:space:]]|$)|^[^#[:space:]][^\{]*\{' /etc/caddy/Caddyfile 2>/dev/null || true
else
  echo "caddyfile_not_readable_without_prompt"
fi

section "NGINX ROUTE SUMMARY"
if command -v nginx >/dev/null 2>&1; then
  if nginx -T >/dev/null 2>&1; then
    nginx -T 2>/dev/null | grep -nE 'server_name|listen |proxy_pass' || true
  elif command -v sudo >/dev/null 2>&1 && sudo -n nginx -T >/dev/null 2>&1; then
    sudo -n nginx -T 2>/dev/null | grep -nE 'server_name|listen |proxy_pass' || true
  else
    echo "nginx_config_not_readable_without_prompt"
  fi
else
  echo "nginx_binary_not_found"
fi

section "DISCOVERED COMPOSE FILES"
find "$HOME" -maxdepth 4 -type f \( -name 'docker-compose.yml' -o -name 'docker-compose.*.yml' -o -name 'compose.yml' -o -name 'compose.*.yml' \) -print 2>/dev/null | sort || true

section "OLLAMA SERVICE"
if command -v systemctl >/dev/null 2>&1; then
  echo "ollama_active=$(systemctl is-active ollama 2>/dev/null || true)"
fi
if command -v curl >/dev/null 2>&1; then
  if command -v python3 >/dev/null 2>&1; then
    if result="$(curl -fsS --max-time 3 http://127.0.0.1:11434/api/tags 2>/dev/null | python3 -c 'import json,sys; data=json.load(sys.stdin); names=sorted(str(x.get("name") or x.get("model")) for x in data.get("models",[]) if x.get("name") or x.get("model")); print(",".join(names))' 2>/dev/null)"; then
      echo "ollama_http=reachable"
      echo "ollama_models=$result"
    else
      echo "ollama_http=not_reachable_or_unparseable_on_127.0.0.1:11434"
    fi
  elif curl -fsS --max-time 3 http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
    echo "ollama_http=reachable"
    echo "ollama_models=python3_unavailable"
  else
    echo "ollama_http=not_reachable_on_127.0.0.1:11434"
  fi
fi

section "SAFETY ASSERTIONS"
echo "no_env_files_read=true"
echo "no_files_created_or_removed=true"
echo "no_containers_started_or_stopped=true"
echo "no_docker_resources_created_or_removed=true"
echo "no_git_mutation=true"
echo "no_firewall_or_dns_mutation=true"
echo "no_existing_application_mutation=true"

echo
echo "=== ISI TARGET SERVER PREFLIGHT COMPLETE ==="
