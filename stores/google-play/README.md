# Google Play(初版)

初版を整備済み(2026-11-06)。公式で再確認が必要な項目は、各ファイルに「要確認」と書いてある。

- `CLAUDE.md` の部品: `CLAUDE.part.md`
- 審査チェック: `review_prompts/`(1 企画 / 2 開発中 / 3 提出前)
- 掲載情報の申請キット、宣言、スクリーンショット: `playstore/`
- クローズドテスト運用: `workflow/closed_testing.md`、記録 `docs/closed_test_feedback.md`

## 確認できた点(2026-11-06)
- 個人アカウント(2023-11-13 以降に作成)は、本番公開の前に、クローズドテストで 12 人以上・14 日間継続(Google ヘルプ)。
- 新規アプリ・更新は、2026-08-31 以降 Android 16(API 36)以上が対象(Android Developers)。
- アイコンは 512×512 px の PNG、短い説明は 80 文字、フィーチャーグラフィックは必須(Google ヘルプ)。
- Repetitive Content: 機能・内容・体験が高度に似た複数アプリは、ポリシー違反となり得る。

## 自動入力(第2段階・未実装)
データセーフティの書き込み API があることを確認済み(`applications.dataSafety`)。実装する時は、Apple と同じ関所を守る(`stores/apple/appstore/automation/README.md`)。

## 未整備・未確認
- Android App Bundle の要件、開発者アカウントの登録料と本人確認、審査にかかる日数: 公式で確認する。
- アプリのタイトルの文字数(30 と 50 の食い違い)、スクリーンショットの寸法・枚数: Play Console で確認する。
- Android の技術別ルール(`engines/android/`)は、まだない。Android 向けに作る時に整備する。
- ポリシーの条文(Repetitive Content、Minimum Functionality ほか)は、ポリシーセンターで直接確認する。
