
## ストア別ルール: Apple(App Store)
- 審査への返信文・Apple の質問への回答案は、**Apple から実際のメッセージが届き、オーナーが文面を渡した時だけ**作る。未申請のアプリでは作らない・雛形(`appstore/after_review/`)を埋めない。提出時の「審査メモ」(`appstore/review_notes_template.md`)は別物で、提出前チェックに通過してから作る。
- **実装完了(起動アニメーションを含む)をオーナーが宣言するまで、App Store 提出用の Archive・アップロード・App Store Connect の操作に触れない。提案もしない。** TestFlight 配布用のビルドは、オーナーが明示的に指示した時だけ(`workflow/testflight.md`)。
- 企画: `review_prompts/1_planning.md`(4.3 重複・スパム、4.2.6 テンプレート、4.2 最小機能)。
- 開発中: `review_prompts/2_development.md`。オーナーが指示したら TestFlight を始める(`workflow/testflight.md`)。
- 提出前: `review_prompts/3_submission.md`。通過してから `appstore/kit.md` を作る(`appstore/submission_kit_instructions.md`、固有値は `appstore/app_input.md`)。
- 記録先(Apple 固有): `docs/testflight_feedback.md`。

### 申請・公開
- 公開ページは `web/` の雛形から作り、GiveTeX サイトの `apps/{スラッグ}/` に置く(PR → 承認 → マージ)。
  **申請と同時に(遅くとも申請の前に)本番で公開済みにする。**申請後に作らない(広告と App Store Connect のURL入力のため)。
- スクリーンショットは `appstore/screenshots.md` に従い、Xcode のシミュレータで撮る。捏造しない。テスト広告・デバッグ表示は写さない。
