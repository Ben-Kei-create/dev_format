#!/usr/bin/env python3
"""Google Play Developer API: 掲載情報・画像・データセーフティの差分確認と反映。

- `plan`        : 下書き(edit)を作って現在の掲載情報を読み、差分を表示し、下書きを破棄する。何も確定しない。
- `apply`       : オーナーが差分を確認して OK した後にだけ実行する。下書きに書き込み、サーバーで検証し、
                  `--commit` が無ければ下書きを破棄する(= サーバー検証つきの予行)。`--commit` で確定する。
                  確定は「変更を公開に送る」操作(公開済みのアプリでは審査に送られる)。別の承認を得てから。
- `datasafety`  : データセーフティの宣言(CSV)を書き込む。API は書き込みのみで、現在の値は読めない(差分なし)。
- 対象外(手動): アプリの作成、ビルド(AAB)のアップロード、トラックへのリリース、アプリのコンテンツの宣言
                (広告・アクセス・ターゲット層・レーティング)、個人情報(連絡先など)、価格。
- 認証: サービスアカウントの JSON 鍵のパスを環境変数 PLAY_SA_KEY_PATH に。鍵はリポジトリに置かない・表示しない。
        Play Console の「ユーザーと権限」でサービスアカウントを招待し、必要な権限を与えておく。
- 依存: pip install pyjwt cryptography
状態: 実際の API では未実行(テストは偽の応答のみ)。公式リファレンスで確認済み(2026-11-06): edits.insert(POST)、
      edits.delete(DELETE)、edits.validate(POST :validate)、edits.commit(POST :commit)、edits.listings.patch(PATCH)・update(PUT)、
      edits.images の list(GET)・deleteall(DELETE)・upload、AppImageType の値、applications.dataSafety(POST)。
      最初は必ず `plan` だけを実行すること。
"""
import argparse, hashlib, json, os, pathlib, re, struct, sys, time, urllib.error, urllib.parse, urllib.request

API = "https://androidpublisher.googleapis.com/androidpublisher/v3/applications"
UPLOAD = "https://androidpublisher.googleapis.com/upload/androidpublisher/v3/applications"
SCOPE = "https://www.googleapis.com/auth/androidpublisher"
# 上限は Play Console ヘルプ「アプリの作成と設定」(2026-11-06): アプリ名 30、短い説明 80、詳しい説明 4,000。全角・半角を同じ1文字として数える
LISTING_FIELDS = {"title": 30, "shortDescription": 80, "fullDescription": 4000, "video": None}
# 画像の規則: Google Play ヘルプ「プレビュー アセット」(2026-11-06 確認)。imageType の値は AppImageType(公式)
# スクリーンショット: 端末の種類ごとに最大8枚 / JPEG または24ビット PNG(アルファなし) / 各辺 320〜3840px / 長辺は短辺の2倍まで
# アイコン: 512x512 / 32ビット PNG(アルファあり) / 1024KB 以下
# フィーチャーグラフィック: 1024x500 / JPEG または24ビット PNG(アルファなし)
SHOT = {"max": 8, "alpha": False, "minDim": 320, "maxDim": 3840, "ratio": 2}
IMAGE_RULES = {
    "phoneScreenshots": SHOT,
    "sevenInchScreenshots": SHOT,
    "tenInchScreenshots": SHOT,
    "icon": {"max": 1, "exact": (512, 512), "alpha": True, "maxKB": 1024, "png": True},
    "featureGraphic": {"max": 1, "exact": (1024, 500), "alpha": False},
}
IMAGE_TYPES = {k: v["max"] for k, v in IMAGE_RULES.items()}  # (tvScreenshots / wearScreenshots / tvBanner は未対応)
IMAGE_EXT = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}

EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")
PHONE = re.compile(r"(?:\+81[ -]?\(?0?\)?[1-9][0-9 -]{7,}|(?<![0-9])0[1-9]0?[ -]?[0-9]{3,4}[ -]?[0-9]{4}(?![0-9]))")
OK_EMAIL_DOMAINS = ("example.com", "example.org", "example.net")


class SyncError(Exception):
    pass


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
    errs, warns = [], []
    if not isinstance(data.get("packageName"), str) or not data["packageName"]:
        errs.append("packageName が必要です")
    for k in data:
        if k not in {"packageName", "listings", "images", "dataSafety"}:
            errs.append(f"未対応のキー: {k}(対象外。手動で入力してください)")
    for lang, fields in (data.get("listings") or {}).items():
        if not isinstance(fields, dict):
            errs.append(f"listings.{lang} はオブジェクトにしてください")
            continue
        for f, v in fields.items():
            if f not in LISTING_FIELDS:
                errs.append(f"listings.{lang}.{f} は対象外の項目です")
            elif not isinstance(v, str):
                errs.append(f"listings.{lang}.{f} は文字列にしてください")
            elif LISTING_FIELDS[f] and len(v) > LISTING_FIELDS[f]:
                errs.append(f"listings.{lang}.{f} が上限 {LISTING_FIELDS[f]} 文字を超えています(現在 {len(v)} 文字)")
    for lang, types in (data.get("images") or {}).items():
        if not isinstance(types, dict):
            errs.append(f"images.{lang} はオブジェクトにしてください")
            continue
        for t, files in types.items():
            if t not in IMAGE_TYPES:
                errs.append(f"images.{lang}.{t} は未対応の画像の種類です(対応: {', '.join(IMAGE_TYPES)})")
                continue
            if not isinstance(files, list) or not files:
                errs.append(f"images.{lang}.{t} はファイルのパスの配列にしてください")
                continue
            if len(files) > IMAGE_TYPES[t]:
                errs.append(f"images.{lang}.{t} が上限 {IMAGE_TYPES[t]} 枚を超えています")
            for f in files:
                if not isinstance(f, str) or pathlib.Path(f).suffix.lower() not in IMAGE_EXT:
                    errs.append(f"images.{lang}.{t}: {f!r} は .png / .jpg / .jpeg のパスにしてください")
    ds = data.get("dataSafety")
    if ds is not None and (not isinstance(ds, dict) or set(ds) != {"csvPath"}):
        errs.append('dataSafety は {"csvPath": "..."} の形にしてください')
    for path, s in iter_strings({k: v for k, v in data.items() if k != "images"}):
        for m in EMAIL.findall(s):
            if not m.lower().endswith(OK_EMAIL_DOMAINS):
                errs.append(f"{path}: メールアドレスらしい文字列があります(個人情報は入れない)")
        if PHONE.search(s):
            errs.append(f"{path}: 電話番号らしい文字列があります(個人情報は入れない)")
    return errs, warns


def image_info(path):
    """(幅, 高さ, アルファの有無, 形式) を返す。PNG と JPEG のヘッダーだけを読む。"""
    b = pathlib.Path(path).read_bytes()
    if b[:8] == b"\x89PNG\r\n\x1a\n":
        w, h = struct.unpack(">II", b[16:24])
        return w, h, b[25] in (4, 6), "png"
    if b[:2] == b"\xff\xd8":
        i = 2
        while i + 9 < len(b):
            if b[i] != 0xFF:
                i += 1
                continue
            if b[i + 1] in (0xC0, 0xC1, 0xC2):
                h, w = struct.unpack(">HH", b[i + 5:i + 9])
                return w, h, False, "jpeg"
            i += 2 + struct.unpack(">H", b[i + 2:i + 4])[0]
    raise SyncError(f"{path}: 画像の形式を読み取れません(PNG / JPEG のみ)")


def check_images(data, base_dir):
    """ローカルの画像を公式の規則で検査する。(エラー, 警告) を返す。"""
    errs, warns, shots = [], [], 0
    for lang, types in (data.get("images") or {}).items():
        for t, files in types.items():
            rule = IMAGE_RULES.get(t)
            if not rule:
                continue
            for f in files:
                path = pathlib.Path(f) if pathlib.Path(f).is_absolute() else pathlib.Path(base_dir) / f
                if not path.exists():
                    errs.append(f"{f}: ファイルがありません")
                    continue
                w, h, alpha, fmt = image_info(path)
                if t.endswith("Screenshots"):
                    shots += 1
                if rule.get("png") and fmt != "png":
                    errs.append(f"{f}: {t} は PNG にしてください")
                if not rule.get("alpha") and alpha:
                    errs.append(f"{f}: アルファチャンネルがあります({t} は不可。24ビット PNG または JPEG)")
                if "exact" in rule and (w, h) != rule["exact"]:
                    errs.append(f"{f}: 寸法 {w}x{h} は {t} の {rule['exact'][0]}x{rule['exact'][1]} と一致しません")
                if "minDim" in rule:
                    if min(w, h) < rule["minDim"] or max(w, h) > rule["maxDim"]:
                        errs.append(f"{f}: 寸法 {w}x{h} は各辺 {rule['minDim']}〜{rule['maxDim']}px の範囲外です")
                    if max(w, h) > rule["ratio"] * min(w, h):
                        errs.append(f"{f}: 縦横比が {rule['ratio']}:1 を超えています({w}x{h})")
                if "maxKB" in rule and path.stat().st_size > rule["maxKB"] * 1024:
                    errs.append(f"{f}: {rule['maxKB']}KB を超えています")
    if data.get("images") and shots < 2:
        warns.append("スクリーンショットは、公開に最低2枚(端末の種類をまたいで)必要とされます")
    return errs, warns


class Client:
    def __init__(self, transport=None):
        self._transport = transport or self._http
        self._token, self._exp = None, 0

    def _make_token(self):
        try:
            import jwt
        except ImportError:
            raise SyncError("pyjwt と cryptography が必要です: pip install pyjwt cryptography")
        try:
            key_path = os.environ["PLAY_SA_KEY_PATH"]
        except KeyError:
            raise SyncError("環境変数 PLAY_SA_KEY_PATH が未設定です")
        key = json.loads(pathlib.Path(key_path).read_text(encoding="utf-8"))
        uri = key.get("token_uri", "https://oauth2.googleapis.com/token")
        now = int(time.time())
        assertion = jwt.encode({"iss": key["client_email"], "scope": SCOPE, "aud": uri, "iat": now, "exp": now + 3000},
                               key["private_key"], algorithm="RS256")
        body = urllib.parse.urlencode({"grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                                       "assertion": assertion}).encode()
        req = urllib.request.Request(uri, data=body, method="POST",
                                     headers={"Content-Type": "application/x-www-form-urlencoded"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                res = json.loads(r.read())
        except urllib.error.HTTPError as e:
            raise SyncError(f"トークンの取得に失敗しました(HTTP {e.code})")
        self._exp = now + int(res.get("expires_in", 3000))
        return res["access_token"]

    def _auth(self):
        if not self._token or time.time() > self._exp - 60:
            self._token = self._make_token()
        return {"Authorization": f"Bearer {self._token}"}

    def _http(self, method, url, params, json_body, data, content_type):
        if params:
            url += "?" + urllib.parse.urlencode(params)
        headers = self._auth()
        if json_body is not None:
            data = json.dumps(json_body).encode()
            headers["Content-Type"] = "application/json"
        elif content_type:
            headers["Content-Type"] = content_type
        req = urllib.request.Request(url, data=data, method=method, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                raw = r.read()
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            raise SyncError(f"{method} {url.split('?')[0]} が失敗しました(HTTP {e.code}): {e.read().decode(errors='replace')[:400]}")

    def call(self, method, url, params=None, json_body=None, data=None, content_type=None):
        return self._transport(method, url, params, json_body, data, content_type)


def new_edit(c, pkg):
    return c.call("POST", f"{API}/{pkg}/edits", json_body={})["id"]


def drop_edit(c, pkg, edit):
    try:
        c.call("DELETE", f"{API}/{pkg}/edits/{edit}")
    except SyncError:
        pass


def read_listings(c, pkg, edit):
    res = c.call("GET", f"{API}/{pkg}/edits/{edit}/listings")
    return {x["language"]: x for x in res.get("listings", [])}


def read_images(c, pkg, edit, lang, itype):
    res = c.call("GET", f"{API}/{pkg}/edits/{edit}/listings/{lang}/{itype}")
    return res.get("images", [])


def read_csv(base_dir, path):
    p = pathlib.Path(path)
    if not p.is_absolute():
        p = pathlib.Path(base_dir) / p
    if not p.exists():
        raise SyncError(f"{path}: ファイルがありません")
    text = p.read_text(encoding="utf-8")
    return text, hashlib.sha256(text.encode()).hexdigest()[:12], len(text.splitlines())


def build_plan(c, data, base_dir="."):
    errs, warns = validate(data)
    if errs:
        raise SyncError("入力に問題があります:\n  - " + "\n  - ".join(errs))
    pkg = data["packageName"]
    plan = {"package": pkg, "changes": [], "images": [], "dataSafety": None, "warnings": warns}
    img_errs, img_warns = check_images(data, base_dir)
    if img_errs:
        raise SyncError("画像に問題があります:\n  - " + "\n  - ".join(img_errs))
    plan["warnings"] += img_warns
    if data.get("dataSafety"):
        text, digest, rows = read_csv(base_dir, data["dataSafety"]["csvPath"])
        plan["dataSafety"] = {"csv": data["dataSafety"]["csvPath"], "sha": digest, "rows": rows}
    edit = new_edit(c, pkg)
    try:
        remote = read_listings(c, pkg, edit)
        for lang, wanted in (data.get("listings") or {}).items():
            cur = remote.get(lang, {})
            for f in LISTING_FIELDS:
                if f in wanted and (cur.get(f) or "") != wanted[f]:
                    plan["changes"].append({"language": lang, "field": f, "old": cur.get(f), "new": wanted[f]})
        for lang, files_by_type in (data.get("images") or {}).items():
            for t, files in files_by_type.items():
                existing = read_images(c, pkg, edit, lang, t)
                plan["images"].append({"language": lang, "type": t, "files": files, "existing": len(existing)})
    finally:
        drop_edit(c, pkg, edit)  # plan は何も確定しない
    return plan


def show_plan(plan):
    print(f"パッケージ: {plan['package']}")
    for c in plan["changes"]:
        old = c["old"] or ""
        print(f"- [listing {c['language']}] {c['field']}")
        print(f"    現在: {old[:80]!r}{'…' if len(old) > 80 else ''}")
        print(f"    新規: {c['new'][:80]!r}{'…' if len(c['new']) > 80 else ''}  ({len(c['new'])}文字)")
    for i in plan["images"]:
        print(f"- [images {i['language']}] {i['type']}: {len(i['files'])} 枚を追加(既存 {i['existing']} 枚)")
        if i["existing"]:
            print("    ! 既存の画像を全て削除して置き換えます。実行には --allow-delete-images が必要")
    if plan["dataSafety"]:
        d = plan["dataSafety"]
        print(f"- [dataSafety] {d['csv']}: {d['rows']} 行 / sha256 {d['sha']}…  ※宣言全体を上書き。現在の値は API で読めない")
    for w in plan["warnings"]:
        print(f"! {w}")
    if not (plan["changes"] or plan["images"] or plan["dataSafety"]):
        print("変更はありません。")


def apply_edit(c, plan, data, base_dir, allow_delete, commit):
    pkg = plan["package"]
    for i in plan["images"]:
        if i["existing"] and not allow_delete:
            raise SyncError(f"{i['language']} / {i['type']} に既存の画像が {i['existing']} 枚あります。置き換えるには --allow-delete-images が必要です")
    edit = new_edit(c, pkg)
    try:
        by_lang = {}
        for ch in plan["changes"]:
            by_lang.setdefault(ch["language"], {})[ch["field"]] = ch["new"]
        for lang, fields in by_lang.items():
            body = dict(fields)
            c.call("PATCH", f"{API}/{pkg}/edits/{edit}/listings/{lang}", json_body=body)
        for i in plan["images"]:
            lang, t = i["language"], i["type"]
            if i["existing"]:
                c.call("DELETE", f"{API}/{pkg}/edits/{edit}/listings/{lang}/{t}")
            for f in i["files"]:
                path = pathlib.Path(f) if pathlib.Path(f).is_absolute() else pathlib.Path(base_dir) / f
                c.call("POST", f"{UPLOAD}/{pkg}/edits/{edit}/listings/{lang}/{t}", params={"uploadType": "media"},
                       data=path.read_bytes(), content_type=IMAGE_EXT[path.suffix.lower()])
        c.call("POST", f"{API}/{pkg}/edits/{edit}:validate", json_body={})
        if commit:
            c.call("POST", f"{API}/{pkg}/edits/{edit}:commit", params={"changesInReviewBehavior": "ERROR_IF_IN_REVIEW"}, json_body={})
            return "committed"
        drop_edit(c, pkg, edit)
        return "validated-discarded"
    except SyncError:
        drop_edit(c, pkg, edit)
        raise


def apply_data_safety(c, pkg, base_dir, csv_path):
    text, digest, rows = read_csv(base_dir, csv_path)
    c.call("POST", f"{API}/{pkg}/dataSafety", json_body={"safetyLabels": text})
    return digest, rows


def main(argv=None, client=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["plan", "apply", "datasafety"])
    ap.add_argument("input")
    ap.add_argument("--confirm-package", help="apply / datasafety で必須。入力の packageName と同じ値")
    ap.add_argument("--allow-delete-images", action="store_true", help="既存の画像を削除して置き換える")
    ap.add_argument("--commit", action="store_true", help="変更を確定する(公開に送る操作。別の承認を得てから)")
    args = ap.parse_args(argv)
    try:
        inp = pathlib.Path(args.input).resolve()
        data = json.loads(inp.read_text(encoding="utf-8"))
        client = client or Client()
        base = inp.parent
        if args.command == "datasafety":
            errs, _ = validate(data)
            if errs or not data.get("dataSafety"):
                raise SyncError("入力に問題があります(dataSafety.csvPath が必要):\n  - " + "\n  - ".join(errs))
            text, digest, rows = read_csv(base, data["dataSafety"]["csvPath"])
            print(f"データセーフティ: {data['dataSafety']['csvPath']} {rows} 行 / sha256 {digest}…(宣言全体を上書きします)")
            if args.confirm_package != data["packageName"]:
                raise SyncError("書き込むには --confirm-package <パッケージ名> が必要です(内容を確認して OK を得た後にだけ)")
            apply_data_safety(client, data["packageName"], base, data["dataSafety"]["csvPath"])
            print("送信しました。Play Console の「データセーフティ」で確認してください。")
            return 0
        plan = build_plan(client, data, base)
        show_plan(plan)
        if args.command == "plan":
            print("\n(読み取りのみ。何も確定していません。)")
            return 0
        if args.confirm_package != data["packageName"]:
            raise SyncError("apply には --confirm-package <パッケージ名> が必要です(オーナーが差分を確認して OK した後にだけ)")
        if not (plan["changes"] or plan["images"]):
            return 0
        result = apply_edit(client, plan, data, base, args.allow_delete_images, args.commit)
        if result == "committed":
            print("\n確定しました。公開済みのアプリでは審査に送られます。Play Console で状態を確認してください。")
        else:
            print("\nサーバーでの検証に成功しました(確定していません。下書きは破棄)。確定するには、承認を得て --commit を付けて再実行します。")
        return 0
    except SyncError as e:
        print(f"中止: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
