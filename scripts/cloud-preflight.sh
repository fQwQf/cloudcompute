#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

pass() {
  PASS_COUNT=$((PASS_COUNT + 1))
  printf '[PASS] %s\n' "$1"
}

warn() {
  WARN_COUNT=$((WARN_COUNT + 1))
  printf '[WARN] %s\n' "$1"
}

fail() {
  FAIL_COUNT=$((FAIL_COUNT + 1))
  printf '[FAIL] %s\n' "$1"
}

section() {
  printf '\n== %s ==\n' "$1"
}

section "Project files"
for file in docker-compose.yml backend/Dockerfile frontend/Dockerfile .env.example README.md; do
  if [[ -f "$file" ]]; then
    pass "$file exists"
  else
    fail "$file missing"
  fi
done

if [[ -f .env ]]; then
  pass ".env exists"
else
  warn ".env missing, run: cp .env.example .env"
fi

section "Docker"
if command -v docker >/dev/null 2>&1; then
  pass "docker command found: $(docker --version)"
else
  fail "docker command not found"
fi

if docker compose version >/dev/null 2>&1; then
  pass "docker compose found: $(docker compose version --short)"
else
  fail "docker compose plugin not found"
fi

if docker info >/dev/null 2>&1; then
  pass "docker daemon is running"
else
  warn "docker daemon is not reachable; start Docker before deployment"
fi

section "Compose config"
if docker compose config >/tmp/cloudcostlab-compose-check.yml 2>/tmp/cloudcostlab-compose-check.err; then
  pass "docker compose config is valid"
else
  fail "docker compose config failed"
  cat /tmp/cloudcostlab-compose-check.err
fi

section "Containers"
if docker info >/dev/null 2>&1; then
  docker compose ps || true
  for container in cloudcostlab-opengauss cloudcostlab-backend cloudcostlab-frontend; do
    if docker inspect "$container" >/dev/null 2>&1; then
      status="$(docker inspect -f '{{.State.Status}}' "$container")"
      if [[ "$status" == "running" ]]; then
        pass "$container is running"
      else
        warn "$container exists but status is $status"
      fi
    else
      warn "$container does not exist; run: docker compose up -d --build"
    fi
  done
else
  warn "skip container checks because docker daemon is not reachable"
fi

section "HTTP checks"
if command -v curl >/dev/null 2>&1; then
  if curl -fsS http://127.0.0.1:8000/api/health >/tmp/cloudcostlab-health.txt 2>/dev/null; then
    pass "backend health endpoint ok"
  else
    warn "backend health endpoint not reachable at http://127.0.0.1:8000/api/health"
  fi

  if curl -fsS http://127.0.0.1:8080 >/dev/null 2>&1; then
    pass "frontend reachable at http://127.0.0.1:8080"
  else
    warn "frontend not reachable at http://127.0.0.1:8080"
  fi
else
  warn "curl command not found; skip HTTP checks"
fi

section "openGauss checks"
if docker inspect cloudcostlab-opengauss >/dev/null 2>&1; then
  DB_USER="${OPENGAUSS_USER:-gaussdb}"
  DB_PASSWORD="${OPENGAUSS_PASSWORD:-CloudGauss@2026}"
  if [[ -f .env ]]; then
    # shellcheck disable=SC1091
    set -a && source .env && set +a
    DB_USER="${OPENGAUSS_USER:-$DB_USER}"
    DB_PASSWORD="${OPENGAUSS_PASSWORD:-$DB_PASSWORD}"
  fi
  if docker exec \
    -e LD_LIBRARY_PATH=/usr/local/opengauss/lib:/usr/local/opengauss/lib/postgresql \
    cloudcostlab-opengauss \
    /usr/local/opengauss/bin/gsql \
    -d postgres \
    -U "$DB_USER" \
    -W "$DB_PASSWORD" \
    -h 127.0.0.1 \
    -p 5432 \
    -c "select count(*) as resources from cloud_resources;" \
    >/tmp/cloudcostlab-db.txt 2>/tmp/cloudcostlab-db.err; then
    pass "openGauss query ok"
    cat /tmp/cloudcostlab-db.txt
  else
    warn "openGauss query failed; database may still be initializing, or gsql credentials do not match"
    warn "used /usr/local/opengauss/bin/gsql with LD_LIBRARY_PATH=/usr/local/opengauss/lib:/usr/local/opengauss/lib/postgresql"
    cat /tmp/cloudcostlab-db.err || true
  fi
else
  warn "skip database checks because openGauss container does not exist"
fi

section "Summary"
printf 'Passed: %s, Warnings: %s, Failed: %s\n' "$PASS_COUNT" "$WARN_COUNT" "$FAIL_COUNT"

if [[ "$FAIL_COUNT" -gt 0 ]]; then
  exit 1
fi
