
## 技術別ルール: SwiftUI(iPhone / macOS)
- Swift / SwiftUI を基本とする(`philosophy/tech_standards.md`)。データは端末内保存を優先し、バックエンドは必要性が明確になるまで入れない。
- フォントは Bundle に入れ、`UIAppFonts` に登録し、Dynamic Type に追従させる(`philosophy/fonts.md` の実装の注意)。
- 起動時アニメーションの実装は `modes/launch_animation.md` の「実装の指針(iOS / SwiftUI)」。
- スクリーンショット用の撮影モード(`-SCREENSHOT_MODE`)は、`appstore/screenshots.md`(Apple 側)に従う。
- デザインシステム(Astryx など外部のもの)を使う案が出た時は `workflow/astryx_tokens.md`。既定は丸ごと採用せず、トークンの考え方だけ借りる。
