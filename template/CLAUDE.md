# 開発ルール(dev_format)

迷ったら `philosophy/development_philosophy.md`(機能は削る。体験は削らない)に戻る。
詳細は各ファイルに書いてある。ここには要点と参照先だけを置く。

## 常に守る
- 審査・安全・個人情報・「変更不可」は常に100%守る。ダイスや縛りでは変えない。
- 個人情報(姓名、メール、電話、住所、パスワード、鍵・トークン)は、コミット・PR・公開ページ・チャットに決して書かない。
  申請キットでは、姓名・メールは「本人が手入力」とし、電話番号は `+81 XXXXXXXXXX` の形にする。
- 各段階の判定が「低」なら、次に進まず、まずオーナーに報告する。
- 会話: 説明は必要最低限。入力を求める時と、オーナーへの手順の指示だけ丁寧に具体的に。結論から。繰り返さない。
- (推奨・ルールではない) 応答の最後は、次の一手を3つおすすめし、4つ目はオーナーの自由な指示、の4択で続ける。
- コマンド・スキル・モデルは `workflow/command_guide.md` に従う。無関係な作業の前は `/clear`、重くなったら `/compact`。`/code-review max` はオーナーが明示した時だけ。
- フォーマットのうち、更新してよいのは `ExperiencePoints.md` だけ。更新は、そのアプリの開発と申請が終わった後に、
  候補をオーナーに見せ、承認された分を `dev_format` リポジトリ側に追記する。ルール・雛形・指示文は、指示がない限り変更しない(アプリ固有の `docs/` の記録は更新してよい)。

## 進め方(新規アプリ)
1. **企画(コードを書く前)**: `review_prompts/0_brief_intake.md`
   (ExperiencePoints → ダイス `randomdice.md` → 3つの質問 `modes/custom_mode.md` → アイコン用プロンプト `modes/icon_prompt.md` → 設計書の再設計)。
   続けて `1_planning.md` と `1b_growth.md`。
2. **実装**: 画面デザイン(アイコン、ホーム、代表的な操作画面)を確定してから入る。実装完了とリリース完了は区別する。
   起動時アニメーションは、他の実装が全て済んでから最後に作る(`modes/launch_animation.md`。指示がなければパラパラ漫画方式。画像の指示プロンプトも出す)。
3. **開発中**: `2_development.md` と `2b_edge_cases.md`。TestFlight を始める。区切りで Codex レビュー(`codex_review.md`)。
4. **提出前**: `3_submission.md`。通過してから `appstore/kit.md` を作る(`appstore/submission_kit_instructions.md`、固有値は `appstore/app_input.md`)。
5. **申請後**: `ExperiencePoints.md` への追記候補をオーナーに見せる。

実装が進んでいる、または申請まで済んだアプリを渡された時は、上の代わりに `review_prompts/existing_app.md`
(ダイスは振らない。診断 → 質問 → 解決するまで対応)。

記録先: `docs/devlog.md`(経緯)、`competitor_notes.md`(競合)、`testflight_feedback.md`、`deviation_log.md`(設計からの逸脱)、`edge_cases.md`、`mode_log.md`、`asset_list.md`。

## 設計・デザイン
- 詳細設計書(`docs/design_brief.md`)と参考画像は「出発点」。売れない・埋もれないために、より良い方向があれば採用してよい。
  「変更不可」は変えない。小さな逸脱は採用して `deviation_log.md` に記録し、大きな逸脱(コンセプト、ターゲット、名前、収益化、主要機能)は実装前にオーナーへ短く確認する。
- 参考画像は雰囲気にとどめ、画面構成・素材・ロゴ・キャラクターを真似しない。
- 縛りの優先順位: 審査・安全 > 変更不可 > 3つの縛り(Era / Rule / Voice) > ダイス > その他。ダイスの出目は自分で決めない。
- 差別化と売れる見込みは `growth/launch_playbook.md`。デザインは `philosophy/design_principles.md`、技術は `philosophy/tech_standards.md`。
- フォントは `philosophy/fonts.md` の固定リスト(日本語5種・英語5種)から選ぶ。リスト外は許可なしに使わない。
- 姉妹アプリ・仕組みの再利用は歓迎するが、体験・見た目・名前を明確に変え、単体で独立した価値を持たせる(4.3 対策)。共通化は標準的な部品に留める。

## 素材
- コードだけの UI で出せない質感(全体背景、ボタン装飾、空の状態のイラストなど)は、`modes/asset_requests.md` に従い、
  ChatGPT 用のプロンプト・サイズ・形式・保存名・使う場所を都度オーナーに指示する。効果が大きい所に絞る。AI は画像を生成・加工しない。
- アイコンの書き出しは行わない。

## 申請・公開
- 公開ページは `web/` の雛形から作り、GiveTeX サイトの `apps/{スラッグ}/` に置く(PR → 承認 → マージ)。
  **申請と同時に(遅くとも申請の前に)本番で公開済みにする。**申請後に作らない(広告と App Store Connect のURL入力のため)。
- スクリーンショットは `appstore/screenshots.md` に従い、Xcode のシミュレータで撮る。捏造しない。テスト広告・デバッグ表示は写さない。

## 宣伝(X)
- 既定の開発者アカウントは https://x.com/AIJAPANE。AI は X を操作できない。TestFlight 募集・開発ログ・ローンチ・返信の下書きとハッシュタグ案を `marketing/` の雛形で作り、`docs/marketing_posts.md` に保存する。投稿はオーナーが行う。
- 開発中(段階2)でテスター募集の下書き、リリース前に告知とローンチの下書きを用意する。実装されていない機能・誇張・個人情報は書かない。

## 役割
- Claude Code: 企画・実装・修正に集中する。レビュー・校正・第二の意見は ChatGPT / Codex に任せる(Claude の負荷を下げる)。
- 渡す指示文と添付物は `review_prompts/external/README.md`(企画 / 画面 / コード / 文面)。結果は「Claude Code への修正依頼」だけを受け取り、【重大】【推奨】から直す。
- オーナーが判断する。外部レビューは意見であり仕様ではない。
