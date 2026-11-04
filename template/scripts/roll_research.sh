#!/usr/bin/env bash
# 使い方: ./scripts/roll_research.sh <余り%>
# 余り(リサーチ主導の書き直しの割合)を、6つの調査視点にダイスで配分する。
# 余りが 20% 未満の時は、ダイスを振らず ③競合 のみを調べる(randomdice.md の深さの表に従う)。
set -euo pipefail
R="${1:?使い方: $0 <余り%>}"
python3 -I - "$R" <<'PY'
import sys, secrets, collections
r = int(sys.argv[1])
names = {1:"① 新作トレンド", 2:"② 古い名作", 3:"③ 競合", 4:"④ 異ジャンルの借用", 5:"⑤ 失敗事例", 6:"⑥ 利用の文脈"}
if r <= 0:
    print("余り 0%: リサーチ主導の書き直しは行わない"); sys.exit(0)
if r < 20:
    print(f"余り {r}%: ダイスなし。③ 競合(レビューの不満)のみ調べる"); sys.exit(0)
n = max(1, round(r / 10))
tally = collections.Counter(secrets.randbelow(6) + 1 for _ in range(n))
print(f"余り {r}% → d6 を {n} 回")
for k in range(1, 7):
    print(f"  {names[k]}: {'●' * tally[k]}{' (出なかった)' if tally[k]==0 else ''}")
print("● が多い視点を重点的に調べる。出なかった視点も、深さの表の最低ラインは満たす。")
PY
