#!/usr/bin/env bash
# 使い方: ./setup.sh /path/to/new-app-repo
# template/ の中身を、新規アプリのリポジトリにコピーする(既存ファイルは上書きしない)。
set -euo pipefail
TARGET="${1:?使い方: ./setup.sh /path/to/new-app-repo}"
SRC="$(cd "$(dirname "$0")" && pwd)/template"
[ -d "$TARGET" ] || { echo "ディレクトリがありません: $TARGET" >&2; exit 1; }
cp -rn "$SRC"/. "$TARGET"/
echo "コピーしました: $TARGET"
echo "既に CLAUDE.md がある場合は上書きしていないので、template/CLAUDE.md の内容を手動で追記してください。"
