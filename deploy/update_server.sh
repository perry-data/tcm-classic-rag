#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/opt/tcm-classic-rag}"
REMOTE_NAME="${REMOTE_NAME:-origin}"
DEPLOY_BRANCH="${DEPLOY_BRANCH:-main}"
SERVICE_NAME="${SERVICE_NAME:-tcm-classic-rag}"
BACKEND_URL="${BACKEND_URL:-http://127.0.0.1:8000}"
PUBLIC_URL="${PUBLIC_URL:-http://127.0.0.1/}"

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "missing required command: $1" >&2
    exit 1
  fi
}

wait_for_http() {
  local url="$1"
  local label="$2"
  local attempt

  for attempt in $(seq 1 30); do
    if curl -fsS --max-time 10 "$url" >/dev/null; then
      echo "healthy: $label ($url)"
      return 0
    fi
    sleep 2
  done

  echo "health check failed: $label ($url)" >&2
  return 1
}

require_cmd git
require_cmd curl
require_cmd npm
require_cmd systemctl
require_cmd python3

cd "$PROJECT_DIR"

if [[ ! -d .git ]]; then
  echo "expected git worktree at $PROJECT_DIR" >&2
  exit 1
fi

git fetch "$REMOTE_NAME" "$DEPLOY_BRANCH"

if git show-ref --verify --quiet "refs/heads/$DEPLOY_BRANCH"; then
  git checkout "$DEPLOY_BRANCH"
else
  git checkout -B "$DEPLOY_BRANCH" "$REMOTE_NAME/$DEPLOY_BRANCH"
fi

git reset --hard "$REMOTE_NAME/$DEPLOY_BRANCH"

install -m 644 deploy/systemd/tcm-classic-rag.service "/etc/systemd/system/${SERVICE_NAME}.service"
install -m 644 deploy/caddy/Caddyfile.ipv4 /etc/caddy/Caddyfile
systemctl daemon-reload

if [[ ! -x .venv/bin/python ]]; then
  python3 -m venv .venv
fi

. .venv/bin/activate
pip install -r requirements.txt

pushd frontend >/dev/null
npm ci
npm run build
popd >/dev/null

systemctl restart "$SERVICE_NAME"
systemctl reload caddy || systemctl restart caddy

wait_for_http "${BACKEND_URL}/" "backend"
wait_for_http "$PUBLIC_URL" "public proxy"

SMOKE_FILE="$(mktemp)"
trap 'rm -f "$SMOKE_FILE"' EXIT

curl -fsS --max-time 120 \
  -X POST "${BACKEND_URL}/api/v1/answers" \
  -H "Content-Type: application/json" \
  --data '{"query":"黄连汤方的条文是什么？"}' >"$SMOKE_FILE"

python3 - "$SMOKE_FILE" <<'PY'
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
required_fields = ("query", "answer_mode", "answer_text")
missing = [field for field in required_fields if field not in payload]
if missing:
    raise SystemExit(f"missing response fields: {', '.join(missing)}")
if not str(payload["answer_text"]).strip():
    raise SystemExit("empty answer_text in smoke response")
print(json.dumps({"query": payload["query"], "answer_mode": payload["answer_mode"]}, ensure_ascii=False))
PY
