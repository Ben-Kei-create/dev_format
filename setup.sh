#!/usr/bin/env bash
# 使い方: ./setup.sh /path/to/new-app-repo [--store apple] [--engine swiftui]
#   --store  : apple(既定) / google-play(未整備)
#   --engine : swiftui(既定) / godot(未整備) / android(未整備)
# core/ + stores/<store>/ + engines/<engine>/ を、新規アプリのリポジトリに同じ相対パスでコピーする。
# 既存ファイルは上書きしない。CLAUDE.md は、3つの CLAUDE 部品をつなげて作る。
set -euo pipefail

TARGET=""; STORE="apple"; ENGINE="swiftui"
while [ $# -gt 0 ]; do
  case "$1" in
    --store)  STORE="${2:?--store に値が必要}"; shift 2 ;;
    --engine) ENGINE="${2:?--engine に値が必要}"; shift 2 ;;
    -h|--help) sed -n 2,6p "$0"; exit 0 ;;
    *) [ -z "$TARGET" ] && TARGET="$1" || { echo "余分な引数: $1" >&2; exit 1; }; shift ;;
  esac
done
[ -n "$TARGET" ] || { echo "使い方: $0 /path/to/new-app-repo [--store apple] [--engine swiftui]" >&2; exit 1; }
[ -d "$TARGET" ] || { echo "ディレクトリがありません: $TARGET" >&2; exit 1; }

ROOT="$(cd "$(dirname "$0")" && pwd)"
CORE="$ROOT/core"; STORE_DIR="$ROOT/stores/$STORE"; ENGINE_DIR="$ROOT/engines/$ENGINE"
[ -d "$STORE_DIR" ]  || { echo "未知の --store: $STORE(stores/ 以下: $(ls "$ROOT/stores" | tr '\n' ' '))" >&2; exit 1; }
[ -d "$ENGINE_DIR" ] || { echo "未知の --engine: $ENGINE(engines/ 以下: $(ls "$ROOT/engines" | tr '\n' ' '))" >&2; exit 1; }

copy_tree() {  # $1=元ディレクトリ。既存は上書きしない。CLAUDE.part.md・直下の README.md・直下の CLAUDE.md は除く
  local src="$1"
  (cd "$src" && find . -type f ! -name 'CLAUDE.part.md' ! -path './README.md' ! -path './CLAUDE.md' -print0) | while IFS= read -r -d '' f; do
    if [ -e "$TARGET/$f" ]; then
      echo "スキップ(既存): $f"
    else
      mkdir -p "$TARGET/$(dirname "$f")"
      cp "$src/$f" "$TARGET/$f"
    fi
  done
}

copy_tree "$CORE"
copy_tree "$STORE_DIR"
copy_tree "$ENGINE_DIR"

# 未整備のストア・技術の通知
for d in "$STORE_DIR" "$ENGINE_DIR"; do
  if [ -f "$d/README.md" ] && [ ! -f "$d/CLAUDE.part.md" ]; then
    echo "注意: $(basename "$(dirname "$d")")/$(basename "$d") は未整備です(共通ルールのみ入ります)。内容: $d/README.md"
  fi
done

# CLAUDE.md を作る(core + ストア別 + 技術別)
if [ -e "$TARGET/CLAUDE.md" ]; then
  echo "スキップ(既存): CLAUDE.md。次の部品を手動で追記してください:"
  echo "  $CORE/CLAUDE.md  $STORE_DIR/CLAUDE.part.md  $ENGINE_DIR/CLAUDE.part.md"
else
  { cat "$CORE/CLAUDE.md"
    [ -f "$STORE_DIR/CLAUDE.part.md" ]  && cat "$STORE_DIR/CLAUDE.part.md"
    [ -f "$ENGINE_DIR/CLAUDE.part.md" ] && cat "$ENGINE_DIR/CLAUDE.part.md"
  } > "$TARGET/CLAUDE.md"
  echo "CLAUDE.md を作りました(store=$STORE, engine=$ENGINE)"
fi

# .gitignore に個人情報の除外が無ければ追記
if ! grep -q '^private/\*' "$TARGET/.gitignore" 2>/dev/null; then
  { echo; cat "$CORE/.gitignore"; } >> "$TARGET/.gitignore"
  echo ".gitignore に除外設定を追記しました"
fi

# コミット前の個人情報チェック(pre-commit フック)を入れる
if [ -d "$TARGET/.git" ]; then
  if [ ! -e "$TARGET/.git/hooks/pre-commit" ]; then
    cp "$CORE/scripts/pre-commit" "$TARGET/.git/hooks/pre-commit" && chmod +x "$TARGET/.git/hooks/pre-commit"
    echo "pre-commit フックを入れました"
  else
    echo "既に pre-commit フックがあるため入れていません。手動で統合: scripts/pre-commit"
  fi
else
  echo "注意: $TARGET は git リポジトリではありません。git init 後に ./scripts/install_hooks.sh を実行してください。"
fi

echo "コピーしました: $TARGET"
