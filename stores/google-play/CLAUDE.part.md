
## ストア別ルール: Google Play(初版。公式で要確認の項目あり)
- 企画: `review_prompts/1_planning.md`(Repetitive Content = 似たアプリを複数出さない、Minimum Functionality など)。
- 開発中: `review_prompts/2_development.md`。**個人アカウント(2023-11-13 以降に作成)は、本番公開の申請前に、クローズドテストで 12 人以上のテスターを 14 日間継続して参加させる必要がある**(`workflow/closed_testing.md`)。テスターの募集は X(`marketing/`)で行い、AI が下書きを作る。クローズドテスト用ビルドのアップロードは、オーナーが指示した時だけ。
- 提出前: `review_prompts/3_submission.md`。通過してから、掲載情報の申請キット(`playstore/listing_kit.md`)を作る。
- **実装完了(起動アニメーションを含む)をオーナーが宣言するまで、本番公開用のビルドのアップロード・Play Console の公開操作に触れない。提案もしない。**
- 審査への返信文・Google からの質問への回答案は、**Google から実際のメッセージが届き、オーナーが文面を渡した時だけ**作る。未申請では作らない。
- 宣言の内容(広告、アプリのアクセス、ターゲット層、コンテンツレーティング、データセーフティ、プライバシーポリシー)は `playstore/app_content_and_data_safety.md`。実装と必ず一致させる。
- スクリーンショット・アイコン・フィーチャーグラフィックは `playstore/screenshots.md`。エミュレータまたは実機で撮る。捏造しない。テスト広告・デバッグ表示は写さない。
- 公開ページ(プライバシーポリシーなど)は `web/` の雛形から作り、申請の前に本番で公開済みにする(Apple と同じ)。
- 記録先(Google Play 固有): `docs/closed_test_feedback.md`。
