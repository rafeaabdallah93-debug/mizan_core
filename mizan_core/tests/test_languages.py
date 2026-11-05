import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils.jinja_globals import is_rtl

from mizan_core.setup.languages import enable_languages

TEST_EMAIL = "mizan-lang-test@example.com"


class TestLanguages(IntegrationTestCase):
	def test_ar_and_en_enabled(self):
		# The rows must exist, otherwise "disabling" them below would pass vacuously.
		for lang in ("ar", "en"):
			self.assertTrue(frappe.db.exists("Language", lang), f"Language {lang} missing")

		def restore():
			for lang in ("ar", "en"):
				frappe.db.set_value("Language", lang, "enabled", 1)
			frappe.clear_cache()

		self.addCleanup(restore)
		# Start from a disabled state so the test proves enable_languages() does the work.
		for lang in ("ar", "en"):
			frappe.db.set_value("Language", lang, "enabled", 0)
		enable_languages()
		enable_languages()  # idempotent
		for lang in ("ar", "en"):
			self.assertEqual(frappe.db.get_value("Language", lang, "enabled"), 1)

	def test_user_can_switch_language(self):
		if not frappe.db.exists("User", TEST_EMAIL):
			frappe.get_doc(
				{"doctype": "User", "email": TEST_EMAIL, "first_name": "Lang", "send_welcome_email": 0}
			).insert(ignore_permissions=True)
		user = frappe.get_doc("User", TEST_EMAIL)
		for lang in ("ar", "en"):
			user.language = lang
			user.save(ignore_permissions=True)
			self.assertEqual(frappe.db.get_value("User", TEST_EMAIL, "language"), lang)

	def test_arabic_is_rtl(self):
		original = frappe.local.lang
		try:
			frappe.local.lang = "ar"
			self.assertTrue(is_rtl())
			frappe.local.lang = "en"
			self.assertFalse(is_rtl())
		finally:
			frappe.local.lang = original
