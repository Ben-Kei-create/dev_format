#!/usr/bin/env python3
"""App Store Connect: メタデータ(テキスト)の差分確認と反映。

- `plan`  : 読み取りのみ(GET)。現在の値との差分を表示する。何も書き込まない。
- `apply` : オーナーが差分を確認して OK した後にだけ実行する。変更前の値を private/ に保存してから PATCH する。
- 対象: バージョンの掲載文(説明・キーワード・プロモーション文・サポート/マーケティングURL・新機能)、
        アプリ情報(名前・サブタイトル・プライバシーポリシーURL)、審査メモ(notes)、スクリーンショット
        (App Asset Library: 予約 → アップロード → 確定 → 処理待ち → 配置 → 並び順。従来のセット方式は Apple が非推奨にしたため使わない)。
- 対象外(手動): アプリのレコード作成、ビルドのアップロード、App Privacy、審査連絡先(姓名・メール・電話)、
        価格、審査への提出。
- 認証: 環境変数 ASC_KEY_ID / ASC_ISSUER_ID / ASC_KEY_PATH(.p8 のパス)。鍵はリポジトリに置かない・表示しない。
- 依存: pip install pyjwt cryptography
状態: 実際の API では未実行(テストは偽の応答のみ)。最初は必ず `plan` だけを実行すること。
"""
import argparse, json, os, pathlib, re, struct, sys, time, urllib.error, urllib.parse, urllib.request, datetime

BASE = "https://api.appstoreconnect.apple.com"
# 文字数の上限(Apple の仕様。変わり得るので、超過は警告にとどめず、エラーにして止める)
VERSION_LOC_FIELDS = {"description": 4000, "keywords": 100, "marketingUrl": None,
                      "promotionalText": 170, "supportUrl": None, "whatsNew": 4000}
APPINFO_LOC_FIELDS = {"name": 30, "subtitle": 30, "privacyPolicyUrl": None}
REVIEW_FIELDS = {"notes": 4000}
EDITABLE_STATES = {"PREPARE_FOR_SUBMISSION", "DEVELOPER_REJECTED", "REJECTED", "METADATA_REJECTED"}
# スクリーンショット(App Asset Library)。値は Apple の公式ドキュメントの記載
ASSET_CATEGORY = "APP_SCREENSHOTS_AND_PREVIEWS"
PLACEMENT_TYPE = "APP_SCREENSHOT"
MAX_SCREENSHOTS_PER_GROUP = 10  # App Store バージョンの上限(公式)。参照データの groupLimits が正
READY_STATE = "PREPARE_FOR_SUBMISSION"
SHOT_EXT = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}

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
    allowed_top = {"bundleId", "versionString", "versionLocalizations", "appInfoLocalizations", "reviewDetail", "screenshots"}
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
    # スクリーンショットの指定: {ロケール: {配置グループ: [ファイルのパス, ...]}}
    for loc, groups in (data.get("screenshots") or {}).items():
        if not isinstance(groups, dict):
            errs.append(f"screenshots.{loc} はオブジェクト(配置グループ → ファイルの配列)にしてください")
            continue
        for group, files in groups.items():
            if not isinstance(files, list) or not files:
                errs.append(f"screenshots.{loc}.{group} はファイルのパスの配列にしてください")
                continue
            if len(files) > MAX_SCREENSHOTS_PER_GROUP:
                errs.append(f"screenshots.{loc}.{group} が上限 {MAX_SCREENSHOTS_PER_GROUP} 枚を超えています")
            for f in files:
                if not isinstance(f, str) or pathlib.Path(f).suffix.lower() not in SHOT_EXT:
                    errs.append(f"screenshots.{loc}.{group}: {f!r} は .png / .jpg / .jpeg のパスにしてください")
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

    def upload(self, method, url, headers, data):
        """アップロード用の URL へバイト列を送る。認証なし(JWT は送らない)。URL は共有しない・表示しない。"""
        if getattr(self, "_upload_transport", None):
            return self._upload_transport(method, url, headers, data)
        req = urllib.request.Request(url, data=data, method=method, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                return r.status
        except urllib.error.HTTPError as e:
            raise SyncError(f"アップロードに失敗しました(HTTP {e.code})")


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


def build_plan(client, data, base_dir='.'):
    errs = validate(data)
    if errs:
        raise SyncError("入力に問題があります:\n  - " + "\n  - ".join(errs))
    apps = client.request("GET", "/v1/apps", {"filter[bundleId]": data["bundleId"]}).get("data", [])
    if not apps:
        raise SyncError(f"Bundle ID {data['bundleId']} のアプリが見つかりません。レコードは App Store Connect で先に作成してください。")
    app_id = apps[0]["id"]
    version_id, state = pick_version(client, app_id, data["versionString"])
    changes, notes = [], []

    by_loc = {}
    if data.get("versionLocalizations") or data.get("screenshots"):
        remote = client.request("GET", f"/v1/appStoreVersions/{version_id}/appStoreVersionLocalizations").get("data", [])
        by_loc = {r["attributes"]["locale"]: r for r in remote}
    shots = []
    if data.get("screenshots"):
        shots, shot_notes = plan_screenshots(client, data, {k: v["id"] for k, v in by_loc.items()}, base_dir)
        notes += shot_notes
    if data.get("versionLocalizations"):
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

    return {"appId": app_id, "versionId": version_id, "versionState": state, "changes": changes, "notes": notes, "screenshots": shots}


# ---------- スクリーンショット(App Asset Library) ----------
def image_info(path):
    """(幅, 高さ, アルファの有無) を返す。PNG と JPEG のヘッダーだけを読む。"""
    b = pathlib.Path(path).read_bytes()
    if b[:8] == b"\x89PNG\r\n\x1a\n":
        w, h = struct.unpack(">II", b[16:24])
        return w, h, b[25] in (4, 6)
    if b[:2] == b"\xff\xd8":
        i = 2
        while i + 9 < len(b):
            if b[i] != 0xFF:
                i += 1
                continue
            marker = b[i + 1]
            if marker in (0xC0, 0xC1, 0xC2):
                h, w = struct.unpack(">HH", b[i + 5:i + 9])
                return w, h, False
            seg = struct.unpack(">H", b[i + 2:i + 4])[0]
            i += 2 + seg
    raise SyncError(f"{path}: 画像の形式を読み取れません(PNG / JPEG のみ)")


def load_refdata(client):
    """参照データ(寸法・配置グループ)を取得する。取れなければ None。仕様はハードコードしない。"""
    try:
        res = client.request("GET", "/v1/appAssetLibraryRefData",
                             {"fields[appAssetLibraryRefData]": "imageSpecs,placementProfileGroups"})
    except SyncError:
        return None
    d = res.get("data")
    item = d[0] if isinstance(d, list) and d else d
    return (item or {}).get("attributes") or None


def check_shot(ref, group, path, w, h, alpha):
    """問題の一覧を返す。参照データの構造が想定と違う時は、検査をスキップする(サーバー側の検証に任せる)。"""
    errs = []
    if alpha:
        errs.append(f"{path}: アルファチャンネルがあります(スクリーンショットは不可。透過のない PNG / JPEG にする)")
    if ref:
        groups = ref.get("placementProfileGroups")
        if groups and group not in json.dumps(groups):
            errs.append(f"配置グループ {group} が参照データにありません(参照データから正しい識別子を確認する)")
        specs = ref.get("imageSpecs")
        if isinstance(specs, list) and specs and all(isinstance(x, dict) and "dimensions" in x for x in specs):
            ok = False
            for sp in specs:
                dm = sp["dimensions"]
                if (dm.get("minWidth") == dm.get("maxWidth") == w and dm.get("minHeight") == dm.get("maxHeight") == h
                        and PLACEMENT_TYPE in (sp.get("compatiblePlacementTypes") or [PLACEMENT_TYPE])):
                    ok = True
            if not ok:
                errs.append(f"{path}: 寸法 {w}x{h} に一致する仕様が参照データにありません(寸法は完全一致が必要)")
    return errs


def plan_screenshots(client, data, loc_ids, base_dir):
    ref = load_refdata(client)
    items, notes, errs = [], [], []
    if ref is None:
        notes.append("参照データを取得できませんでした。寸法・配置グループの事前検査をスキップします(サーバー側で検証されます)")
    for loc, groups in data["screenshots"].items():
        loc_id = loc_ids.get(loc)
        if not loc_id:
            notes.append(f"screenshots: ロケール {loc} が App Store Connect にありません(先に追加してください)")
            continue
        for group, files in groups.items():
            entries = []
            for f in files:
                path = pathlib.Path(f)
                if not path.is_absolute():
                    path = pathlib.Path(base_dir) / path
                if not path.exists():
                    errs.append(f"{f}: ファイルがありません")
                    continue
                w, h, alpha = image_info(path)
                errs += check_shot(ref, group, f, w, h, alpha)
                entries.append({"path": str(path), "name": path.name, "size": path.stat().st_size,
                                "w": w, "h": h, "mime": SHOT_EXT[path.suffix.lower()]})
            res = client.request("GET", f"/v1/appStoreVersionLocalizations/{loc_id}/placements",
                                 {"filter[placementType]": PLACEMENT_TYPE, "filter[placementGroup]": group,
                                  "sort": "placementGroupPosition"})
            existing = [x["id"] for x in res.get("data", [])]
            items.append({"locale": loc, "locId": loc_id, "group": group, "files": entries, "existing": existing})
    if errs:
        raise SyncError("スクリーンショットに問題があります:\n  - " + "\n  - ".join(errs))
    return items, notes


def get_asset_library_id(client, app_id):
    res = client.request("GET", f"/v1/apps/{app_id}/assetLibrary")
    d = res.get("data")
    if not d:
        raise SyncError("アセットライブラリを取得できませんでした")
    return d["id"]


def upload_one(client, library_id, entry, sleep, timeout):
    """予約 → アップロード → 確定 → 処理待ち。画像の ID を返す。"""
    body = {"data": {"type": "appAssetLibraryImages",
                     "attributes": {"fileName": entry["name"], "fileSize": entry["size"],
                                    "category": ASSET_CATEGORY, "referenceName": entry["name"]},
                     "relationships": {"assetLibrary": {"data": {"type": "appAssetLibraries", "id": library_id}}}}}
    res = client.request("POST", "/v1/appAssetLibraryImages", None, body)["data"]
    image_id = res["id"]
    raw = pathlib.Path(entry["path"]).read_bytes()
    for op in res["attributes"].get("uploadOperations") or []:
        headers = {h["name"]: h["value"] for h in op.get("requestHeaders") or []}
        client.upload(op["method"], op["url"], headers, raw[op["offset"]:op["offset"] + op["length"]])
    client.request("PATCH", f"/v1/appAssetLibraryImages/{image_id}", None,
                   {"data": {"type": "appAssetLibraryImages", "id": image_id, "attributes": {"uploaded": True}}})
    waited = 0
    while True:
        st = client.request("GET", f"/v1/appAssetLibraryImages/{image_id}")["data"]["attributes"]
        if st.get("state") == READY_STATE:
            return image_id
        if st.get("state") == "FAILED":
            raise SyncError(f"{entry['name']}: 処理に失敗しました: {st.get('stateDetails')}(画像を削除して、やり直してください: {image_id})")
        if waited >= timeout:
            raise SyncError(f"{entry['name']}: 処理が終わりません(状態: {st.get('state')}。画像 ID: {image_id})")
        sleep(3)
        waited += 3


def apply_screenshots(client, plan, library_id, allow_delete, sleep=time.sleep, timeout=180):
    done = []
    for it in plan["screenshots"]:
        if it["existing"] and not allow_delete:
            raise SyncError(f"{it['locale']} / {it['group']} に既存のスクリーンショットが {len(it['existing'])} 枚あります。"
                            "置き換えるには --allow-delete-placements が必要です(画像はライブラリに残ります)")
    for it in plan["screenshots"]:
        for pid in it["existing"]:
            client.request("DELETE", f"/v1/appAssetLibraryPlacements/{pid}")
        new_ids = []
        for entry in it["files"]:
            image_id = upload_one(client, library_id, entry, sleep, timeout)
            body = {"data": {"type": "appAssetLibraryPlacements",
                             "attributes": {"placementType": PLACEMENT_TYPE, "placementGroup": it["group"]},
                             "relationships": {
                                 "image": {"data": {"type": "appAssetLibraryImages", "id": image_id}},
                                 "appStoreVersionLocalization": {"data": {"type": "appStoreVersionLocalizations", "id": it["locId"]}}}}}
            new_ids.append(client.request("POST", "/v1/appAssetLibraryPlacements", None, body)["data"]["id"])
        if new_ids:
            order = {"data": {"type": "appAssetLibraryPlacementOrderingRequests",
                              "attributes": {"placementGroup": it["group"]},
                              "relationships": {
                                  "orderedPlacements": {"data": [{"type": "appAssetLibraryPlacements", "id": i} for i in new_ids]},
                                  "appStoreVersionLocalization": {"data": {"type": "appStoreVersionLocalizations", "id": it["locId"]}}}}}
            client.request("POST", "/v1/appAssetLibraryPlacementOrderingRequests", None, order)
        done.append((it["locale"], it["group"], len(new_ids)))
    return done


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
    backup.write_text(json.dumps({"changes": plan["changes"],
                                  "screenshots": [{"locale": i["locale"], "group": i["group"], "existingPlacements": i["existing"]}
                                                  for i in plan.get("screenshots", [])]},
                                 ensure_ascii=False, indent=2), encoding="utf-8")
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
    for it in plan.get("screenshots", []):
        print(f"- [screenshots {it['locale']}] {it['group']}: {len(it['files'])} 枚を追加(既存 {len(it['existing'])} 枚)")
        if it["existing"]:
            print("    ! 既存の配置を削除して置き換えます(画像はライブラリに残る)。実行には --allow-delete-placements が必要")
        for i, e in enumerate(it["files"], 1):
            print(f"    {i}. {e['name']}  {e['w']}x{e['h']}  {e['size']} bytes")
    for n in plan["notes"]:
        print(f"! {n}")


def main(argv=None, client=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["plan", "apply"])
    ap.add_argument("input")
    ap.add_argument("--confirm-bundle-id", help="apply の時に必須。入力の bundleId と同じ値を指定する")
    ap.add_argument("--backup-dir", default="private")
    ap.add_argument("--allow-delete-placements", action="store_true",
                    help="既存のスクリーンショットの配置を削除して置き換える(画像はライブラリに残る)")
    args = ap.parse_args(argv)
    try:
        data = json.loads(pathlib.Path(args.input).read_text(encoding="utf-8"))
        client = client or Client()
        plan = build_plan(client, data, pathlib.Path(args.input).resolve().parent)
        show_plan(plan)
        if args.command == "plan":
            print("\n(読み取りのみ。何も書き込んでいません。)")
            return 0
        if args.confirm_bundle_id != data["bundleId"]:
            raise SyncError("apply には --confirm-bundle-id <Bundle ID> が必要です(オーナーが差分を確認して OK した後にだけ実行する)")
        if not plan["changes"] and not plan["screenshots"]:
            return 0
        for it in plan["screenshots"]:  # 破壊的な操作の関所は、何かを書き込む前に確認する
            if it["existing"] and not args.allow_delete_placements:
                raise SyncError(f"{it['locale']} / {it['group']} に既存のスクリーンショットがあります。置き換えるには --allow-delete-placements が必要です")
        backup, n = apply_plan(client, plan, args.backup_dir)
        print(f"\n{n} 件のテキストの更新を送信しました。変更前の値: {backup}(コミットしない)")
        if plan["screenshots"]:
            lib = get_asset_library_id(client, plan["appId"])
            for loc, group, cnt in apply_screenshots(client, plan, lib, args.allow_delete_placements):
                print(f"スクリーンショット {loc} / {group}: {cnt} 枚を配置しました")
        print("次: App Store Connect の画面で内容を確認してください。審査への提出は手動で行います。")
        return 0
    except SyncError as e:
        print(f"中止: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
