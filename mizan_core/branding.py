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


def _is_erpnext(value) -> bool:
	return isinstance(value, str) and "erpnext" in value.lower()


def rewrite_boot_apps(bootinfo) -> None:
	"""boot_session hook: replace ERPNext's name and logo in the desk app list.

	Frappe builds ``bootinfo.app_data`` (sidebar header, app switcher) from each
	installed app's own ``app_title``/``app_logo_url`` hooks. ERPNext's hooks
	cannot be edited, so the entries are rewritten here at boot time.
	"""
	for app in bootinfo.get("app_data") or []:
		if _is_erpnext(app.get("app_title")):
			app["app_title"] = BRAND_NAME_EN
		logo = app.get("app_logo_url")
		logos = logo if isinstance(logo, list | tuple) else [logo]
		if any(_is_erpnext(x) for x in logos):
			app["app_logo_url"] = LOGO_URL
