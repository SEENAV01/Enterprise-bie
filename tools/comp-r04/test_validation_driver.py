"""Offline helper contract checks. NOT BIE regression or real-render evidence."""
import copy
import unittest
from run_comp_r04_slice import REQUIRED, check_lock, check_harness, check_media, exclude_font_binaries


def lock_fixture():
    package = {"dependencies": dict(REQUIRED), "devDependencies": {
        "@types/react": "^19.0.0", "@types/react-dom": "^19.0.0"}}
    deps = {**package["dependencies"], **package["devDependencies"]}
    packages = {"": copy.deepcopy(package)}
    for name, version in deps.items():
        packages["node_modules/" + name] = {"version": version.lstrip("^"),
            "resolved": "https://registry.npmjs.org/" + name + "/-/fixture.tgz",
            "integrity": "SYNTHETIC_UNIT_TEST_VALUE_NOT_A_DOWNLOAD_HASH"}
    return package, {"lockfileVersion": 3, "packages": packages}


def harness_fixture():
    return {"passed": True, "accepted": False, "real_book_e2e": "NOT_RUN",
        "scope": "CHECKED_SCENE_IR_TECHNICAL_EXECUTION", "stages": [
            {"stage": s, "passed": True} for s in (
                "checked-source", "full-pinned-typecheck", "real-cli-composition-discovery", "smoke", "full")]}


class DriverChecks(unittest.TestCase):
    def test_font_binaries_are_excluded_from_evidence_exports(self):
        names = ["a.TTF", "b.otf", "c.woff", "d.woff2", "e.ttc", "scene.tsx", "tone.wav"]
        self.assertEqual(exclude_font_binaries("unused", names), names[:5])

    def test_lock_records_actual_type_resolution(self):
        package, lock = lock_fixture()
        self.assertEqual(check_lock(package, lock)["@types/react"], {"requested": "^19.0.0", "resolved": "19.0.0"})

    def test_mismatched_pin_is_rejected(self):
        package, lock = lock_fixture()
        lock["packages"]["node_modules/remotion"]["version"] = "4.0.505"
        with self.assertRaisesRegex(ValueError, "LOCK_PIN_MISMATCH"):
            check_lock(package, lock)

    def test_missing_integrity_is_rejected(self):
        package, lock = lock_fixture()
        del lock["packages"]["node_modules/react"]["integrity"]
        with self.assertRaisesRegex(ValueError, "LOCK_INTEGRITY_MISSING"):
            check_lock(package, lock)

    def test_unreviewed_origin_is_rejected(self):
        package, lock = lock_fixture()
        lock["packages"]["node_modules/react"]["resolved"] = "file:../external"
        with self.assertRaisesRegex(ValueError, "UNREVIEWED_DEPENDENCY_ORIGIN"):
            check_lock(package, lock)

    def test_missing_render_stage_is_rejected(self):
        result = harness_fixture(); result["stages"].pop()
        with self.assertRaisesRegex(ValueError, "MISSING_PASS_STAGE:full"):
            check_harness(result)

    def test_acceptance_promotion_is_rejected(self):
        result = harness_fixture(); result["accepted"] = True
        with self.assertRaisesRegex(ValueError, "ACCEPTANCE_BOUNDARY_CHANGED"):
            check_harness(result)

    def test_passing_technical_receipt_keeps_acceptance_false(self):
        result = harness_fixture(); check_harness(result)
        self.assertIs(result["accepted"], False)

    def test_wrong_frame_count_and_missing_audio_are_rejected(self):
        raw = {"streams": [{"codec_type": "video", "codec_name": "h264", "width": 1280,
            "height": 720, "avg_frame_rate": "24/1", "nb_read_frames": "48", "duration": "2.0"},
            {"codec_type": "audio", "codec_name": "aac"}]}
        check_media(raw, 48)
        with self.assertRaisesRegex(ValueError, "DECODED_FRAME_COUNT_MISMATCH"):
            check_media(raw, 12)
        raw["streams"].pop()
        with self.assertRaisesRegex(ValueError, "EXPECTED_AUDIO_STREAM_MISSING"):
            check_media(raw, 48)

if __name__ == "__main__":
    unittest.main()
