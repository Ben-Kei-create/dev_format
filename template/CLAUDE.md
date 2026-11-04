# 開発ルール(App Store 審査対策)

このリポジトリでは、リジェクトを避けるため、次の段階チェックを必ず行う。

- 新しいアプリ/大きな機能の実装前: `review_prompts/1_planning.md` を実行する。
- 主要機能ができた時: `review_prompts/2_development.md` を実行し、TestFlight を開始する。
- 申請の直前: `review_prompts/3_submission.md` を実行する。
- 各段階の判定が「低」なら、次に進まず、まず私に報告する。
- 開発の経緯は `docs/devlog.md` に、競合との違いは `docs/competitor_notes.md` に、
  テスターの意見は `docs/testflight_feedback.md` に、その都度記録する。
- 他の自分のアプリとコードや画面構成が同型にならないよう、共通化は標準的な部品に留める。
- 個人情報(名前、電話、メール、住所、パスワード、鍵・トークン、広告ID等)は、コミット・PR・公開ページに決して含めない。
  実値は `private/owner_info.md`(.gitignore 済み)にだけ置く。コミット前に `git diff --cached` で確認する。
- App Store Connect の申請準備は `appstore/submission_kit_instructions.md` に従い、アプリ固有の値は `appstore/app_input.md` に書く。
- 申請用のコピペリスト `appstore/kit.md` は、審査チェックの段階1〜3が全て通過してから作る。個人情報は `{{キー}}` で書き、実値は `./scripts/fill_private.sh` で `private/` に出力する(コミットしない)。
- `private/` 配下(owner_info.md、kit_filled.md)は、読まない・表示しない・チャットに貼らない。中身が必要な作業は、スクリプトに任せ、AI は中身を見ない。
- セッション開始時に `./scripts/cleanup_private.sh --stale` を実行し、期限切れの `private/kit_filled.md` を削除する。
- `kit_filled.md` を作ったら、必ず「申請は済みましたか?」と確認する。「済んだ」と答えたら、すぐ `./scripts/cleanup_private.sh --now` で削除する。確認が取れない場合も、期限(既定180分)で自動削除されるため、そのまま放置せず、次のセッションでも再度確認する。
