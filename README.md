# dev_format

新しいアプリを作る時に使う、開発フォーマット集。App Store のリジェクト(4.3 重複・スパム、4.2.6 テンプレート等)を避けるための、段階別チェックと記録テンプレートを入れている。

## 中身(`template/`)
- `CLAUDE.md`: Claude Code が起動時に読む開発ルール
- `review_prompts/`: 審査・品質チェック指示文(0 受け取り / 1 企画 / 2 開発中 / 3 提出前 / ChatGPT・Codex レビュー / 既存アプリ)
- `docs/`: 詳細設計書(依頼メモ)、逸脱ログ、想定外バグ/ユーザー記録、開発ログ、競合メモ、TestFlight 記録
- `web/`: 公開ページ(紹介・サポート・プライバシー)の雛形。GiveTeX サイト用
- `modes/`: カスタムモード(Era / Rule / Voice の3つの質問)、アイコン用プロンプト、画像素材の依頼形式、起動時アニメーション、音声
- `ExperiencePoints.md`: 開発で得た知見をためる場所。申請完了後に、選別して更新する(唯一更新してよいファイル)
- `randomdice.md`: 設計の依存度をダイスで決める仕組み(`scripts/roll_dice.sh`、`scripts/roll_research.sh`)
- `marketing/`: X(既定 @AIJAPANE)での TestFlight 募集・宣伝のプレイブックと投稿の雛形
- `workflow/`: コマンド・スキル・モデルの使い分けガイド(品質とトークン節約)
- `philosophy/`: オーナーの開発思想、デザイン共通原則、固定フォント、技術・設計の標準方針
- `growth/`: 初回リリース・差別化のプレイブック(自分用)
- `appstore/`: App Store Connect 申請キット作成指示書、アプリ固有の入力欄
- `scripts/`: ダイス、pre-commit(メール・電話番号らしい文字列や `private/` のファイルを含むコミットを中止)、フック導入
- `.gitignore`: 個人情報・鍵類をコミットしない設定

## 新規アプリへの導入
```bash
git clone https://github.com/Ben-Kei-create/dev_format
cd dev_format
./setup.sh /path/to/new-app-repo
```
コピー後、新規アプリのリポジトリでコミットする。既に `CLAUDE.md` がある場合は、`template/CLAUDE.md` の内容を追記する。

## 更新
チェック項目を改善したら、このリポジトリを更新し、使っているアプリ側にも再度コピーする。
