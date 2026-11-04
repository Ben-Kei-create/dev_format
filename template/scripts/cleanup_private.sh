#!/usr/bin/env bash
# 使い方:
#   ./scripts/cleanup_private.sh --now     申請が済んだら実行。kit_filled.md を完全に削除する
#   ./scripts/cleanup_private.sh --stale   有効期限(既定 180 分)を過ぎていたら削除する
# 期限は環境変数 KIT_TTL_MIN(分)で変更できる。
set -euo pipefail
cd "$(dirname "$0")/.."
f="private/kit_filled.md"
[ -e "$f" ] || { echo "削除対象なし"; exit 0; }
wipe() {
  if command -v shred >/dev/null 2>&1; then shred -u "$f" 2>/dev/null || rm -f "$f"; else rm -f "$f"; fi
  echo "削除しました: $f"
}
case "${1:-}" in
  --now) wipe ;;
  --stale)
    ttl_sec=$(( ${KIT_TTL_SEC:-$(( ${KIT_TTL_MIN:-180} * 60 ))} ))
    mtime="$(stat -c %Y "$f" 2>/dev/null || stat -f %m "$f")"
    age=$(( $(date +%s) - mtime ))
    if [ "$age" -ge "$ttl_sec" ]; then wipe; else echo "期限内(あと $(( (ttl_sec - age) / 60 )) 分で自動削除)"; fi ;;
  *) echo "使い方: $0 --now | --stale" >&2; exit 1 ;;
esac
