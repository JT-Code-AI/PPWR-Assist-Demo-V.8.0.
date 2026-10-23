import unittest
from datetime import date

from src.models import (
    AssessmentCase,
    Company,
    PackagingComponent,
    PackagingUnit,
    ReuseSystem,
)
from src.special_rules import build_obligations


def make_case(*, assessment_date=date(2026, 10, 22)):
    company = Company(company_id="COMP-001")
    return AssessmentCase(
        case_id="CASE-001",
        company=company,
        assessment_date=assessment_date,
    )


class SpecialRuleTests(unittest.TestCase):
    def test_pfas_is_scoped_to_food_contact_component(self):
        case = make_case()
        ve = PackagingUnit(ve_id="VE-001", name="Flasche")
        ve.components = [
            PackagingComponent(pkg_id="PKG-001", name="Deckel", food_contact=True),
            PackagingComponent(pkg_id="PKG-002", name="Karton", food_contact=False),
        ]
        case.company.packaging_units = [ve]
        items = build_obligations(case)
        pfas = [item for item in items if item["trigger_ids"] == ["SPEC_PFAS"]]
        self.assertEqual(len(pfas), 1)
        self.assertEqual(pfas[0]["scope_id"], "PKG-001")
        self.assertIn("25 ppb", pfas[0]["summary"])

    def test_reuse_system_is_background_object_and_merged_by_id(self):
        case = make_case()
        case.company.reuse_systems = [ReuseSystem("SYS-001", "Pool", "open")]
        ve = PackagingUnit(ve_id="VE-001", name="Kiste", intended_for_reuse=True, reuse_system_id="SYS-001")
        case.company.packaging_units = [ve]
        items = build_obligations(case)
        self.assertEqual(sum(item["obligation_id"] == "PPWR_ART11_REUSABILITY_REVIEW" for item in items), 1)
        system = next(item for item in items if item["trigger_ids"] == ["SPEC_REUSE_SYSTEM"])
        self.assertIn("Art. 26 und 27", system["summary"])

    def test_horeca_uses_existing_company_fields_and_micro_exception(self):
        case = make_case(assessment_date=date(2028, 3, 1))
        case.company.activities = ["direct_end_recipient"]
        case.company.sector_triggers = ["hospitality_takeaway"]
        case.company.micro_enterprise_status = "yes"
        items = build_obligations(case)
        art32 = next(item for item in items if item["obligation_id"] == "PPWR_ART32_OWN_CONTAINERS")
        art33 = next(item for item in items if item["obligation_id"] == "PPWR_ART33_REUSE_OFFER")
        self.assertEqual(art32["status"], "applicable")
        self.assertEqual(art33["status"], "exempt")

    def test_plastic_bag_notice_includes_threshold_and_exceptions(self):
        case = make_case(assessment_date=date(2029, 1, 1))
        ve = PackagingUnit(ve_id="VE-001", is_plastic_carrier_bag=True)
        case.company.packaging_units = [ve]
        bag = next(item for item in build_obligations(case) if item["trigger_ids"] == ["SPEC_BAG"])
        self.assertEqual(bag["status"], "upcoming")
        self.assertIn("unter 15 µm", bag["summary"])
        self.assertIn("Hygienezwecke", bag["summary"])

    def test_unknown_voidspace_implementing_act_stays_review(self):
        case = make_case()
        case.company.activities = ["fill_purchased_packaging"]
        ve = PackagingUnit(ve_id="VE-001", packaging_type_candidates=["transport"])
        case.company.packaging_units = [ve]
        item = next(item for item in build_obligations(case) if item["obligation_id"] == "PPWR_ART24_1_VOIDSPACE_50_PERCENT")
        self.assertEqual(item["status"], "scheduled_review")
        self.assertIn("je nachdem", item["summary"])

    def test_beverage_emits_three_independent_obligations(self):
        case = make_case()
        ve = PackagingUnit(
            ve_id="VE-001",
            is_beverage_packaging=True,
            beverage_packaging_type="single_use_plastic_bottle",
        )
        case.company.packaging_units = [ve]
        items = build_obligations(case)
        beverage = [item for item in items if "SPEC_BEVERAGE" in item["trigger_ids"]]
        bases = {source for item in beverage for source in item["legal_basis"]}
        self.assertTrue(any("Art. 7" in source for source in bases))
        self.assertTrue(any("Art. 29" in source for source in bases))
        self.assertTrue(any("Art. 50" in source for source in bases))

    def test_compost_format_and_innovative_path_are_reviewable(self):
        case = make_case()
        ve = PackagingUnit(
            ve_id="VE-001",
            compostable_format="tea_coffee_bag",
            potentially_innovative=True,
        )
        case.company.packaging_units = [ve]
        items = build_obligations(case)
        self.assertIn("SPEC_COMPOST", [trigger for item in items for trigger in item["trigger_ids"]])
        innovation = next(item for item in items if item["trigger_ids"] == ["SPEC_INNOVATIVE"])
        self.assertEqual(innovation["status"], "review")
        self.assertIn("keine automatische Ausnahme", innovation["summary"])

    def test_duplicate_article_29_notice_merges_triggers(self):
        case = make_case()
        ve = PackagingUnit(
            ve_id="VE-001",
            is_beverage_packaging=True,
            intended_for_reuse=True,
            packaging_type_candidates=["sales", "transport"],
            packaging_functions=["transport"],
        )
        case.company.packaging_units = [ve]
        items = build_obligations(case)
        art29 = [item for item in items if item["obligation_id"] == "PPWR_ART29_REUSE_REQUIREMENTS_REVIEW"]
        self.assertEqual(len(art29), 1)
        self.assertIn("SPEC_BEVERAGE", art29[0]["trigger_ids"])
        self.assertIn("SPEC_REUSE", art29[0]["trigger_ids"])

    def test_dangerous_and_sensitive_do_not_create_global_exemption(self):
        case = make_case()
        ve = PackagingUnit(
            ve_id="VE-001",
            used_for_dangerous_goods=True,
            sensitive_packaging_category="ivd",
        )
        case.company.packaging_units = [ve]
        items = build_obligations(case)
        self.assertTrue(all(item["status"] != "not_applicable" for item in items))
        self.assertEqual(sum(item["trigger_ids"] == ["SPEC_DANGEROUS"] for item in items), 1)
        self.assertEqual(sum(item["trigger_ids"] == ["SPEC_SENSITIVE"] for item in items), 1)

    def test_primary_trigger_uses_leading_packaging_type_only(self):
        case = make_case()
        ve = PackagingUnit(
            ve_id="VE-001",
            packaging_type_candidates=["sales", "primary_production"],
            primary_packaging_type="sales",
        )
        case.company.packaging_units = [ve]
        self.assertNotIn("SPEC_PRIMARY", [trigger for item in build_obligations(case) for trigger in item["trigger_ids"]])
        ve.primary_packaging_type = "primary_production"
        self.assertIn("SPEC_PRIMARY", [trigger for item in build_obligations(case) for trigger in item["trigger_ids"]])


if __name__ == "__main__":
    unittest.main()
