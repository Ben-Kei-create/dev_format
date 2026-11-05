# 申請キット指示書: 初回専用: 登録の順序(§7)

(入口: `appstore/submission_kit_instructions.md`)

## 7. 初回専用: 登録の順序
- Apple Developer → Certificates, Identifiers & Profiles → Identifiers: App ID の有無を確認。未登録なら登録手順を示す。明示的 App ID、Bundle ID、必要な Capabilities を、実装に照らして示す。Xcode の署名設定と一致させる。
- App Store Connect → アプリ → + → 新規アプリ: プラットフォーム/名前/プライマリ言語/Bundle ID/SKU/ユーザアクセスを、ラベルごとに入力・選択方法付きで示す。
- 初回の注意: Apple ID はレコード作成後に表示される。更新時に既存の SKU や Bundle ID を再入力させない。
