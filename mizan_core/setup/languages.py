"""Arabic and English support. Idempotent; runs on install and on every migrate."""

import frappe

SUPPORTED_LANGUAGES = ("ar", "en")


def enable_languages() -> None:
	"""Make sure the Language records for Arabic and English exist and are enabled."""
	for lang in SUPPORTED_LANGUAGES:
		if frappe.db.exists("Language", lang):
			if not frappe.db.get_value("Language", lang, "enabled"):
				frappe.db.set_value("Language", lang, "enabled", 1)
		else:
			frappe.get_doc(
				{
					"doctype": "Language",
					"language_code": lang,
					"language_name": {"ar": "العربية", "en": "English"}[lang],
					"enabled": 1,
				}
			).insert(ignore_permissions=True)
	frappe.clear_cache()
