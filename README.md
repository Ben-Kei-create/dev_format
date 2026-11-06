# dev_format

新しいアプリを作る時に使う、開発フォーマット集(オーナー専用)。
App Store のリジェクト(4.3 重複・スパム、4.2.6 テンプレート等)を避けつつ、売れる・埋もれないアプリにするための、段階別チェック、設計の仕組み、記録の雛形を入れている。

## 構成
```
dev_format/
├─ core/            共通(全アプリ・全ストア・全技術で使う)
├─ stores/
│   ├─ apple/       App Store(審査チェック、申請キット、TestFlight、スクリーンショット)
│   └─ google-play/ 初版(クローズドテスト、掲載情報、宣言、審査チェック)
├─ engines/
│   ├─ swiftui/     SwiftUI(iPhone / macOS)
│   ├─ godot/       未整備
│   └─ android/     未整備
└─ setup.sh         core + ストア + 技術 を、新規アプリに同じ相対パスでコピーする
```

### core/(共通)
- `CLAUDE.md`(共通ルール)、`ExperiencePoints.md`(知見。申請完了後に更新できる唯一のファイル)、`randomdice.md`(依存度ダイス)
- `philosophy/`(開発思想、デザイン原則、固定フォント、技術の標準)、`growth/`(差別化プレイブック)
- `modes/`(Era / Rule / Voice の3つの質問、アイコン用プロンプト、画面デザインの参考画像(インタビュー形式)、画像素材の依頼、起動アニメーション、音声)
- `review_prompts/`(0 受け取り、1b 差別化、2b 想定外、Codex レビュー、既存アプリ診断、`external/`=ChatGPT・Codex 向けレビュー指示)
- `marketing/`(X での宣伝。既定 @AIJAPANE)、`web/`(公開ページの雛形。GiveTeX 用)、`workflow/`(コマンド・スキル・モデルの使い分け、使うツール・素材のカタログ)
- `docs/`(記録の雛形)、`scripts/`(ダイス、pre-commit)、`.gitignore`

### stores/apple/
- `CLAUDE.part.md`(Apple 固有のルール)
- `review_prompts/`(1 企画、2 開発中、3 提出前)
- `appstore/`(申請キット指示書、審査メモの雛形、スクリーンショット手順、`after_review/`=Apple から実際のメッセージが届いた時だけ使う返信の雛形)
- `workflow/testflight.md`、`docs/testflight_feedback.md`

### engines/swiftui/
- `CLAUDE.part.md`(SwiftUI 固有のルール)

## 新規アプリへの導入
```bash
git clone https://github.com/Ben-Kei-create/dev_format
cd dev_format
./setup.sh /path/to/new-app-repo                         # 既定: --store apple --engine swiftui
./setup.sh /path/to/new-app-repo --store apple --engine swiftui
```
- 既存のファイルは上書きしない。`CLAUDE.md` は、共通 + ストア別 + 技術別をつなげて作る(既に `CLAUDE.md` がある場合は、部品を手動で追記する)。
- 未整備の組み合わせ(google-play、godot、android)を選ぶと、共通ルールだけが入る。最初に使う時に整備する。
- コピー後、新規アプリのリポジトリでコミットする。

## 更新
チェック項目を改善したら、このリポジトリを更新し、使っているアプリ側にも再度コピーする。
更新してよいのは、オーナーの指示がある時と、`ExperiencePoints.md`(申請完了後)だけ。
