# Godot(初版)

初版を整備済み(2026-11-06)。公式で再確認が必要な項目は、各ファイルに「要確認」と書いてある。
- `CLAUDE.part.md`: Godot 固有のルール
- `workflow/godot_export.md`: 書き出し手順と、Apple / Google Play との関係

確認済み(2026-11-06): Android の JDK / SDK / AAB(Gradle 必須)/ キーストアの手順(公式)。
未確認: **iOS のプライバシーマニフェストの自動生成の有無**、**Android のターゲット API 36 の既定値**(4.7 は 36 が既定、4.6.2 は 35 とみなす。公式の記載ではない。`workflow/godot_export.md` の手順で、書き出し後に必ず確認する)、広告プラグインの選定、C# の書き出し制約、Godot 公式のバージョン情報。
