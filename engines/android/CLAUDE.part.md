
## 技術別ルール: Android ネイティブ(初版。公式で要確認の項目あり)
- **標準**: Kotlin + Jetpack Compose。UI は Compose を基本とし、画面ごとに状態(ViewModel + StateFlow)を持つ。迷ったら公式の「Guide to app architecture」(developer.android.com)に従う。
- データは**端末内保存を優先**(設定は DataStore、構造化データは Room)。バックエンドは、必要性が明確になるまで入れない(`philosophy/tech_standards.md`)。
- 依存を増やさない(「機能は削る」)。DI(Hilt など)や外部ライブラリは、必要が明確な時だけ。
- **ターゲット API レベル**: 2026-08-31 以降、新規アプリと更新は Android 16(API 36)以上(`stores/google-play/`)。minSdk は、対象ユーザーの端末の分布を見て決め、理由を `docs/design_brief.md` に書く。
- ビルド形式は Android App Bundle(AAB)。リリース用のキーストアとパスワードは、**リポジトリにコミットしない・チャットに出さない**。
- フォントは `res/font` に入れ、サイズは `sp` で指定する(端末の文字サイズ設定に追従)。`philosophy/fonts.md` の固定リストのみ。
- アクセシビリティ: TalkBack のラベル、十分なコントラスト、タップ領域(48dp 以上を目安)、文字拡大。
- 起動: OS の起動画面(Android 12 以降のスプラッシュ。背景色とアイコン)は静止。パラパラ漫画のアニメーションは、その直後に Compose 内で流す(`modes/launch_animation.md`)。「アニメーションを減らす」設定(アニメーション倍率が 0)の時は、最後のフレームを静止で表示する。
- スクリーンショットは `stores/google-play/playstore/screenshots.md` に従い、エミュレータまたは実機で撮る。
- テスト: 実機で、複数の画面サイズ・Android バージョン・向き・ダークモード・文字拡大を確認する。
