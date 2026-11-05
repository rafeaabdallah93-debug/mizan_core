"""Tests for provision_site().

dev.localhost (and CI's test_site after other test modules ran) already has several companies,
while provisioning is meant for a site with at most one. Only the "which companies exist"
lookup (_existing_companies) is patched, to stand in for a single-company site; the code under
test runs for real. The setup-wizard state is reset inside the test transaction (rolled back
afterwards) so that marking it complete is actually exercised. The fresh-site path (ERPNext's
fixtures on a site with no records at all) is covered end-to-end on a new site, not here.
"""

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from mizan_core.setup.provision import provision_site

TEST_COMPANY = "Mizan Test Co"
TEST_ABBR = "MTC"
EXISTING = "mizan_core.setup.provision._existing_companies"


def only_company(name):
	return patch(EXISTING, return_value=[name])


class TestProvision(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		# Registered first so it runs last (LIFO), after the class rollback: drop cached
		# settings/defaults that tests changed only inside the rolled-back transaction.
		cls.addClassCleanup(frappe.clear_cache)
		super().setUpClass()
		cls.language = frappe.db.get_single_value("System Settings", "language") or "en"

	def reset_setup_wizard(self):
		"""Put the site back in the state of a fresh site: wizard not done."""
		frappe.db.set_value(
			"Installed Application", {"app_name": ("in", ["frappe", "erpnext"])}, "is_setup_complete", 0
		)
		frappe.db.set_single_value("System Settings", "setup_complete", 0)
		frappe.db.set_default("desktop:home_page", "setup-wizard")
		frappe.clear_cache()
		self.assertFalse(frappe.is_setup_complete())

	def snapshot(self):
		return {
			"company": frappe.db.get_value("Company", TEST_COMPANY, "modified"),
			"accounts": frappe.get_all(
				"Account", filters={"company": TEST_COMPANY}, fields=["name", "modified"], order_by="name"
			),
			"apps": frappe.get_all(
				"Installed Application", fields=["app_name", "is_setup_complete", "modified"], order_by="name"
			),
			"system_settings": frappe.db.get_value("System Settings", None, "modified"),
			"global_defaults": frappe.db.get_value("Global Defaults", None, "modified"),
			"home_page": frappe.db.get_default("desktop:home_page"),
			"fiscal_years": frappe.db.count("Fiscal Year"),
			"price_lists": frappe.db.count("Price List"),
		}

	def test_provision_marks_setup_complete(self):
		self.reset_setup_wizard()
		with only_company(TEST_COMPANY):
			provision_site(TEST_COMPANY, TEST_ABBR, language=self.language)

		self.assertTrue(frappe.is_setup_complete())
		self.assertTrue(frappe.db.get_single_value("System Settings", "setup_complete"))
		# The desk opens the setup wizard while this default still points at it.
		self.assertNotEqual(frappe.db.get_default("desktop:home_page"), "setup-wizard")
		self.assertTrue(frappe.db.get_value("Currency", "EGP", "enabled"))
		self.assertEqual(frappe.db.get_value("Company", TEST_COMPANY, "default_currency"), "EGP")

	def test_provision_is_idempotent(self):
		with only_company(TEST_COMPANY):
			provision_site(TEST_COMPANY, TEST_ABBR, language=self.language)
			before = self.snapshot()
			provision_site(TEST_COMPANY, TEST_ABBR, language=self.language)
		self.assertEqual(self.snapshot(), before)
		self.assertTrue(frappe.is_setup_complete())

	def test_provision_sets_language(self):
		other = "ar" if self.language != "ar" else "en"
		with only_company(TEST_COMPANY):
			provision_site(TEST_COMPANY, TEST_ABBR, language=other)
		self.assertEqual(frappe.db.get_single_value("System Settings", "language"), other)
		self.assertEqual(frappe.db.get_default("lang"), other)

	def test_provision_refuses_second_company(self):
		other = "Mizan Test Second Provisioned Co"
		self.assertFalse(frappe.db.exists("Company", other))
		with only_company(TEST_COMPANY), self.assertRaises(frappe.ValidationError) as caught:
			provision_site(other, "MTSPC")
		self.assertIn(TEST_COMPANY, str(caught.exception))
		self.assertFalse(frappe.db.exists("Company", other))

	def test_invalid_language_rejected(self):
		before = frappe.db.get_single_value("System Settings", "language")
		with only_company(TEST_COMPANY):
			for language in ("fr", "", "arabic"):
				with self.assertRaises(frappe.ValidationError):
					provision_site(TEST_COMPANY, TEST_ABBR, language=language)
		self.assertEqual(frappe.db.get_single_value("System Settings", "language"), before)
