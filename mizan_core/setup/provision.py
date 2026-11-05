"""Provision a customer site: ONE company with Egyptian defaults, and ERPNext's setup wizard
marked as done so that it never appears.

The setup wizard must not run on a Mizan site: finishing it creates a second company with
ERPNext's "Egypt Tax" / "GST 10%" placeholder. provision_site() does what the wizard does
instead (Frappe 16 frappe/desk/page/setup_wizard/setup_wizard.py and ERPNext 16
erpnext/setup/setup_wizard/), with apply_egypt_defaults() in place of the wizard's company step.

Command line (non-interactive, used by packaging):

    bench --site <site> mizan-provision --company "<name>" --abbr <ABBR> [--language ar|en]   (default ar)

provision_site() is safe to call repeatedly with the same arguments. It does not commit; the
bench command commits.
"""

import frappe
from frappe import _

from mizan_core.setup.egypt_defaults import (
	EGYPT_COUNTRY,
	EGYPT_CURRENCY,
	EGYPT_TIME_ZONE,
	apply_egypt_defaults,
)
from mizan_core.setup.languages import SUPPORTED_LANGUAGES

# Apps whose Installed Application.is_setup_complete flags frappe.is_setup_complete() reads.
SETUP_WIZARD_APPS = ("frappe", "erpnext")
# Default desk home page while the wizard is pending; the wizard sets "workspace" when done.
WIZARD_HOME_PAGE = "setup-wizard"
HOME_PAGE_AFTER_SETUP = "workspace"


def provision_site(company: str, abbr: str, language: str = "ar") -> None:
	"""Set this site up with `company` as its only company, Egyptian defaults and `language`
	("ar", the default, or "en") as the default language, and mark the setup wizard complete.

	Refuses (before changing anything) if the site has any other company, or if `language` is
	not supported.
	"""
	company = (company or "").strip()
	if not company:
		frappe.throw(_("A company name is required."))
	if language not in SUPPORTED_LANGUAGES:
		frappe.throw(
			_("Language must be one of {0}, not {1}.").format(", ".join(SUPPORTED_LANGUAGES), repr(language))
		)
	others = [name for name in _existing_companies() if name != company]
	if others:
		frappe.throw(
			_(
				"This site already has another company ({0}). Mizan uses one company per site; "
				"provision a new site for {1}."
			).format(", ".join(others), company)
		)
	existing_abbr = frappe.db.get_value("Company", company, "abbr")
	if existing_abbr and existing_abbr != abbr:
		frappe.throw(
			_("Company {0} already exists with abbreviation {1}, not {2}.").format(
				company, existing_abbr, abbr
			)
		)

	first_run = not frappe.is_setup_complete()
	if first_run and not frappe.db.count("Company"):
		# Wizard stage "Setting up the basics", as on a fresh site: ERPNext's master records.
		# Only on a site with no company, where none of them exist yet (re-inserting into
		# existing trees logs errors); apply_egypt_defaults fills in any that are missing.
		from erpnext.setup.setup_wizard.operations import install_fixtures

		install_fixtures.install(EGYPT_COUNTRY)

	apply_egypt_defaults(company, abbr)

	if first_run:
		_apply_wizard_settings()
	_set_language(language)
	if not frappe.db.get_value("Currency", EGYPT_CURRENCY, "enabled"):
		frappe.db.set_value("Currency", EGYPT_CURRENCY, "enabled", 1)
	_mark_setup_complete()


def _existing_companies() -> list[str]:
	return frappe.get_all("Company", pluck="name")


def _apply_wizard_settings() -> None:
	"""The settings the wizard writes besides the company, applied once (first provisioning
	only, so later changes by the admin are kept)."""
	from erpnext.setup.setup_wizard.operations import (
		install_fixtures as erpnext_fixtures,
	)
	from frappe.desk.page.setup_wizard import install_fixtures as frappe_fixtures
	from frappe.desk.page.setup_wizard.setup_wizard import update_system_settings

	# Frappe stage (update_global_settings): System Settings for the country. The language is
	# set afterwards from provision_site's argument.
	update_system_settings(
		frappe._dict(country=EGYPT_COUNTRY, currency=EGYPT_CURRENCY, timezone=EGYPT_TIME_ZONE)
	)
	frappe.db.set_value("User", {"name": ("in", frappe.STANDARD_USERS)}, "time_zone", EGYPT_TIME_ZONE)

	# ERPNext stage "Applying recommended settings" (install_defaults) minus what
	# apply_egypt_defaults already did (price lists, global defaults), the optional bank account,
	# and Stock Settings.email_footer_address (a field Stock Settings no longer has in v16).
	# EGP is enabled by provision_site on every run.
	erpnext_fixtures.update_stock_settings()
	erpnext_fixtures.update_selling_defaults()
	erpnext_fixtures.update_buying_defaults()

	# Frappe's run_setup_success: genders, salutations, global search, dashboards.
	frappe_fixtures.install()

	# The wizard's telemetry checkbox (apply_telemetry_preference): Mizan sites opt out.
	frappe.db.set_single_value("System Settings", "enable_telemetry", 0)


def _set_language(language: str) -> None:
	settings = frappe.get_single("System Settings")
	if settings.language != language:
		settings.language = language
		settings.save(ignore_permissions=True)  # on_update sets the "lang" default
	if frappe.db.get_default("lang") != language:
		from frappe.translate import set_default_language

		set_default_language(language)


def _mark_setup_complete() -> None:
	"""What the wizard does when it finishes: per-app flags (enable_setup_wizard_complete),
	then disable_future_access(): desk home page, onboarding, System Settings.setup_complete."""
	changed = False
	for app in SETUP_WIZARD_APPS:
		if not frappe.db.get_value("Installed Application", {"app_name": app}, "is_setup_complete"):
			frappe.db.set_value("Installed Application", {"app_name": app}, "is_setup_complete", 1)
			changed = True

	home_page = frappe.db.get_default("desktop:home_page")
	if not home_page or home_page == WIZARD_HOME_PAGE:
		frappe.db.set_default("desktop:home_page", HOME_PAGE_AFTER_SETUP)
		frappe.db.set_single_value("System Settings", "enable_onboarding", 1)
		changed = True

	if not frappe.db.get_single_value("System Settings", "setup_complete"):
		frappe.db.set_single_value("System Settings", "setup_complete", 1)
		changed = True

	if changed:
		frappe.clear_cache()
