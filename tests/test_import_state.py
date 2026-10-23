import unittest

from src.import_state import install_imported_case
from src.models import AssessmentCase, Company, MarketFlow, PackagingComponent, PackagingUnit


class ImportSessionStateTests(unittest.TestCase):
    def test_import_clears_old_widget_values_and_rebuilds_sequences(self):
        case = AssessmentCase(
            case_id="CASE-NEW",
            company=Company(
                company_id="COMP-NEW",
                name="Bäckerei",
                country="DE",
                packaging_units=[PackagingUnit(
                    "VE-004",
                    components=[PackagingComponent("PKG-006")],
                    market_flows=[MarketFlow("FLOW-008")],
                )],
            ),
        )
        session = {
            "company_name_v072": "Alter Betrieb",
            "company_country_v072": "FR",
            "name_VE-004": "Alte VE",
            "selected_object": {"type": "ve", "id": "VE-004"},
            "widget_generation": 7,
            "unrelated_widget": "stale",
        }

        install_imported_case(session, case)

        self.assertEqual(session["case"].company.name, "Bäckerei")
        self.assertEqual(session["case"].company.country, "DE")
        self.assertEqual(session["selected_object"], {
            "type": "company", "id": "COMP-NEW"
        })
        self.assertEqual(session["next_ve_number"], 5)
        self.assertEqual(session["next_pkg_number"], 7)
        self.assertEqual(session["next_flow_number"], 9)
        self.assertEqual(session["widget_generation"], 8)
        self.assertNotIn("company_name_v072", session)
        self.assertNotIn("company_country_v072", session)
        self.assertNotIn("name_VE-004", session)
        self.assertNotIn("unrelated_widget", session)


if __name__ == "__main__":
    unittest.main()
