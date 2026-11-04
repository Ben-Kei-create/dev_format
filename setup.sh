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

# .gitignore に個人情報の除外が無ければ追記
if ! grep -q '^private/\*' "$TARGET/.gitignore" 2>/dev/null; then
  { echo; cat "$SRC/.gitignore"; } >> "$TARGET/.gitignore"
  echo ".gitignore に除外設定を追記しました"
fi

# コミット前の個人情報チェック(pre-commit フック)を入れる
if [ -d "$TARGET/.git" ]; then
  if [ ! -e "$TARGET/.git/hooks/pre-commit" ]; then
    cp "$SRC/scripts/pre-commit" "$TARGET/.git/hooks/pre-commit" && chmod +x "$TARGET/.git/hooks/pre-commit"
    echo "pre-commit フックを入れました"
  else
    echo "既に pre-commit フックがあるため入れていません。手動で統合: scripts/pre-commit"
  fi
else
  echo "注意: $TARGET は git リポジトリではありません。git init 後に ./scripts/install_hooks.sh を実行してください。"
fi

echo "コピーしました: $TARGET"
echo "既に CLAUDE.md があった場合は、template/CLAUDE.md の内容を手動で追記してください。"
