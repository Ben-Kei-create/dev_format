
## 技術別ルール: Android ネイティブ(初版。詳細は `workflow/android_guide.md`)
- Kotlin + Jetpack Compose。データは端末内保存(小さな設定は DataStore、構造化データは Room)、バックエンドなし、依存は最小限(「機能は削る」)。
- ターゲット API 36 以上(2026-08-31 以降の要件)。ビルドは AAB。キーストアとパスワードは、コミットもチャット貼り付けもしない。
- フォントは `res/font` + `sp`(`philosophy/fonts.md` の固定リストのみ)。TalkBack のラベル、コントラスト、タップ領域 48dp 以上、文字拡大。
- 起動: OS のスプラッシュは静止。アニメは直後に Compose 内で(`modes/launch_animation.md`)。アニメーションの倍率が 0 の時は、最後のフレームを静止で(自前のタイマーは自動では守らない。`workflow/android_guide.md`)。
- 実機で、画面サイズ・Android バージョン・向き・ダークモード・文字拡大を確認する。
