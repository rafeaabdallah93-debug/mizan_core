"""Mizan branding. Applied on install and on every migrate (idempotent)."""

import frappe

BRAND_NAME_EN = "Mizan"
BRAND_NAME_AR = "ميزان"
BRAND_COLOR = "#1F4E79"
LOGO_URL = "/assets/mizan_core/images/logo.svg"
FAVICON_URL = LOGO_URL

# Public workspaces ERPNext ships with its name in the label, and the label Mizan shows instead
# (translated through Frappe's catalog, e.g. "Settings" -> "الإعدادات"). Only label and title
# change: the record name stays, so ERPNext's own workspace sync keeps matching it.
WORKSPACE_LABELS = {"ERPNext Settings": "Settings"}


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

	# Frappe appends the "default_mail_footer" hook ("Sent via ERPNext") to every email unless
	# this is set. email_body.get_footer() reads it from the defaults, which a plain
	# set_single_value does not update, so both are written.
	frappe.db.set_single_value("System Settings", "disable_standard_email_footer", 1)
	frappe.db.set_default("disable_standard_email_footer", 1)

	relabel_erpnext_workspaces()
	frappe.clear_cache()


def relabel_erpnext_workspaces() -> None:
	"""Give ERPNext's public workspaces a label without the ERPNext name.

	Runs from after_migrate, which Frappe calls after the model sync that imports the app
	workspaces, so a label ERPNext re-imports on an update is replaced again. Written with
	db.set_value: standard workspaces cannot be saved from the site outside developer mode.
	"""
	for workspace in frappe.get_all(
		"Workspace", filters={"public": 1, "for_user": ("in", ("", None))}, fields=["name", "label", "title"]
	):
		changes = {}
		for field in ("label", "title"):
			value = workspace.get(field)
			if _is_erpnext(value):
				changes[field] = WORKSPACE_LABELS.get(value) or _without_erpnext(value)
		if changes:
			frappe.db.set_value("Workspace", workspace.name, changes, update_modified=False)


def _without_erpnext(value: str) -> str:
	import re

	return re.sub(r"\s*erpnext\s*", " ", value, flags=re.IGNORECASE).strip() or BRAND_NAME_EN


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
