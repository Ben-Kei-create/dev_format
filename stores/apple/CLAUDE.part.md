
## ストア別ルール: Apple(App Store)
- 段階: 企画 `review_prompts/1_planning.md`(4.3・4.2.6・4.2) → 開発中 `2_development.md`(指示があれば TestFlight: `workflow/testflight.md`) → 提出前 `3_submission.md`(通過後に `appstore/kit.md`。入口 `appstore/submission_kit_instructions.md`、固有値 `appstore/app_input.md`)。
- **実装完了(起動アニメーションを含む)をオーナーが宣言するまで、App Store 提出用の Archive・アップロード・App Store Connect の操作に触れない。提案もしない。** TestFlight 用ビルドは、オーナーが指示した時だけ。
- 審査への返信文・回答案は、**Apple から実際のメッセージが届き、オーナーが文面を渡した時だけ**(雛形 `appstore/after_review/`)。未申請では作らない・埋めない。提出時の「審査メモ」(`appstore/review_notes_template.md`)は別物で、提出前チェックの通過後に作る。
- **自動入力**(`appstore/automation/README.md`): 実装完了の宣言の後、オーナーが指示した時だけ。`plan` で差分 → 会話で明確に OK → `apply`。**価格は二段階**(`--confirm-price` に地域と金額を打ち直す。新規の設定のみ)。年齢制限は実際の内容に基づく。**審査への提出・個人情報・App Privacy・レコード作成・ビルドのアップロードは手動。**鍵はコミットも貼り付けもしない。クラウドでは使わない。
- 公開ページ(`web/` の雛形、GiveTeX の `apps/{スラッグ}/`)は、**申請と同時に(遅くとも前に)本番で公開済みに**。スクリーンショットは `appstore/screenshots.md`(シミュレータ。捏造しない。テスト広告・デバッグ表示を写さない)。記録先: `docs/testflight_feedback.md`。
