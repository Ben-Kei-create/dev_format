import json, tempfile, unittest, pathlib
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
        d = dict(BASE, reviewDetail={"notes": "連絡は someone@gmail.com か 090-1234-5678"})
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

if __name__ == "__main__":
    unittest.main()
