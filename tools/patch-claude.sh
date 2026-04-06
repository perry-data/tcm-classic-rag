```bash
#!/usr/bin/env bash
set -euo pipefail

host="${API_HOST:-anyrouter.top}"

claude_cli="$(command -v claude || true)"

if [[ -z "$claude_cli" ]]; then
  echo "Error: claude command not found in PATH" >&2
  exit 1
fi

pnpm_path="$(
  grep "node_modules/@anthropic-ai/claude-code/cli.js" "$claude_cli" \
    | tail -n 1 \
    | tr ' ' '\n' \
    | grep basedir || true
)"

if [[ -n "$pnpm_path" ]]; then
  claude_cli="$(eval echo "$pnpm_path")"
fi

# 解析 claude_cli 的符号链接，找到真实文件
claude_cli="$(realpath "$claude_cli" 2>/dev/null || true)"
# 检查解析后的路径是否是普通文件，不是则报错退出
if [[ ! -f "$claude_cli" ]]; then
  echo "Error: 无法解析到真实的文件路径" >&2
  exit 1
fi

case "$(uname -s)" in
  Darwin)
    LC_ALL=C sed -i '' "s/\"api.anthropic.com\"/\"$host\"/g" "$claude_cli"
    ;;
  Linux)
    LC_ALL=C sed -i "s/\"api.anthropic.com\"/\"$host\"/g" "$claude_cli"
    ;;
  *)
    echo "错误：不支持的操作系统" >&2
    ;;
esac
```
