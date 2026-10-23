import json
import unittest

from src.models import (
    AssessmentCase,
    Company,
    MarketFlow,
    PackagingComponent,
    PackagingUnit,
    ObligationAssessment,
    ReuseSystem,
)
from src.serialization import case_from_json, case_to_json


class CaseSerializationTests(unittest.TestCase):
    def test_round_trip_keeps_nested_and_special_path_data(self):
        case = AssessmentCase(case_id="CASE-008")
        case.company = Company(
            company_id="COMP-008",
            name="Beispiel",
            reuse_systems=[ReuseSystem("RS-001", "Pool", "open")],
            packaging_units=[PackagingUnit(
                "VE-001",
                intended_for_reuse=True,
                reuse_system_id="RS-001",
                is_beverage_packaging=True,
                market_flows=[MarketFlow("FLOW-001", label="Direktversand")],
                components=[PackagingComponent(
                    "PKG-001", name="Flasche", food_contact=True
                )],
            )],
        )
        case.obligation_records = [ObligationAssessment(
            obligation_id="PPWR_ART15_MANUFACTURER_OBLIGATIONS",
            title="Pflichten des Erzeugers",
            scope_type="VE",
            scope_id="VE-001",
            applicability="applicable",
            status="Erfüllt",
            evidence=["Doku/PPWR.pdf"],
            exceptions=["Einzelfallprüfung"],
        )]

        loaded = case_from_json(case_to_json(case))
        self.assertEqual(loaded.case_id, "CASE-008")
        self.assertEqual(loaded.company.reuse_systems[0].name, "Pool")
        self.assertTrue(loaded.company.packaging_units[0].intended_for_reuse)
        self.assertTrue(loaded.company.packaging_units[0].components[0].food_contact)
        self.assertEqual(
            loaded.company.packaging_units[0].market_flows[0].flow_id,
            "FLOW-001",
        )
        self.assertEqual(
            loaded.company.packaging_units[0].market_flows[0].label,
            "Direktversand",
        )
        self.assertEqual(loaded.schema_version, "0.8.2")
        self.assertEqual(loaded.obligation_records[0].status, "Erfüllt")
        self.assertEqual(loaded.obligation_records[0].evidence, ["Doku/PPWR.pdf"])
        self.assertEqual(loaded.obligation_records[0].exceptions, ["Einzelfallprüfung"])

    def test_legacy_direct_json_fills_new_fields_with_defaults(self):
        legacy = {
            "case_id": "CASE-OLD",
            "schema_version": "0.7.2",
            "company": {
                "company_id": "COMP-OLD",
                "packaging_units": [{
                    "ve_id": "VE-001",
                    "components": [{"pkg_id": "PKG-001"}],
                    "market_flows": [{"flow_id": "FLOW-001"}],
                }],
            },
        }
        loaded = case_from_json(json.dumps(legacy))
        ve = loaded.company.packaging_units[0]
        self.assertEqual(loaded.schema_version, "0.8.2")
        self.assertFalse(ve.intended_for_reuse)
        self.assertFalse(ve.components[0].food_contact)
        self.assertEqual(ve.compostable_format, "no")
        self.assertEqual(ve.article21_para1_trigger, "clarification_required")
        self.assertEqual(ve.market_flows[0].label, "")

    def test_v085_article21_field_name_is_migrated(self):
        legacy = {
            "case_id": "CASE-085",
            "company": {
                "company_id": "COMP-085",
                "packaging_units": [{
                    "ve_id": "VE-001",
                    "article21_manufacturer_trigger": "yes",
                }],
            },
        }
        loaded = case_from_json(json.dumps(legacy))
        self.assertEqual(
            loaded.company.packaging_units[0].article21_para1_trigger,
            "yes",
        )

    def test_v08_export_wrapper_loads_and_migrates_obligations(self):
        old_export = {
            "format": "ppwr-assist-case",
            "schema_version": "0.8.0",
            "case": {
                "case_id": "CASE-08",
                "schema_version": "0.8.0",
                "company": {"company_id": "COMP-08"},
            },
        }
        loaded = case_from_json(json.dumps(old_export))
        self.assertEqual(loaded.schema_version, "0.8.2")
        self.assertEqual(loaded.obligation_records, [])

    def test_invalid_case_is_rejected_with_actionable_message(self):
        with self.assertRaisesRegex(ValueError, "Prüffall"):
            case_from_json('{"hello": "world"}')


if __name__ == "__main__":
    unittest.main()
