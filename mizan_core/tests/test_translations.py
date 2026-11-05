"""Every user-facing string of the app has an Arabic translation in locale/ar.po."""

import os

import frappe
from frappe.tests import IntegrationTestCase

from mizan_core.tests.translation_check import missing_arabic_translations


class TestArabicTranslations(IntegrationTestCase):
	def test_every_string_has_arabic(self):
		self.assertEqual(missing_arabic_translations("mizan_core"), [])

	def test_po_file_is_shipped(self):
		self.assertTrue(os.path.exists(frappe.get_app_path("mizan_core", "locale", "ar.po")))
