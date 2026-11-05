import frappe
from frappe.tests import IntegrationTestCase

from mizan_core.branding import BRAND_NAME_AR, BRAND_NAME_EN, apply_branding


class TestBranding(IntegrationTestCase):
	def test_app_name_is_brand(self):
		apply_branding()
		frappe.clear_cache()
		self.assertEqual(frappe.db.get_single_value("Website Settings", "app_name"), BRAND_NAME_EN)
		self.assertEqual(frappe.db.get_single_value("System Settings", "app_name"), BRAND_NAME_EN)
		self.assertEqual(frappe.get_website_settings("app_name"), BRAND_NAME_EN)

	def test_no_erpnext_in_brand(self):
		self.assertNotIn("erpnext", BRAND_NAME_EN.lower())
		self.assertNotIn("erpnext", BRAND_NAME_AR.lower())

	def test_apply_branding_is_idempotent(self):
		def snapshot():
			return (
				frappe.db.get_single_value("System Settings", "app_name"),
				frappe.db.get_single_value("Website Settings", "app_name"),
				frappe.db.get_single_value("Website Settings", "app_logo"),
				frappe.db.get_single_value("Website Settings", "favicon"),
				frappe.db.get_single_value("Website Settings", "brand_html"),
				frappe.db.get_single_value("Website Settings", "footer_powered"),
				frappe.db.get_single_value("Navbar Settings", "app_logo"),
			)

		apply_branding()
		first = snapshot()
		apply_branding()
		self.assertEqual(first, snapshot())
