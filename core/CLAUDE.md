# 開発ルール(dev_format)

迷ったら `philosophy/development_philosophy.md`(機能は削る。体験は削らない)。詳細は各ファイル。ここは要点と参照先だけ。

## 常に守る
- 審査・安全・個人情報・「変更不可」は常に100%。ダイスや縛りでは変えない。判定が「低」なら、次に進まず報告する。
- 個人情報(姓名、メール、電話、住所、パスワード、鍵・トークン)は、コミット・PR・公開ページ・チャットに書かない。申請キットでは姓名・メールは「本人が手入力」、電話は `+81 XXXXXXXXXX`。
- 会話: 説明は最低限。入力を求める時と手順の指示だけ丁寧に。結論から。(推奨・ルールではない)約8割は、おすすめ3つ + 自由な指示1つの選択肢で進める。
- 更新してよいフォーマットは `ExperiencePoints.md` だけ(申請完了後に候補を見せ、承認分を `dev_format` 側に追記)。他は指示がない限り変えない(アプリ固有の `docs/` は可)。
- コマンド・スキル・モデルは `workflow/command_guide.md`。無関係な作業の前は `/clear`、重くなったら `/compact`。`/code-review max` は明示された時だけ。
- **ChatGPT への画像生成の指示と、ChatGPT / Codex へのレビュー指示は、ダイスに関係なく、常に自分から出す**(場面は `review_prompts/external/README.md` の表。出さない時は理由を一行)。Claude は企画・実装・修正に集中する。結果は「Claude Code への修正依頼」の【重大】【推奨】だけ受け取る。外部レビューは意見で、判断はオーナー。

## 進め方(新規アプリ)
1. **企画**: `review_prompts/0_brief_intake.md`(ExperiencePoints → ダイス `randomdice.md` → 3つの質問 `modes/custom_mode.md` → アイコン用プロンプト `modes/icon_prompt.md` → 設計書の再設計)。続けて `1b_growth.md` と、ストア別の企画チェック。
2. **実装**: 画面デザイン(アイコン、ホーム、代表的な操作画面)を確定してから。実装完了とリリース完了は区別する。起動アニメーションは最後(`modes/launch_animation.md`)。
3. **開発中**: `2b_edge_cases.md` とストア別の開発中チェック。区切りで `codex_review.md`。テスト配布はオーナーが指示した時だけ。
4. **提出前**: ストア別の提出前チェック → 通過後に申請キット。
5. **申請後**: `ExperiencePoints.md` への追記候補を見せる。

実装が進んだ/申請済みのアプリは、代わりに `review_prompts/existing_app.md`(ダイスなし。診断 → 質問 → 解決まで)。
末尾の「ストア別ルール」「技術別ルール」は `setup.sh` が追記する。記録先は `docs/`(`devlog.md`、`competitor_notes.md`、`deviation_log.md`、`edge_cases.md`、`mode_log.md`、`asset_list.md`)。

## 設計・デザイン
- 詳細設計書(`docs/design_brief.md`)と参考画像は出発点。売れない・埋もれないために、より良い方向なら採用してよい。「変更不可」は変えない。小さな逸脱は `deviation_log.md` に記録、大きな逸脱(コンセプト、ターゲット、名前、収益化、主要機能)は実装前に確認する。参考画像は雰囲気にとどめ、構成・素材・ロゴ・キャラクターを真似しない。
- 優先順位: 審査・安全 > 変更不可 > 3つの縛り(Era / Rule / Voice) > ダイス > その他。ダイスの出目は自分で決めない。
- 差別化は `growth/launch_playbook.md`、デザインは `philosophy/design_principles.md`、技術は `philosophy/tech_standards.md`。フォントは `philosophy/fonts.md` の固定リスト(日本語6種・英語5種)のみ。
- 姉妹アプリ・仕組みの再利用は歓迎するが、体験・見た目・名前を明確に変え、単体で独立した価値を持たせる(4.3 対策)。

## 素材
- 作る前に `workflow/tools_catalog.md` で探して積極的に使う。**使う前に商用利用・クレジット・再配布を公式で確認し、`docs/asset_list.md` に出典・条件・確認日を記録。**確認できないものは使わない。同じ素材パックだけで作らない。
- コードで出せない質感は `modes/asset_requests.md` に従い、ChatGPT 用の指示(プロンプト・サイズ・形式・保存名・使う場所)を都度出す。AI は画像を生成・加工しない。アイコンの書き出しは行わない。
- 音声は `modes/voice_audio.md`(アプリ内の読み上げは OS 標準、事前に作る音声は AivisSpeech の ACML/CC0 を第一候補。声のライセンスを必ず確認)。
- アイコンや他の場面・他アプリのアニメーション・演出・素材は、なるべく使い回さない(コードの部品の共通化は可)。

## 宣伝(X)
- 既定は https://x.com/AIJAPANE。AI は操作できない。`marketing/` の雛形で、募集・開発ログ・告知・ローンチ・返信の下書きとハッシュタグ案を作り、`docs/marketing_posts.md` に保存。投稿はオーナー。未実装の機能・誇張・個人情報は書かない。
