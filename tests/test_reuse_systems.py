import unittest

from src.models import Company, PackagingUnit, ReuseSystem
from src.reuse_systems import add_reuse_system, delete_reuse_system


class ReuseSystemIdTests(unittest.TestCase):
    def test_deleted_system_id_is_not_reused_and_links_are_cleared(self):
        company = Company(company_id="COMP-001")
        systems = [add_reuse_system(company) for _ in range(3)]
        ve = PackagingUnit(
            ve_id="VE-001",
            intended_for_reuse=True,
            reuse_system_id=systems[2].system_id,
        )
        company.packaging_units.append(ve)

        self.assertTrue(delete_reuse_system(company, "SYS-003"))
        self.assertIsNone(ve.reuse_system_id)
        self.assertEqual(add_reuse_system(company).system_id, "SYS-004")

    def test_legacy_system_ids_raise_counter_on_first_use(self):
        company = Company(company_id="COMP-001")
        company.reuse_systems = [ReuseSystem(system_id="SYS-005")]

        self.assertEqual(add_reuse_system(company).system_id, "SYS-006")
