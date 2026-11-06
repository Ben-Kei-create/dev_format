
## 技術別ルール: Godot(ゲーム。初版。詳細は `workflow/godot_export.md`)
- 書き出し先のストア(`stores/`)のルールが、そのまま適用される。エディタとエクスポートテンプレートのバージョンは一致させる。
- 書き出し(Xcode プロジェクト、Archive、アップロード、AAB)は、オーナーが実装完了を宣言し、指示するまで行わない。
- Android は `gradle_build/target_sdk` を明示的に 36 以上にし、書き出した AAB のマニフェストで確認する。iOS は macOS + Xcode が必要。
- 素材は `workflow/tools_catalog.md`。Godot Asset Library はアセットごとにライセンスが違うので個別に確認。広告プラグインは、ライセンス・同意管理・申告への影響を確認してから採用。
- 起動アニメーションは Godot 内で(`modes/launch_animation.md`)。実機で、画面サイズ・向き・セーフエリア・タッチ・音量・バックグラウンド復帰を確認する。
