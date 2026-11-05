"""Mizan branding. Applied on install and on every migrate (idempotent)."""

import frappe

BRAND_NAME_EN = "Mizan"
BRAND_NAME_AR = "ميزان"
BRAND_COLOR = "#1F4E79"
LOGO_URL = "/assets/mizan_core/images/logo.svg"
FAVICON_URL = LOGO_URL


def apply_branding() -> None:
	"""Set app name, logo and favicon so the product never shows ERPNext's brand."""
	frappe.db.set_single_value("System Settings", "app_name", BRAND_NAME_EN)

	website = {
		"app_name": BRAND_NAME_EN,
		"app_logo": LOGO_URL,
		"favicon": FAVICON_URL,
		"splash_image": LOGO_URL,
		"footer_powered": BRAND_NAME_EN,
		"brand_html": f'<img src="{LOGO_URL}" alt="{BRAND_NAME_EN}" style="max-height: 32px;">',
	}
	for field, value in website.items():
		frappe.db.set_single_value("Website Settings", field, value)
	frappe.db.set_single_value("Navbar Settings", "app_logo", LOGO_URL)

	frappe.clear_cache()
