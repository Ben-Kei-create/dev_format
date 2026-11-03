#!/usr/bin/env bash
# 使い方: ./setup.sh /path/to/new-app-repo
# template/ の中身を、新規アプリのリポジトリにコピーする(既存ファイルは上書きしない)。
set -euo pipefail
TARGET="${1:?使い方: ./setup.sh /path/to/new-app-repo}"
SRC="$(cd "$(dirname "$0")" && pwd)/template"
[ -d "$TARGET" ] || { echo "ディレクトリがありません: $TARGET" >&2; exit 1; }

# 既存ファイルは上書きしない
(cd "$SRC" && find . -type f -print0) | while IFS= read -r -d '' f; do
  if [ -e "$TARGET/$f" ]; then
    echo "スキップ(既存): $f"
  else
    mkdir -p "$TARGET/$(dirname "$f")"
    cp "$SRC/$f" "$TARGET/$f"
  fi
done

# 個人情報ファイルの雛形(コミットされない)
if [ ! -e "$TARGET/private/owner_info.md" ]; then
  cp "$SRC/private/owner_info.example.md" "$TARGET/private/owner_info.md"
fi

# .gitignore に個人情報の除外が無ければ追記
if ! grep -q '^private/\*' "$TARGET/.gitignore" 2>/dev/null; then
  { echo; cat "$SRC/.gitignore"; } >> "$TARGET/.gitignore"
  echo ".gitignore に除外設定を追記しました"
fi

echo "コピーしました: $TARGET"
echo "次にやること: private/owner_info.md に実際の値を入れる(コミットされません)。"
echo "既に CLAUDE.md があった場合は、template/CLAUDE.md の内容を手動で追記してください。"
