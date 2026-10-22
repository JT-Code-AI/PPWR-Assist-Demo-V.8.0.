from datetime import date
import unittest

from src.models import (
    AssessmentCase,
    Company,
    MarketFlow,
    ObligationAssessment,
    PackagingUnit,
    RoleAssessment,
)
from src.obligation_engine import build_register
from src.documentation_register import build_documentation_register


class ObligationEngineTests(unittest.TestCase):
    def setUp(self):
        self.case = AssessmentCase(
            case_id="CASE-1",
            assessment_date=date(2026, 10, 22),
            company=Company(
                company_id="COMP-1",
                micro_enterprise_status="no",
                packaging_units=[PackagingUnit("VE-1")],
            ),
        )

    def test_role_applicability_is_separate_from_work_status(self):
        roles = [RoleAssessment(
            role_key="producer", title="Erzeuger", status="yes", scope="VE-1"
        )]
        register = build_register(self.case, roles)
        duty = next(x for x in register if x.obligation_id == "PPWR_ART15_MANUFACTURER_OBLIGATIONS")
        self.assertEqual(duty.applicability, "applicable")
        self.assertEqual(duty.status, "Klärung erforderlich")
        self.assertIn("Anhang VII", duty.requirement_text)

        self.case.obligation_records.append(ObligationAssessment(
            obligation_id=duty.obligation_id,
            title=duty.title,
            scope_type="VE",
            scope_id="VE-1",
            status="Erfüllt",
            evidence=["Anhang_VII.pdf"],
        ))
        updated = build_register(self.case, roles)
        duty = next(x for x in updated if x.obligation_id == duty.obligation_id)
        self.assertEqual(duty.status, "Erfüllt")
        self.assertEqual(duty.evidence, ["Anhang_VII.pdf"])

    def test_article_21_merges_art15_and_keeps_microenterprise_check(self):
        ve = self.case.company.packaging_units[0]
        ve.article21_manufacturer_trigger = "yes"
        roles = [
            RoleAssessment(role_key="importer", title="Importeur", status="yes", scope="VE-1"),
        ]
        register = build_register(self.case, roles)
        art15 = [x for x in register if x.obligation_id == "PPWR_ART15_MANUFACTURER_OBLIGATIONS"]
        self.assertEqual(len(art15), 1)
        self.assertIn("ROLE_ART21_IMPORTER", art15[0].trigger_ids)
        self.assertIn("PPWR Art. 21", art15[0].sources)

        self.case.company.micro_enterprise_status = "clarification_required"
        register = build_register(self.case, roles)
        art15 = next(x for x in register if x.obligation_id == "PPWR_ART15_MANUFACTURER_OBLIGATIONS")
        self.assertEqual(art15.applicability, "clarification_required")
        self.assertTrue(art15.missing_facts)

    def test_epr_register_is_scoped_per_member_state(self):
        ve = self.case.company.packaging_units[0]
        ve.market_flows = [
            MarketFlow("FLOW-1", target_country="DE"),
            MarketFlow("FLOW-2", target_country="NL"),
            MarketFlow("FLOW-3", target_country="DE"),
        ]
        roles = [
            RoleAssessment(role_key="manufacturer", title="Hersteller", status="yes", scope="FLOW-1"),
            RoleAssessment(role_key="manufacturer", title="Hersteller", status="yes", scope="FLOW-2"),
            RoleAssessment(role_key="manufacturer", title="Hersteller", status="yes", scope="FLOW-3"),
        ]
        register = build_register(self.case, roles)
        registrations = [x for x in register if x.obligation_id == "PPWR_ART44_PRODUCER_REGISTRATION"]
        self.assertEqual({x.country for x in registrations}, {"DE", "NL"})
        self.assertEqual({x.scope_id for x in registrations}, {"COMP-1"})
        german = next(x for x in registrations if x.country == "DE")
        self.assertIn("FLOW-1", german.trigger_ids)
        self.assertIn("FLOW-3", german.trigger_ids)

    def test_unknown_act_date_is_future_and_not_guessed(self):
        ve = self.case.company.packaging_units[0]
        ve.packaging_type_candidates = ["transport"]
        ve.self_filling_sales_grouped = "yes"
        register = build_register(self.case, [])
        duty = next(x for x in register if x.obligation_id == "PPWR_ART24_1_VOIDSPACE_50_PERCENT")
        self.assertEqual(duty.applicability, "future")
        self.assertTrue(duty.depends_on_act)
        self.assertIn("drei Jahre", duty.time_rule)

    def test_future_duties_are_routed_to_outlook_and_docs_are_triggered(self):
        from src.models import PackagingComponent

        ve = self.case.company.packaging_units[0]
        ve.packaging_type_candidates = ["transport"]
        ve.self_filling_sales_grouped = "yes"
        ve.components = [PackagingComponent("PKG-1", food_contact=True)]
        roles = [RoleAssessment(
            role_key="producer", title="Erzeuger", status="yes", scope="VE-1"
        )]
        register = build_register(self.case, roles)
        docs, future = build_documentation_register(register)

        future_ids = {item.obligation_id for item in future}
        self.assertIn("PPWR_ART24_1_VOIDSPACE_50_PERCENT", future_ids)
        doc_titles = {item["title"] for item in docs}
        self.assertIn("Technische Dokumentation nach Anhang VII", doc_titles)
        self.assertIn("PFAS-Nachweis nach Art. 5 Abs. 5", doc_titles)

        ve.components = [PackagingComponent("PKG-1", food_contact=False)]
        register = build_register(self.case, roles)
        docs, _ = build_documentation_register(register)
        self.assertNotIn(
            "PFAS-Nachweis nach Art. 5 Abs. 5",
            {item["title"] for item in docs},
        )


if __name__ == "__main__":
    unittest.main()
