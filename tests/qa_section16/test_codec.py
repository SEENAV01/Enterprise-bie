import json
import unittest
from bie.qa.release_v2 import ContractError
from bie.qa.release_v2.codec import dumps, loads, bundle_from_dict
from bie.qa.release_v2.contracts import MAX_JSON_BYTES
from helpers import CaseTest


class CodecTests(CaseTest):
    def test_roundtrip_preserves_digest_and_bytes(self):
        raw = dumps(self.bundle)
        restored = loads(raw)
        self.assertEqual(restored.content_digest, self.bundle.content_digest)
        self.assertEqual(dumps(restored), raw)

    def test_unknown_top_level_authorization_is_rejected(self):
        data = json.loads(dumps(self.bundle))
        data["product_accepted"] = True
        with self.assertRaisesRegex(ContractError, "OBJECT_FIELDS_MISMATCH"):
            loads(json.dumps(data).encode())

    def test_unknown_nested_fields_rejected(self):
        for target in ("candidate", "evidence", "report"):
            data = json.loads(dumps(self.bundle))
            obj = data["candidate"] if target == "candidate" else data["evidence"][0]
            if target == "report":
                obj = obj["report"]
            obj["skip_validation"] = True
            with self.subTest(target=target), self.assertRaises(ContractError):
                loads(json.dumps(data).encode())

    def test_missing_fields_are_not_defaulted(self):
        data = json.loads(dumps(self.bundle))
        del data["evidence"][0]["signature"]
        with self.assertRaises(ContractError):
            loads(json.dumps(data).encode())

    def test_duplicate_json_keys_rejected(self):
        with self.assertRaisesRegex(ContractError, "DUPLICATE_JSON_KEY"):
            loads(b'{"schema_version":"1.0.0","schema_version":"2.0.0"}')

    def test_non_finite_json_numbers_rejected(self):
        for number in (b"NaN", b"Infinity", b"-Infinity", b"1.0", b"1e3"):
            with self.subTest(number=number), self.assertRaises(ContractError):
                loads(b'{"number":' + number + b'}')

    def test_invalid_utf8_rejected(self):
        with self.assertRaises(ContractError):
            loads(b'\xff\xfe')

    def test_byte_order_mark_rejected(self):
        with self.assertRaises(ContractError):
            loads(b'\xef\xbb\xbf' + dumps(self.bundle))

    def test_truncated_and_trailing_json_rejected(self):
        for raw in (dumps(self.bundle)[:-1], dumps(self.bundle) + b' {}'):
            with self.subTest(raw=raw[:20]), self.assertRaises(ContractError):
                loads(raw)

    def test_size_bound_checked_before_parse(self):
        with self.assertRaisesRegex(ContractError, "JSON_SIZE_OR_TYPE"):
            loads(b" " * (MAX_JSON_BYTES + 1))

    def test_non_bytes_input_rejected(self):
        for raw in ("{}", bytearray(b"{}"), None, b""):
            with self.subTest(raw=raw), self.assertRaises(ContractError):
                loads(raw)

    def test_deep_nesting_is_bounded(self):
        with self.assertRaises(ContractError):
            loads(b'[' * 100 + b'0' + b']' * 100)

    def test_boolean_not_integer_on_wire(self):
        data = json.loads(dumps(self.bundle))
        data["candidate"]["artifacts"][0]["size"] = True
        with self.assertRaises(ContractError):
            loads(json.dumps(data).encode())

    def test_object_cannot_substitute_for_array(self):
        data = json.loads(dumps(self.bundle))
        data["evidence"] = {}
        with self.assertRaisesRegex(ContractError, "EXPECTED_ARRAY"):
            loads(json.dumps(data).encode())

    def test_no_coercion_of_numeric_strings(self):
        data = json.loads(dumps(self.bundle))
        data["evidence"][0]["created_at"] = "1790413170"
        with self.assertRaises(ContractError):
            loads(json.dumps(data).encode())

    def test_arbitrary_python_objects_are_rejected(self):
        with self.assertRaises(ContractError):
            bundle_from_dict(object())

    def test_huge_integer_rejected_as_contract_error(self):
        with self.assertRaises(ContractError):
            loads(b'{"number":' + b'9' * 5000 + b'}')

    def test_non_string_mapping_key_rejected_as_contract_error(self):
        with self.assertRaisesRegex(ContractError, "NON_STRING_JSON_KEY"):
            bundle_from_dict({1: "unexpected", "schema_version": "2.0.0"})


if __name__ == "__main__":
    unittest.main()
