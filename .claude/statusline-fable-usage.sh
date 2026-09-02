#!/bin/bash
# statusline用: Fable(モデル別)週次利用率の整数%のみを出力する。取得不可なら何も出力しない。
# claude.ai の /usage 画面と同じ OAuth usage API を参照。statuslineは高頻度で呼ばれるため60秒キャッシュする。
# トークンは macOS Keychain から取得し、標準出力には一切出さない。
CACHE="${TMPDIR:-/tmp}/claude-statusline-fable-$(id -u)"
TTL=60
now=$(date +%s)
if [ -f "$CACHE" ]; then
  mtime=$(stat -f %m "$CACHE" 2>/dev/null || echo 0)
  if [ $((now - mtime)) -lt "$TTL" ]; then
    cat "$CACHE"
    exit 0
  fi
fi
token=$(security find-generic-password -s "Claude Code-credentials" -w 2>/dev/null | jq -r '.claudeAiOauth.accessToken // empty' 2>/dev/null)
pct=""
if [ -n "$token" ]; then
  pct=$(curl -sf --max-time 3 \
    -H "Authorization: Bearer $token" \
    -H "anthropic-beta: oauth-2025-04-20" \
    https://api.anthropic.com/api/oauth/usage 2>/dev/null \
    | jq -r '[.limits[]? | select(.kind == "weekly_scoped" and .scope.model != null)][0].percent // empty' 2>/dev/null)
fi
pct=${pct%%.*}
if [ -n "$pct" ]; then
  printf '%s' "$pct" > "$CACHE.tmp" && mv "$CACHE.tmp" "$CACHE"
  printf '%s' "$pct"
elif [ -f "$CACHE" ]; then
  # API失敗時は期限切れキャッシュを流用（表示が消えるより古い値のほうがまし）
  touch "$CACHE"
  cat "$CACHE"
fi
