#!/usr/bin/env bash
set -Eeuo pipefail

compose() {
  if docker compose version >/dev/null 2>&1; then
    docker compose "$@"
  else
    docker-compose "$@"
  fi
}

project_name="${COMPOSE_PROJECT_NAME:-realmeet_ci}"
backend_url="http://localhost:${BACKEND_PORT:-18080}"

show_logs() {
  compose -p "$project_name" -f docker-compose.ci.yml logs --no-color backend frontend db || true
}

cleanup() {
  compose -p "$project_name" -f docker-compose.ci.yml stop || true
}

trap 'status=$?; if [ "$status" -ne 0 ]; then show_logs; fi; cleanup; exit "$status"' EXIT

compose -p "$project_name" -f docker-compose.ci.yml up --build -d

for attempt in $(seq 1 60); do
  if curl -fsS "$backend_url/ready" >/dev/null; then
    break
  fi
  if [ "$attempt" -eq 60 ]; then
    echo "Backend did not become ready within timeout" >&2
    exit 1
  fi
  sleep 2
done

curl -fsS "$backend_url/health"
curl -fsS "$backend_url/ready"
curl -fsS "$backend_url/api/v1/categories"

echo "Smoke checks passed for $backend_url"
