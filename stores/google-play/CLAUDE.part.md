
## ストア別ルール: Google Play(初版。公式で要確認の項目あり)
- 段階: 企画 `review_prompts/1_planning.md` → 開発中 `2_development.md` → 提出前 `3_submission.md`(通過後に `playstore/listing_kit.md` で申請キット)。
- 個人アカウント(2023-11-13 以降に作成)は、公開前にクローズドテストで **12 人以上 × 14 日間継続**(`workflow/closed_testing.md`)。募集は X で(AI が下書き、`marketing/`)。テスト用ビルドのアップロードは、オーナーが指示した時だけ。
- **実装完了(起動アニメーションを含む)をオーナーが宣言するまで、本番公開用のビルドのアップロード・Play Console の公開操作に触れない。提案もしない。**
- 審査への返信文・回答案は、**Google から実際のメッセージが届き、オーナーが文面を渡した時だけ**。未申請では作らない。
- **自動入力**(`playstore/automation/README.md`): 実装完了の宣言の後、オーナーが指示した時だけ。`plan` で差分 → OK → `apply`(検証のみ) → 別の承認 → `--commit`。個人情報・アプリのコンテンツの宣言・AAB は手動。鍵はコミットも貼り付けもしない。クラウドでは使わない。
- 宣言は `playstore/app_content_and_data_safety.md`(実装と必ず一致)。画像は `playstore/screenshots.md`(捏造しない。テスト広告・デバッグ表示を写さない)。公開ページ(`web/`)は申請の前に本番で公開済みに。記録先: `docs/closed_test_feedback.md`。
