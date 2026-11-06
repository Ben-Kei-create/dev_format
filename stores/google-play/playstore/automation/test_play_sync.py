import json, struct, tempfile, unittest, pathlib
import play_sync as p

PKG = "com.example.app"


def fake_png(path, w, h, color_type=2, pad=40):
    ihdr = struct.pack(">IIBBBBB", w, h, 8, color_type, 0, 0, 0)
    pathlib.Path(path).write_bytes(b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + b"IHDR" + ihdr + b"\0\0\0\0" + b"x" * pad)

BASE = {"packageName": PKG}


class Fake:
    def __init__(self, existing_images=0, listings=None):
        self.calls = []
        self.existing_images = existing_images
        self.listings = listings if listings is not None else [{"language": "ja-JP", "title": "旧", "shortDescription": "s", "fullDescription": "f"}]
    def call(self, method, url, params=None, json_body=None, data=None, content_type=None):
        self.calls.append((method, url, params, json_body, data, content_type))
        if method == "POST" and url.endswith("/edits"): return {"id": "E1"}
        if method == "GET" and url.endswith("/edits/E1/listings"): return {"listings": self.listings}
        if method == "GET" and "/listings/" in url: return {"images": [{"id": str(i)} for i in range(self.existing_images)]}
        return {}
    def writes(self):
        return [c for c in self.calls if c[0] in ("PATCH", "PUT") or (c[0] == "POST" and (":commit" in c[1] or "upload" in c[1] or "dataSafety" in c[1]))
                or (c[0] == "DELETE" and "/listings/" in c[1])]


class T(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory(); self.dir = pathlib.Path(self.t.name)
        fake_png(self.dir / "a.png", 1080, 1920); (self.dir / "ds.csv").write_text("a,b\n1,2\n", encoding="utf-8")
    def tearDown(self): self.t.cleanup()

    def test_validate_limits_and_unknown(self):
        e, w = p.validate(dict(BASE, listings={"ja-JP": {"shortDescription": "x" * 81, "foo": "1"}}, extra=1))
        s = "\n".join(e); self.assertIn("上限 80", s); self.assertIn("foo", s); self.assertIn("extra", s)
    def test_title_limit_30(self):
        e, w = p.validate(dict(BASE, listings={"ja-JP": {"title": "あ" * 30}})); self.assertEqual(e, [])  # 全角も1文字
        e, w = p.validate(dict(BASE, listings={"ja-JP": {"title": "あ" * 31}})); self.assertIn("上限 30", "\n".join(e))
    def test_full_description_limit_4000(self):
        e, _ = p.validate(dict(BASE, listings={"ja-JP": {"fullDescription": "x" * 4000}})); self.assertEqual(e, [])
        e, _ = p.validate(dict(BASE, listings={"ja-JP": {"fullDescription": "x" * 4001}})); self.assertIn("上限 4000", "\n".join(e))
    def test_validate_pii(self):
        mail = "someone" + "@" + "gmail.com"; tel = "090-" + "1234-5678"
        e, _ = p.validate(dict(BASE, listings={"ja-JP": {"fullDescription": f"{mail} {tel}"}}))
        s = "\n".join(e); self.assertIn("メール", s); self.assertIn("電話", s)
    def test_image_rules(self):
        fake_png(self.dir / "alpha.png", 1080, 1920, color_type=6); fake_png(self.dir / "tall.png", 400, 1000)
        fake_png(self.dir / "fg.png", 1024, 500); fake_png(self.dir / "fg_bad.png", 1000, 500)
        fake_png(self.dir / "icon.png", 512, 512, color_type=6); fake_png(self.dir / "icon_bad.png", 500, 500, color_type=6)
        def errors(t, f):
            try: p.build_plan(Fake(), dict(BASE, images={"ja-JP": {t: [f]}}), self.dir); return ""
            except p.SyncError as e: return str(e)
        self.assertIn("アルファ", errors("phoneScreenshots", "alpha.png"))
        self.assertIn("縦横比", errors("phoneScreenshots", "tall.png"))
        self.assertEqual(errors("featureGraphic", "fg.png"), "")
        self.assertIn("1024x500", errors("featureGraphic", "fg_bad.png"))
        self.assertEqual(errors("icon", "icon.png"), "")  # アイコンはアルファ可
        self.assertIn("512x512", errors("icon", "icon_bad.png"))
        self.assertEqual(errors("sevenInchScreenshots", "a.png"), "")
    def test_validate_image_types(self):
        e, _ = p.validate(dict(BASE, images={"ja-JP": {"bogus": ["a.png"]}})); self.assertIn("未対応", "\n".join(e))
    def test_plan_diff_and_read_only(self):
        f = Fake()
        plan = p.build_plan(f, dict(BASE, listings={"ja-JP": {"title": "新", "shortDescription": "s"}}), self.dir)
        self.assertEqual([(c["field"]) for c in plan["changes"]], ["title"])
        self.assertEqual(f.writes(), [])
        self.assertEqual(f.calls[-1][0:2], ("DELETE", f"{p.API}/{PKG}/edits/E1"))  # 下書きを破棄
    def test_plan_missing_file(self):
        with self.assertRaises(p.SyncError):
            p.build_plan(Fake(), dict(BASE, images={"ja-JP": {"icon": ["none.png"]}}), self.dir)
    def test_apply_without_commit_validates_and_discards(self):
        f = Fake(); d = dict(BASE, listings={"ja-JP": {"title": "新"}})
        plan = p.build_plan(f, d, self.dir); f.calls.clear()
        r = p.apply_edit(f, plan, d, self.dir, False, False)
        self.assertEqual(r, "validated-discarded")
        names = [(c[0], c[1].split(PKG)[-1]) for c in f.calls]
        self.assertIn(("PATCH", "/edits/E1/listings/ja-JP"), names)
        self.assertIn(("POST", "/edits/E1:validate"), names)
        self.assertFalse([c for c in f.calls if ":commit" in c[1]])
        self.assertEqual(names[-1], ("DELETE", "/edits/E1"))
    def test_apply_commit_uses_error_if_in_review(self):
        f = Fake(); d = dict(BASE, listings={"ja-JP": {"title": "新"}})
        plan = p.build_plan(f, d, self.dir); f.calls.clear()
        self.assertEqual(p.apply_edit(f, plan, d, self.dir, False, True), "committed")
        commit = [c for c in f.calls if ":commit" in c[1]][0]
        self.assertEqual(commit[2], {"changesInReviewBehavior": "ERROR_IF_IN_REVIEW"})
    def test_images_replace_requires_flag(self):
        f = Fake(existing_images=2); d = dict(BASE, images={"ja-JP": {"phoneScreenshots": ["a.png"]}})
        plan = p.build_plan(f, d, self.dir); f.calls.clear()
        with self.assertRaises(p.SyncError): p.apply_edit(f, plan, d, self.dir, False, False)
        self.assertEqual(f.calls, [])  # 何も作らない
        r = p.apply_edit(f, plan, d, self.dir, True, False)
        names = [(c[0], c[1].split(PKG)[-1]) for c in f.calls]
        self.assertIn(("DELETE", "/edits/E1/listings/ja-JP/phoneScreenshots"), names)
        up = [c for c in f.calls if c[0] == "POST" and "/upload/" in c[1]][0]
        self.assertEqual(up[4], (self.dir / "a.png").read_bytes()); self.assertEqual(up[5], "image/png"); self.assertEqual(up[2], {"uploadType": "media"})
    def test_failed_validate_discards_edit(self):
        f = Fake(); d = dict(BASE, listings={"ja-JP": {"title": "新"}})
        plan = p.build_plan(f, d, self.dir); f.calls.clear()
        orig = f.call
        def bad(method, url, *a, **k):
            if url.endswith(":validate"): raise p.SyncError("invalid")
            return orig(method, url, *a, **k)
        f.call = bad
        with self.assertRaises(p.SyncError): p.apply_edit(f, plan, d, self.dir, False, True)
        self.assertTrue([c for c in f.calls if c[0] == "DELETE" and c[1].endswith("/edits/E1")])
        self.assertFalse([c for c in f.calls if ":commit" in c[1]])
    def test_main_requires_confirm(self):
        inp = self.dir / "in.json"; inp.write_text(json.dumps(dict(BASE, listings={"ja-JP": {"title": "新"}})))
        f = Fake(); self.assertEqual(p.main(["apply", str(inp)], client=f), 1); self.assertEqual(f.writes(), [])
        self.assertEqual(p.main(["apply", str(inp), "--confirm-package", PKG], client=f), 0)
    def test_datasafety_requires_confirm_and_sends_csv(self):
        inp = self.dir / "in.json"; inp.write_text(json.dumps(dict(BASE, dataSafety={"csvPath": "ds.csv"})))
        f = Fake(); self.assertEqual(p.main(["datasafety", str(inp)], client=f), 1); self.assertEqual(f.writes(), [])
        self.assertEqual(p.main(["datasafety", str(inp), "--confirm-package", PKG], client=f), 0)
        call = [c for c in f.calls if c[1].endswith("/dataSafety")][0]
        self.assertEqual(call[3], {"safetyLabels": "a,b\n1,2\n"})

if __name__ == "__main__":
    unittest.main()
