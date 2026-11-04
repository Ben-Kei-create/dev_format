#!/usr/bin/env bash
# 使い方: ./scripts/roll_dice.sh
# 依存度ダイス(d60 と d40)を振り、結果を表示して docs/dice_log.md に追記する。
# 余りが出た場合は、続けて調査視点のダイス(roll_research.sh)も振る。
# AI は数値を自分で決めず、必ずこのスクリプトの出力を使う。
set -euo pipefail
cd "$(dirname "$0")/.."
R="$(python3 -I - <<'PY'
import secrets, datetime, pathlib, sys
f = secrets.randbelow(60) + 1   # フォーマット依存度 1〜60
u = secrets.randbelow(40) + 1   # ユーザー指示依存度 1〜40
r = 100 - f - u                 # 余り(リサーチ主導の書き直し) 0〜98
now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
out = sys.stderr
print(f"フォーマット依存度 (d60): {f}%", file=out)
print(f"ユーザー指示依存度 (d40): {u}%", file=out)
print(f"リサーチ主導の書き直し(余り): {r}%", file=out)
log = pathlib.Path("docs/dice_log.md")
log.parent.mkdir(exist_ok=True)
if not log.exists():
    log.write_text("# 依存度ダイスの記録\n\n| 日時 | アプリ | フォーマット(d60) | ユーザー指示(d40) | リサーチ(余り) |\n|---|---|---|---|---|\n", encoding="utf-8")
with log.open("a", encoding="utf-8") as fh:
    fh.write(f"| {now} | (アプリ名) | {f}% | {u}% | {r}% |\n")
print("記録: docs/dice_log.md(アプリ名の欄は手で埋める)", file=out)
print(r)
PY
)"
echo
./scripts/roll_research.sh "$R"
