#!/usr/bin/env bash
# 使い方: ./scripts/install_hooks.sh  (リポジトリのルートで実行)
# .git/hooks はクローンでは複製されないので、クローンし直したら再実行する。
set -euo pipefail
cd "$(dirname "$0")/.."
[ -d .git ] || { echo ".git がありません" >&2; exit 1; }
if [ -e .git/hooks/pre-commit ] && ! cmp -s scripts/pre-commit .git/hooks/pre-commit; then
  echo "既に別の pre-commit があります。手動で統合してください: scripts/pre-commit" >&2; exit 1
fi
cp scripts/pre-commit .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit
echo "pre-commit フックを入れました"
