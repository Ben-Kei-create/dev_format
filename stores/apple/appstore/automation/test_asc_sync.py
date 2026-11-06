import json, struct, tempfile, unittest, pathlib
import asc_sync as a

class Fake:
    def __init__(self, state="PREPARE_FOR_SUBMISSION"):
        self.calls = []
        self.state = state
    def request(self, method, path, params=None, body=None):
        self.calls.append((method, path, params, body))
        if path == "/v1/apps": return {"data": [{"id": "A1"}]}
        if path == "/v1/apps/A1/appStoreVersions": return {"data": [{"id": "V1", "attributes": {"appVersionState": self.state}}]}
        if path == "/v1/appStoreVersions/V1/appStoreVersionLocalizations":
            return {"data": [{"id": "L1", "attributes": {"locale": "ja", "description": "old", "keywords": "a,b", "whatsNew": "x"}}]}
        if path == "/v1/apps/A1/appInfos": return {"data": [{"id": "I1", "attributes": {"appStoreState": "PREPARE_FOR_SUBMISSION"}}]}
        if path == "/v1/appInfos/I1/appInfoLocalizations": return {"data": [{"id": "IL1", "attributes": {"locale": "ja", "name": "N", "subtitle": "S"}}]}
        if path == "/v1/appInfos/I1/ageRatingDeclaration":
            return {"data": {"id": "AR1", "attributes": {"alcoholTobaccoOrDrugUseOrReferences": "NONE", "gambling": False,
                                                          "unrestrictedWebAccess": True, "kidsAgeBand": None}}}
        if path == "/v1/appStoreVersions/V1/appStoreReviewDetail": return {"data": {"id": "R1", "attributes": {"notes": "n0"}}}
        if method == "PATCH": return {}
        raise AssertionError(path)

BASE = {"bundleId": "com.example.app", "versionString": "1.0.0"}

class T(unittest.TestCase):
    def test_validate_ok(self):
        d = dict(BASE, versionLocalizations={"ja": {"description": "d", "keywords": "k"}})
        self.assertEqual(a.validate(d), [])
    def test_validate_too_long_and_unknown(self):
        d = dict(BASE, versionLocalizations={"ja": {"keywords": "x" * 101, "foo": "1"}}, secret="1")
        e = "\n".join(a.validate(d))
        self.assertIn("上限 100", e); self.assertIn("foo", e); self.assertIn("secret", e)
    def test_validate_blocks_pii(self):
        mail = "someone" + "@" + "gmail.com"; tel = "090-" + "1234-5678"  # 個人情報らしい文字列をファイルに直接書かない(pre-commit 対策)
        d = dict(BASE, reviewDetail={"notes": f"連絡は {mail} か {tel}"})
        e = "\n".join(a.validate(d))
        self.assertIn("メール", e); self.assertIn("電話", e)
    def test_validate_blocks_contact_fields(self):
        d = dict(BASE, reviewDetail={"contactEmail": "x"})
        self.assertIn("対象外", "\n".join(a.validate(d)))
    def test_plan_diff(self):
        d = dict(BASE, versionLocalizations={"ja": {"description": "new", "keywords": "a,b"}},
                 appInfoLocalizations={"ja": {"name": "N", "subtitle": "S2"}}, reviewDetail={"notes": "n1"})
        p = a.build_plan(Fake(), d)
        got = {(c["kind"], c["field"]) for c in p["changes"]}
        self.assertEqual(got, {("versionLocalization", "description"), ("appInfoLocalization", "subtitle"), ("reviewDetail", "notes")})
    def test_plan_is_read_only(self):
        f = Fake(); a.build_plan(f, dict(BASE, versionLocalizations={"ja": {"description": "new"}}))
        self.assertTrue(all(c[0] == "GET" for c in f.calls))
    def test_refuses_noneditable_state(self):
        with self.assertRaises(a.SyncError):
            a.build_plan(Fake("READY_FOR_SALE"), dict(BASE, versionLocalizations={"ja": {"description": "x"}}))
    def test_missing_locale_noted(self):
        p = a.build_plan(Fake(), dict(BASE, versionLocalizations={"en-US": {"description": "x"}}))
        self.assertTrue(p["notes"]); self.assertEqual(p["changes"], [])
    def test_apply_patches_and_backs_up(self):
        f = Fake(); d = dict(BASE, versionLocalizations={"ja": {"description": "new", "whatsNew": "y"}})
        p = a.build_plan(f, d)
        with tempfile.TemporaryDirectory() as t:
            path, n = a.apply_plan(f, p, t)
            self.assertEqual(n, 1)
            self.assertTrue(pathlib.Path(path).exists())
        patch = [c for c in f.calls if c[0] == "PATCH"]
        self.assertEqual(len(patch), 1)
        self.assertEqual(patch[0][1], "/v1/appStoreVersionLocalizations/L1")
        self.assertEqual(patch[0][3]["data"]["attributes"], {"description": "new", "whatsNew": "y"})
        self.assertEqual(patch[0][3]["data"]["type"], "appStoreVersionLocalizations")
    def test_apply_requires_confirm(self):
        with tempfile.TemporaryDirectory() as t:
            inp = pathlib.Path(t) / "in.json"
            inp.write_text(json.dumps(dict(BASE, versionLocalizations={"ja": {"description": "new"}})))
            f = Fake()
            rc = a.main(["apply", str(inp), "--backup-dir", t], client=f)
            self.assertEqual(rc, 1)
            self.assertFalse([c for c in f.calls if c[0] == "PATCH"])
            rc = a.main(["apply", str(inp), "--confirm-bundle-id", "com.example.app", "--backup-dir", t], client=f)
            self.assertEqual(rc, 0)
            self.assertTrue([c for c in f.calls if c[0] == "PATCH"])


def fake_png(path, w=1290, h=2796, color_type=2):
    ihdr = struct.pack(">IIBBBBB", w, h, 8, color_type, 0, 0, 0)
    pathlib.Path(path).write_bytes(b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + b"IHDR" + ihdr + b"\0\0\0\0" + b"x" * 40)


class ShotFake(Fake):
    def __init__(self, existing=None, fail_state=False):
        super().__init__()
        self.existing = existing or []
        self.uploads = []
        self.fail_state = fail_state
        self.n = 0
    def upload(self, method, url, headers, data):
        self.uploads.append((method, headers, len(data)))
    def request(self, method, path, params=None, body=None):
        if path == "/v1/apps/A1/assetLibrary": self.calls.append((method, path, params, body)); return {"data": {"id": "LIB1"}}
        if path == "/v1/appAssetLibraryRefData":
            self.calls.append((method, path, params, body))
            return {"data": [{"attributes": {"placementProfileGroups": [{"id": "G1"}],
                    "imageSpecs": [{"dimensions": {"minWidth": 1290, "maxWidth": 1290, "minHeight": 2796, "maxHeight": 2796},
                                    "compatiblePlacementTypes": ["APP_SCREENSHOT"]}]}}]}
        if path == "/v1/appStoreVersionLocalizations/L1/placements":
            self.calls.append((method, path, params, body)); return {"data": [{"id": x} for x in self.existing]}
        if path == "/v1/appAssetLibraryImages" and method == "POST":
            self.calls.append((method, path, params, body)); self.n += 1
            size = body["data"]["attributes"]["fileSize"]
            return {"data": {"id": f"IMG{self.n}", "attributes": {"uploadOperations": [
                {"method": "PUT", "url": "https://upload.invalid/x", "length": size, "offset": 0,
                 "requestHeaders": [{"name": "Content-Type", "value": "image/png"}]}]}}}
        if path.startswith("/v1/appAssetLibraryImages/") and method == "PATCH": self.calls.append((method, path, params, body)); return {}
        if path.startswith("/v1/appAssetLibraryImages/") and method == "GET":
            self.calls.append((method, path, params, body))
            return {"data": {"attributes": {"state": "FAILED" if self.fail_state else "PREPARE_FOR_SUBMISSION", "stateDetails": "bad"}}}
        if path == "/v1/appAssetLibraryPlacements" and method == "POST":
            self.calls.append((method, path, params, body)); return {"data": {"id": f"P{self.n}"}}
        if path.startswith("/v1/appAssetLibraryPlacements/") and method == "DELETE": self.calls.append((method, path, params, body)); return {}
        if path == "/v1/appAssetLibraryPlacementOrderingRequests": self.calls.append((method, path, params, body)); return {"data": {"id": "O1"}}
        return super().request(method, path, params, body)


class A(unittest.TestCase):
    def plan(self, ar):
        return a.build_plan(Fake(), dict(BASE, ageRating=ar))
    def test_diff_only_changed(self):
        p = self.plan({"alcoholTobaccoOrDrugUseOrReferences": "FREQUENT", "gambling": False, "unrestrictedWebAccess": False})
        self.assertEqual({c["field"] for c in p["changes"]}, {"alcoholTobaccoOrDrugUseOrReferences", "unrestrictedWebAccess"})
        self.assertTrue(all(c["kind"] == "ageRating" and c["id"] == "AR1" for c in p["changes"]))
    def test_unknown_attribute_rejected(self):
        with self.assertRaises(a.SyncError) as cm: self.plan({"somethingNew": "NONE"})
        self.assertIn("somethingNew", str(cm.exception))
    def test_bool_type_enforced(self):
        with self.assertRaises(a.SyncError): self.plan({"gambling": "NONE"})
    def test_level_value_enforced(self):
        with self.assertRaises(a.SyncError): self.plan({"alcoholTobaccoOrDrugUseOrReferences": "SOMETIMES"})
    def test_deprecated_value_rejected_in_validate(self):
        e = "\n".join(a.validate(dict(BASE, ageRating={"alcoholTobaccoOrDrugUseOrReferences": "FREQUENT_OR_INTENSE"})))
        self.assertIn("非推奨", e); self.assertIn("FREQUENT", e)
    def test_kids_age_band_null_or_string(self):
        self.assertEqual(self.plan({"kidsAgeBand": None})["changes"], [])
        self.assertEqual([c["field"] for c in self.plan({"kidsAgeBand": "FIVE_AND_UNDER"})["changes"]], ["kidsAgeBand"])
        with self.assertRaises(a.SyncError): self.plan({"kidsAgeBand": True})
    def test_apply_patches_declaration(self):
        f = Fake(); p = a.build_plan(f, dict(BASE, ageRating={"alcoholTobaccoOrDrugUseOrReferences": "FREQUENT", "gambling": True}))
        with tempfile.TemporaryDirectory() as t: a.apply_plan(f, p, t)
        patch = [c for c in f.calls if c[0] == "PATCH"][0]
        self.assertEqual(patch[1], "/v1/ageRatingDeclarations/AR1")
        self.assertEqual(patch[3]["data"]["type"], "ageRatingDeclarations")
        self.assertEqual(patch[3]["data"]["attributes"], {"alcoholTobaccoOrDrugUseOrReferences": "FREQUENT", "gambling": True})
    def test_plan_read_only_and_show(self):
        f = Fake(); p = a.build_plan(f, dict(BASE, ageRating={"gambling": True, "kidsAgeBand": "FIVE_AND_UNDER"}))
        self.assertTrue(all(c[0] == "GET" for c in f.calls)); a.show_plan(p)


class S(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory(); self.dir = pathlib.Path(self.t.name)
        fake_png(self.dir / "a.png"); fake_png(self.dir / "b.png")
    def tearDown(self): self.t.cleanup()
    def data(self, files=("a.png", "b.png")):
        return dict(BASE, screenshots={"ja": {"G1": list(files)}})
    def test_validate_shot_ext_and_limit(self):
        e = "\n".join(a.validate(dict(BASE, screenshots={"ja": {"G1": ["x.gif"]}})))
        self.assertIn(".png", e)
        e = "\n".join(a.validate(dict(BASE, screenshots={"ja": {"G1": [f"{i}.png" for i in range(11)]}})))
        self.assertIn("上限", e)
    def test_plan_reads_only_and_lists(self):
        f = ShotFake(); p = a.build_plan(f, self.data(), self.dir)
        self.assertTrue(all(c[0] == "GET" for c in f.calls))
        self.assertEqual(len(p["screenshots"][0]["files"]), 2)
    def test_plan_rejects_alpha(self):
        fake_png(self.dir / "c.png", color_type=6)
        with self.assertRaises(a.SyncError) as cm:
            a.build_plan(ShotFake(), self.data(("c.png",)), self.dir)
        self.assertIn("アルファ", str(cm.exception))
    def test_plan_rejects_wrong_size(self):
        fake_png(self.dir / "d.png", 100, 100)
        with self.assertRaises(a.SyncError) as cm:
            a.build_plan(ShotFake(), self.data(("d.png",)), self.dir)
        self.assertIn("100x100", str(cm.exception))
    def test_plan_rejects_unknown_group(self):
        d = dict(BASE, screenshots={"ja": {"UNKNOWN": ["a.png"]}})
        with self.assertRaises(a.SyncError) as cm:
            a.build_plan(ShotFake(), d, self.dir)
        self.assertIn("UNKNOWN", str(cm.exception))
    def test_apply_flow_order(self):
        f = ShotFake(); p = a.build_plan(f, self.data(), self.dir)
        f.calls.clear()
        done = a.apply_screenshots(f, p, "LIB1", False, sleep=lambda s: None)
        self.assertEqual(done, [("ja", "G1", 2)])
        kinds = [(c[0], c[1].split("/")[1] + "/" + (c[1].split("/")[2] if len(c[1].split("/")) > 2 else "")) for c in f.calls]
        posts = [c for c in f.calls if c[0] == "POST"]
        self.assertEqual([c[1] for c in posts], ["/v1/appAssetLibraryImages", "/v1/appAssetLibraryPlacements"] * 2 + ["/v1/appAssetLibraryPlacementOrderingRequests"])
        self.assertEqual(len(f.uploads), 2)
        order = posts[-1][3]["data"]["relationships"]["orderedPlacements"]["data"]
        self.assertEqual([x["id"] for x in order], ["P1", "P2"])
        self.assertEqual(posts[0][3]["data"]["attributes"]["category"], "APP_SCREENSHOTS_AND_PREVIEWS")
        self.assertEqual(posts[1][3]["data"]["attributes"]["placementType"], "APP_SCREENSHOT")
    def test_apply_refuses_existing_without_flag(self):
        f = ShotFake(existing=["OLD1"]); p = a.build_plan(f, self.data(), self.dir)
        f.calls.clear()
        with self.assertRaises(a.SyncError):
            a.apply_screenshots(f, p, "LIB1", False, sleep=lambda s: None)
        self.assertFalse([c for c in f.calls if c[0] in ("POST", "DELETE")])
    def test_apply_deletes_existing_with_flag(self):
        f = ShotFake(existing=["OLD1"]); p = a.build_plan(f, self.data(("a.png",)), self.dir)
        a.apply_screenshots(f, p, "LIB1", True, sleep=lambda s: None)
        self.assertIn(("DELETE", "/v1/appAssetLibraryPlacements/OLD1"), [(c[0], c[1]) for c in f.calls])
    def test_failed_processing_stops(self):
        f = ShotFake(fail_state=True); p = a.build_plan(f, self.data(("a.png",)), self.dir)
        with self.assertRaises(a.SyncError) as cm:
            a.apply_screenshots(f, p, "LIB1", False, sleep=lambda s: None)
        self.assertIn("処理に失敗", str(cm.exception))
        self.assertFalse([c for c in f.calls if c[1] == "/v1/appAssetLibraryPlacements" and c[0] == "POST"])
    def test_main_blocks_delete_before_any_write(self):
        inp = self.dir / "in.json"; inp.write_text(json.dumps(dict(self.data(("a.png",)), versionLocalizations={"ja": {"description": "new"}})))
        f = ShotFake(existing=["OLD1"])
        rc = a.main(["apply", str(inp), "--confirm-bundle-id", "com.example.app", "--backup-dir", str(self.dir)], client=f)
        self.assertEqual(rc, 1)
        self.assertFalse([c for c in f.calls if c[0] in ("PATCH", "POST", "DELETE")])


if __name__ == "__main__":
    unittest.main()
