#!/usr/bin/env bash
# 使い方: ./scripts/fill_private.sh
# appstore/kit.md の {{キー}} を private/owner_info.md の値で置き換え、
# private/kit_filled.md を作る(private/ はコミットされない)。
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -I - <<'PY'
import re, sys, pathlib
info = pathlib.Path("private/owner_info.md")
kit = pathlib.Path("appstore/kit.md")
if not info.exists(): sys.exit("private/owner_info.md がありません")
if not kit.exists(): sys.exit("appstore/kit.md がありません(審査チェック完了後に作成します)")
vals = {}
for line in info.read_text(encoding="utf-8").splitlines():
    m = re.match(r"^- ([^:：]+)[:：]\s*(.*)$", line)
    if m and m.group(2).strip():
        vals[m.group(1).strip()] = m.group(2).strip()
text = kit.read_text(encoding="utf-8")
missing = set()
def rep(m):
    k = m.group(1).strip()
    if k in vals: return vals[k]
    missing.add(k); return m.group(0)
out = re.sub(r"\{\{([^}]+)\}\}", rep, text)
pathlib.Path("private/kit_filled.md").write_text(out, encoding="utf-8")
print("作成: private/kit_filled.md(コミットされません)")
if missing: print("未入力のキー: " + "、".join(sorted(missing)))
PY
