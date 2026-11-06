
## 技術別ルール: Godot(ゲーム。初版。公式で要確認の項目あり)
- 2D・3D ゲームの標準エンジン(`philosophy/tech_standards.md`)。**書き出し先のストアのルールが、そのまま適用される**(App Store → `stores/apple/`、Google Play → `stores/google-play/`)。Godot は作り方であり、審査・ポリシーの対象は変わらない。
- 書き出しの手順・設定・ストアとの関係は `workflow/godot_export.md`。ビルドのバージョンは、エディタとエクスポートテンプレートを必ず一致させる。
- Android 向けは、**`gradle_build/target_sdk` を明示的に API 36 以上にし、書き出した AAB のマニフェストで確認する**(2026-08-31 以降の要件。`workflow/godot_export.md`)。
- iOS 向けの書き出しには macOS と Xcode が必要。書き出し(Xcode プロジェクトの生成、Archive、アップロード)は、**オーナーが実装完了を宣言し、指示するまで行わない**(テスト配布は、指示された時だけ)。
- 素材は `workflow/tools_catalog.md`(Kenney、Poly Haven、Quaternius、Mixamo、Pixelorama、Godot Asset Library)を第一候補にする。**Godot Asset Library はアセットごとにライセンスが違う。**個別に確認して `docs/asset_list.md` に記録。
- 起動時アニメーションは Godot 内で実装する(`modes/launch_animation.md`)。OS の起動画面と、エンジンの起動スプラッシュ(ロゴ)の扱いは、プロジェクト設定で確認する。
- 広告(AdMob など)は、Godot 用のプラグインを使う場合、**プラグインのライセンス・SDK のバージョン・同意管理(UMP / ATT)・プライバシー申告への影響を確認してから**採用する。
- 画面サイズ・向き・ノッチ(セーフエリア)・タッチ操作・文字の拡大・音量・バックグラウンド復帰を、実機で確認する。
