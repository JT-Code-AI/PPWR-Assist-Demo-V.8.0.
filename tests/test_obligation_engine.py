from datetime import date
import unittest

from src.models import (
    AssessmentCase,
    Company,
    MarketFlow,
    ObligationAssessment,
    PackagingComponent,
    PackagingUnit,
    RoleAssessment,
)
from src.obligation_engine import build_register
from src.documentation_register import OBLIGATION_DOCUMENTS, build_documentation_register


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

    def test_article_21_has_separate_duty_and_keeps_microenterprise_check(self):
        ve = self.case.company.packaging_units[0]
        ve.article21_para1_trigger = "yes"
        roles = [
            RoleAssessment(role_key="importer", title="Importeur", status="yes", scope="VE-1"),
        ]
        register = build_register(self.case, roles)
        art21 = [x for x in register if x.obligation_id == "PPWR_ART21_PRODUCER_OBLIGATIONS"]
        self.assertEqual(len(art21), 1)
        self.assertIn("ROLE_ART21_IMPORTER", art21[0].trigger_ids)
        self.assertIn("PPWR Art. 21 Abs. 1–2", art21[0].sources)
        self.assertIn("gilt für diese Verpackung als Erzeuger", art21[0].requirement_text)
        self.assertFalse(any(
            item.obligation_id == "PPWR_ART15_MANUFACTURER_OBLIGATIONS"
            for item in register
        ))

        self.case.company.micro_enterprise_status = "clarification_required"
        register = build_register(self.case, roles)
        art21 = next(x for x in register if x.obligation_id == "PPWR_ART21_PRODUCER_OBLIGATIONS")
        self.assertEqual(art21.applicability, "clarification_required")
        self.assertTrue(art21.missing_facts)
        self.assertEqual(art21.title, "Art. 21: Übernahme der Erzeugerpflichten nach Art. 15")
        self.assertIn("Bei erfülltem Tatbestand", art21.requirement_text)

    def test_article_21_documentation_is_derived_from_separate_obligation(self):
        ve = self.case.company.packaging_units[0]
        ve.article21_para1_trigger = "yes"
        roles = [RoleAssessment(
            role_key="importer", title="Importeur", status="yes", scope="VE-1"
        )]
        art21 = next(
            item for item in build_register(self.case, roles)
            if item.obligation_id == "PPWR_ART21_PRODUCER_OBLIGATIONS"
        )

        documents, future = build_documentation_register([art21])

        self.assertFalse(future)
        self.assertEqual(len(documents), 5)
        self.assertTrue(all(item["parent"] is art21 for item in documents))

    def test_article_21_microenterprise_and_union_supplier_prevent_duty_even_if_trigger_unclear(self):
        ve = self.case.company.packaging_units[0]
        self.case.company.micro_enterprise_status = "yes"
        ve.article21_para1_trigger = "clarification_required"
        ve.components = [PackagingComponent(
            "PKG-1", procurement_type="standard_product", supplier_country="DE"
        )]
        roles = [RoleAssessment(
            role_key="distributor", title="Vertreiber", status="yes", scope="VE-1"
        )]

        register = build_register(self.case, roles)

        self.assertFalse(any(
            item.obligation_id in {
                "PPWR_ART15_MANUFACTURER_OBLIGATIONS",
                "PPWR_ART21_PRODUCER_OBLIGATIONS",
            }
            for item in register
        ))

    def test_article_21_microenterprise_third_country_supplier_does_not_apply_exception(self):
        ve = self.case.company.packaging_units[0]
        self.case.company.micro_enterprise_status = "yes"
        ve.article21_para1_trigger = "yes"
        ve.components = [PackagingComponent(
            "PKG-1", procurement_type="standard_product", supplier_country="THIRD_COUNTRY"
        )]
        roles = [RoleAssessment(
            role_key="distributor", title="Vertreiber", status="yes", scope="VE-1"
        )]

        register = build_register(self.case, roles)
        art15 = next(x for x in register if x.obligation_id == "PPWR_ART21_PRODUCER_OBLIGATIONS")

        self.assertEqual(art15.applicability, "applicable")
        self.assertIn("PPWR Art. 21 Abs. 1–2", art15.sources)

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

    def test_all_defined_obligation_ids_have_documentation_mappings(self):
        from src.obligation_engine import ROLE_DEFINITIONS
        from src.special_rules import build_obligations

        ve = self.case.company.packaging_units[0]
        ve.intended_for_reuse = True
        ve.is_plastic_carrier_bag = True
        ve.compostable_format = "tea_coffee_bag"
        ve.is_beverage_packaging = True
        ve.potentially_innovative = True
        ve.sensitive_packaging_category = "medical_device"
        ve.used_for_dangerous_goods = True
        ve.packaging_type_candidates = ["grouped", "transport", "sales"]
        ve.packaging_functions = ["transport"]
        ve.self_filling_sales_grouped = "yes"
        ve.primary_packaging_type = "primary_production"
        ve.individually_designed_large_goods = True
        ve.components = [PackagingComponent("PKG-1", food_contact=True)]
        self.case.company.activities = ["direct_end_recipient"]
        self.case.company.sector_triggers = ["hospitality_takeaway"]

        special_ids = {
            item["obligation_id"]
            for item in build_obligations(self.case)
        }
        self.assertTrue(special_ids.issubset(OBLIGATION_DOCUMENTS))
        self.assertTrue(set(ROLE_DEFINITIONS[key].obligation_id for key in ROLE_DEFINITIONS).issubset(OBLIGATION_DOCUMENTS))
        self.assertIn("PPWR_ART44_PRODUCER_REGISTRATION", OBLIGATION_DOCUMENTS)
        self.assertIn("PPWR_ART45_EPR_COUNTRY_REQUIREMENTS", OBLIGATION_DOCUMENTS)

    def test_importer_distributor_and_epr_obligations_derive_tasks(self):
        self.case.company.packaging_units[0].market_flows = [MarketFlow("FLOW-1", target_country="DE")]
        roles = [
            RoleAssessment(role_key="importer", title="Importeur", status="yes", scope="VE-1"),
            RoleAssessment(role_key="distributor", title="Vertreiber", status="yes", scope="VE-1"),
            RoleAssessment(role_key="manufacturer", title="Hersteller", status="yes", scope="FLOW-1"),
        ]
        obligations = build_register(self.case, roles)
        documents, _ = build_documentation_register(obligations)
        derived_ids = {entry["parent"].obligation_id for entry in documents}
        self.assertTrue({
            "PPWR_ART18_IMPORTER_OBLIGATIONS",
            "PPWR_ART19_DISTRIBUTOR_OBLIGATIONS",
            "PPWR_ART44_PRODUCER_REGISTRATION",
            "PPWR_ART45_EPR_COUNTRY_REQUIREMENTS",
        }.issubset(derived_ids))

    def test_unmapped_new_obligation_is_visible_as_internal_clarification(self):
        unknown = ObligationAssessment(
            obligation_id="NEW_RULE",
            title="Neue Pflicht",
            scope_type="VE",
            scope_id="VE-1",
        )
        documents, _ = build_documentation_register([unknown])
        self.assertEqual(len(documents), 1)
        self.assertIn("fachlich ergänzen", documents[0]["details"][0])
        self.assertIn("keine zusätzliche gesetzliche Pflicht", documents[0]["details"][0])


if __name__ == "__main__":
    unittest.main()
