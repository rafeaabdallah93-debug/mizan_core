import frappe
from frappe.tests import IntegrationTestCase

from mizan_core.branding import BRAND_NAME_AR, BRAND_NAME_EN, apply_branding, rewrite_boot_apps


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

	def test_boot_apps_show_brand(self):
		from frappe.boot import get_app_data

		bootinfo = frappe._dict(app_data=get_app_data())
		rewrite_boot_apps(bootinfo)
		self.assertTrue(bootinfo.app_data)
		for app in bootinfo.app_data:
			self.assertNotIn("erpnext", (app.get("app_title") or "").lower())
			logo = app.get("app_logo_url")
			logos = logo if isinstance(logo, list | tuple) else [logo]
			for item in logos:
				self.assertNotIn("erpnext", (item or "").lower())

	def test_emails_carry_no_erpnext_footer(self):
		from frappe.email.email_body import get_footer

		apply_branding()
		self.assertEqual(frappe.db.get_single_value("System Settings", "disable_standard_email_footer"), 1)
		self.assertNotIn("erpnext", get_footer(None).lower())

	def test_no_visible_workspace_named_erpnext(self):
		apply_branding()
		for workspace in frappe.get_all(
			"Workspace", filters={"public": 1, "is_hidden": 0}, fields=["name", "label", "title"]
		):
			for value in (workspace.label, workspace.title):
				self.assertNotIn("erpnext", (value or "").lower(), workspace.name)
		if frappe.db.exists("Workspace", "ERPNext Settings"):
			self.assertEqual(
				frappe.db.get_value("Workspace", "ERPNext Settings", ["label", "title"]), ("Settings", "Settings")
			)
