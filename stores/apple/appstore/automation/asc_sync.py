#!/usr/bin/env python3
"""App Store Connect: メタデータ(テキスト)の差分確認と反映。

- `plan`  : 読み取りのみ(GET)。現在の値との差分を表示する。何も書き込まない。
- `apply` : オーナーが差分を確認して OK した後にだけ実行する。変更前の値を private/ に保存してから PATCH する。
- 対象: バージョンの掲載文(説明・キーワード・プロモーション文・サポート/マーケティングURL・新機能)、
        アプリ情報(名前・サブタイトル・プライバシーポリシーURL)、審査メモ(notes)。
- 対象外(手動): アプリのレコード作成、ビルドのアップロード、App Privacy、審査連絡先(姓名・メール・電話)、
        スクリーンショット、価格、審査への提出。
- 認証: 環境変数 ASC_KEY_ID / ASC_ISSUER_ID / ASC_KEY_PATH(.p8 のパス)。鍵はリポジトリに置かない・表示しない。
- 依存: pip install pyjwt cryptography
状態: 実際の API では未実行(テストは偽の応答のみ)。最初は必ず `plan` だけを実行すること。
"""
import argparse, json, os, pathlib, re, sys, time, urllib.error, urllib.parse, urllib.request, datetime

BASE = "https://api.appstoreconnect.apple.com"
# 文字数の上限(Apple の仕様。変わり得るので、超過は警告にとどめず、エラーにして止める)
VERSION_LOC_FIELDS = {"description": 4000, "keywords": 100, "marketingUrl": None,
                      "promotionalText": 170, "supportUrl": None, "whatsNew": 4000}
APPINFO_LOC_FIELDS = {"name": 30, "subtitle": 30, "privacyPolicyUrl": None}
REVIEW_FIELDS = {"notes": 4000}
EDITABLE_STATES = {"PREPARE_FOR_SUBMISSION", "DEVELOPER_REJECTED", "REJECTED", "METADATA_REJECTED"}

EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")
PHONE = re.compile(r"(?:\+81[ -]?\(?0?\)?[1-9][0-9 -]{7,}|(?<![0-9])0[1-9]0?[ -]?[0-9]{3,4}[ -]?[0-9]{4}(?![0-9]))")
OK_EMAIL_DOMAINS = ("example.com", "example.org", "example.net")


class SyncError(Exception):
    pass


# ---------- 入力の検証 ----------
def iter_strings(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from iter_strings(v, f"{path}.{k}" if path else k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from iter_strings(v, f"{path}[{i}]")
    elif isinstance(obj, str):
        yield path, obj


def validate(data):
    """問題の一覧(文字列)を返す。空なら OK。"""
    errs = []
    for key in ("bundleId", "versionString"):
        if not isinstance(data.get(key), str) or not data[key]:
            errs.append(f"{key} が必要です")
    allowed_top = {"bundleId", "versionString", "versionLocalizations", "appInfoLocalizations", "reviewDetail"}
    for k in data:
        if k not in allowed_top:
            errs.append(f"未対応のキー: {k}(対象外。手動で入力してください)")

    def check_group(group, allowed, label):
        for loc, fields in (data.get(group) or {}).items():
            if not isinstance(fields, dict):
                errs.append(f"{label}.{loc} はオブジェクトにしてください")
                continue
            for f, v in fields.items():
                if f not in allowed:
                    errs.append(f"{label}.{loc}.{f} は対象外の項目です(手動で入力してください)")
                elif not isinstance(v, str):
                    errs.append(f"{label}.{loc}.{f} は文字列にしてください")
                elif allowed[f] is not None and len(v) > allowed[f]:
                    errs.append(f"{label}.{loc}.{f} が上限 {allowed[f]} 文字を超えています(現在 {len(v)} 文字)")

    check_group("versionLocalizations", VERSION_LOC_FIELDS, "versionLocalizations")
    check_group("appInfoLocalizations", APPINFO_LOC_FIELDS, "appInfoLocalizations")
    rd = data.get("reviewDetail") or {}
    for f, v in rd.items():
        if f not in REVIEW_FIELDS:
            errs.append(f"reviewDetail.{f} は対象外の項目です(審査連絡先などの個人情報は手動で入力)")
        elif not isinstance(v, str):
            errs.append(f"reviewDetail.{f} は文字列にしてください")
        elif len(v) > REVIEW_FIELDS[f]:
            errs.append(f"reviewDetail.{f} が上限 {REVIEW_FIELDS[f]} 文字を超えています(現在 {len(v)} 文字)")
    # 個人情報の混入を止める
    for path, s in iter_strings(data):
        for m in EMAIL.findall(s):
            if not m.lower().endswith(OK_EMAIL_DOMAINS):
                errs.append(f"{path}: メールアドレスらしい文字列があります(個人情報は入れない)")
        if PHONE.search(s):
            errs.append(f"{path}: 電話番号らしい文字列があります(個人情報は入れない)")
    return errs


# ---------- API クライアント ----------
class Client:
    def __init__(self, transport=None):
        self._transport = transport or self._http
        self._token = None
        self._exp = 0

    def _make_token(self):
        try:
            import jwt  # PyJWT
        except ImportError:
            raise SyncError("pyjwt と cryptography が必要です: pip install pyjwt cryptography")
        try:
            key_id = os.environ["ASC_KEY_ID"]
            issuer = os.environ["ASC_ISSUER_ID"]
            key_path = os.environ["ASC_KEY_PATH"]
        except KeyError as e:
            raise SyncError(f"環境変数 {e.args[0]} が未設定です")
        with open(key_path, "rb") as f:
            private_key = f.read()
        now = int(time.time())
        payload = {"iss": issuer, "iat": now, "exp": now + 15 * 60, "aud": "appstoreconnect-v1"}  # 上限は20分
        self._exp = now + 15 * 60
        return jwt.encode(payload, private_key, algorithm="ES256", headers={"kid": key_id, "typ": "JWT"})

    def _auth(self):
        if not self._token or time.time() > self._exp - 60:
            self._token = self._make_token()
        return {"Authorization": f"Bearer {self._token}", "Content-Type": "application/json"}

    def _http(self, method, path, params, body):
        url = BASE + path + (("?" + urllib.parse.urlencode(params)) if params else "")
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, method=method, headers=self._auth())
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                raw = r.read()
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="replace")[:500]
            raise SyncError(f"{method} {path} が失敗しました(HTTP {e.code}): {detail}")

    def request(self, method, path, params=None, body=None):
        return self._transport(method, path, params, body)


# ---------- 差分の作成 ----------
def pick_version(client, app_id, version_string):
    res = client.request("GET", f"/v1/apps/{app_id}/appStoreVersions", {"filter[versionString]": version_string})
    items = res.get("data", [])
    if not items:
        raise SyncError(f"バージョン {version_string} がありません。App Store Connect で先にバージョンを作成してください。")
    v = items[0]
    attrs = v.get("attributes", {})
    state = attrs.get("appVersionState") or attrs.get("appStoreState")
    if state not in EDITABLE_STATES:
        raise SyncError(f"バージョンの状態が {state} です。編集できる状態({', '.join(sorted(EDITABLE_STATES))})ではありません。")
    return v["id"], state


def diff_fields(kind, loc, rid, current, wanted, allowed):
    changes = []
    for f in allowed:
        if f in wanted and (current.get(f) or "") != wanted[f]:
            changes.append({"kind": kind, "locale": loc, "id": rid, "field": f,
                            "old": current.get(f), "new": wanted[f]})
    return changes


def build_plan(client, data):
    errs = validate(data)
    if errs:
        raise SyncError("入力に問題があります:\n  - " + "\n  - ".join(errs))
    apps = client.request("GET", "/v1/apps", {"filter[bundleId]": data["bundleId"]}).get("data", [])
    if not apps:
        raise SyncError(f"Bundle ID {data['bundleId']} のアプリが見つかりません。レコードは App Store Connect で先に作成してください。")
    app_id = apps[0]["id"]
    version_id, state = pick_version(client, app_id, data["versionString"])
    changes, notes = [], []

    if data.get("versionLocalizations"):
        remote = client.request("GET", f"/v1/appStoreVersions/{version_id}/appStoreVersionLocalizations").get("data", [])
        by_loc = {r["attributes"]["locale"]: r for r in remote}
        for loc, wanted in data["versionLocalizations"].items():
            r = by_loc.get(loc)
            if not r:
                notes.append(f"versionLocalizations: ロケール {loc} が App Store Connect にありません(先に追加してください)")
                continue
            changes += diff_fields("versionLocalization", loc, r["id"], r["attributes"], wanted, VERSION_LOC_FIELDS)

    if data.get("appInfoLocalizations"):
        infos = client.request("GET", f"/v1/apps/{app_id}/appInfos").get("data", [])
        if not infos:
            notes.append("appInfos が取得できませんでした")
        else:
            info = next((i for i in infos if (i.get("attributes", {}).get("appStoreState") or
                                              i.get("attributes", {}).get("state")) in EDITABLE_STATES), infos[0])
            remote = client.request("GET", f"/v1/appInfos/{info['id']}/appInfoLocalizations").get("data", [])
            by_loc = {r["attributes"]["locale"]: r for r in remote}
            for loc, wanted in data["appInfoLocalizations"].items():
                r = by_loc.get(loc)
                if not r:
                    notes.append(f"appInfoLocalizations: ロケール {loc} がありません(先に追加してください)")
                    continue
                changes += diff_fields("appInfoLocalization", loc, r["id"], r["attributes"], wanted, APPINFO_LOC_FIELDS)

    if data.get("reviewDetail"):
        res = client.request("GET", f"/v1/appStoreVersions/{version_id}/appStoreReviewDetail").get("data")
        if not res:
            notes.append("appStoreReviewDetail がありません(App Store Connect で審査情報を一度保存してください)")
        else:
            changes += diff_fields("reviewDetail", "-", res["id"], res["attributes"], data["reviewDetail"], REVIEW_FIELDS)

    return {"appId": app_id, "versionId": version_id, "versionState": state, "changes": changes, "notes": notes}


ENDPOINTS = {
    "versionLocalization": ("appStoreVersionLocalizations", "/v1/appStoreVersionLocalizations/{id}"),
    "appInfoLocalization": ("appInfoLocalizations", "/v1/appInfoLocalizations/{id}"),
    "reviewDetail": ("appStoreReviewDetails", "/v1/appStoreReviewDetails/{id}"),
}


def apply_plan(client, plan, backup_dir):
    """差分を PATCH する。変更前の値を backup_dir に保存してから実行する。"""
    backup_dir = pathlib.Path(backup_dir)
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = backup_dir / f"asc_backup_{stamp}.json"
    backup.write_text(json.dumps(plan["changes"], ensure_ascii=False, indent=2), encoding="utf-8")
    grouped = {}
    for c in plan["changes"]:
        grouped.setdefault((c["kind"], c["id"]), {})[c["field"]] = c["new"]
    done = 0
    for (kind, rid), attrs in grouped.items():
        rtype, path = ENDPOINTS[kind]
        body = {"data": {"type": rtype, "id": rid, "attributes": attrs}}
        client.request("PATCH", path.format(id=rid), None, body)
        done += 1
    return str(backup), done


def show_plan(plan):
    print(f"アプリ ID: {plan['appId']} / バージョン状態: {plan['versionState']}")
    if not plan["changes"]:
        print("変更はありません。")
    for c in plan["changes"]:
        old = (c["old"] or "")
        print(f"- [{c['kind']} {c['locale']}] {c['field']}")
        print(f"    現在: {old[:80]!r}{'…' if len(old) > 80 else ''}")
        print(f"    新規: {c['new'][:80]!r}{'…' if len(c['new']) > 80 else ''}  ({len(c['new'])}文字)")
    for n in plan["notes"]:
        print(f"! {n}")


def main(argv=None, client=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["plan", "apply"])
    ap.add_argument("input")
    ap.add_argument("--confirm-bundle-id", help="apply の時に必須。入力の bundleId と同じ値を指定する")
    ap.add_argument("--backup-dir", default="private")
    args = ap.parse_args(argv)
    try:
        data = json.loads(pathlib.Path(args.input).read_text(encoding="utf-8"))
        client = client or Client()
        plan = build_plan(client, data)
        show_plan(plan)
        if args.command == "plan":
            print("\n(読み取りのみ。何も書き込んでいません。)")
            return 0
        if args.confirm_bundle_id != data["bundleId"]:
            raise SyncError("apply には --confirm-bundle-id <Bundle ID> が必要です(オーナーが差分を確認して OK した後にだけ実行する)")
        if not plan["changes"]:
            return 0
        backup, n = apply_plan(client, plan, args.backup_dir)
        print(f"\n{n} 件の更新を送信しました。変更前の値: {backup}(コミットしない)")
        print("次: App Store Connect の画面で内容を確認してください。審査への提出は手動で行います。")
        return 0
    except SyncError as e:
        print(f"中止: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
