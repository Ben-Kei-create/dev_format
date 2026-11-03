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
