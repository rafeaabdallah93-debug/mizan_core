"""Egyptian defaults for a company: country, currency, time zone, fiscal year, chart of accounts
and VAT.

apply_egypt_defaults() is safe to call repeatedly: on a configured company it changes nothing.

Chart of accounts: the first call imports the Egyptian chart into a company that has no accounts,
or that still has only the chart ERPNext created for it (Standard template, no GL entries) - in
that case ERPNext's default chart is REPLACED. A company that already has the Egyptian chart is
never re-imported. A company with any other (custom) chart is refused with an error rather than
wiped.

ERPNext ships a placeholder for Egypt in setup/setup_wizard/data/country_wise_tax.json
("Egypt Tax" templates on a "GST" account at 10%). It is applied by
Company.create_default_tax_template(), which runs from Company.on_update() (new company with
no accounts, or a country change) and at the end of the Chart of Accounts Importer's
import_coa(). This module avoids both paths (see _create_company and _import_chart) and
removes the placeholder if it was created some other way (for example a country change on an
existing company).
"""

import csv
import os

import frappe
from frappe import _
from frappe.utils import cint, flt, getdate, nowdate

# UNVERIFIED: 14% from secondary sources only (see data/README.md). An Egyptian accountant
# must confirm before go-live.
EGYPT_VAT_RATE = 14.0  # UNVERIFIED
# Retail shelf prices in Egypt include VAT: the SALES template is tax-inclusive
# (included_in_print_rate). The purchase template stays exclusive.
PRICES_INCLUDE_VAT = True  # UNVERIFIED (accountant to confirm)
TAX_TEMPLATE_TITLE = "Egypt VAT"

EGYPT_COUNTRY = "Egypt"
EGYPT_CURRENCY = "EGP"
EGYPT_TIME_ZONE = "Africa/Cairo"

# UNVERIFIED draft chart. The ERPNext importer takes exactly 8 columns and no comment rows,
# so the UNVERIFIED marker lives here and in data/README.md instead of inside the CSV.
CHART_OF_ACCOUNTS_STATUS = "UNVERIFIED DRAFT - awaiting review by an Egyptian accountant"
_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
CHART_OF_ACCOUNTS_CSV = os.path.join(_DATA_DIR, "egypt_chart_of_accounts.csv")
# Arabic names by account number (the importer has no column for them).
CHART_OF_ACCOUNTS_AR_CSV = os.path.join(_DATA_DIR, "egypt_chart_of_accounts_ar.csv")

# Account numbers in the chart CSV that the defaults below depend on.
SALES_VAT_ACCOUNT_NUMBER = "2200"  # Output VAT Payable
PURCHASE_VAT_ACCOUNT_NUMBER = "1500"  # Input VAT Recoverable

SALES_TEMPLATE = "Sales Taxes and Charges Template"
PURCHASE_TEMPLATE = "Purchase Taxes and Charges Template"
# Transactions whose `taxes_and_charges` links to each template type.
TEMPLATE_TRANSACTIONS = {
	SALES_TEMPLATE: ("Quotation", "Sales Order", "Delivery Note", "Sales Invoice", "POS Invoice"),
	PURCHASE_TEMPLATE: ("Supplier Quotation", "Purchase Order", "Purchase Receipt", "Purchase Invoice"),
}

# ERPNext's placeholder from country_wise_tax.json for Egypt, and the group
# taxes_setup.get_or_create_tax_group() creates for it when the chart has no Tax group.
PLACEHOLDER_TEMPLATE_TITLE = "Egypt Tax"
PLACEHOLDER_ACCOUNT_NAME = "GST"
PLACEHOLDER_RATE = 10.0
PLACEHOLDER_GROUP_NAME = "Duties and Taxes"

# Company default-account fields filled from the chart, by account type (lowest number wins).
DEFAULT_ACCOUNTS_BY_TYPE = {
	"default_receivable_account": "Receivable",
	"default_payable_account": "Payable",
	"default_cash_account": "Cash",
	"default_bank_account": "Bank",
	"round_off_account": "Round Off",
	"accumulated_depreciation_account": "Accumulated Depreciation",
	"depreciation_expense_account": "Depreciation",
	"asset_received_but_not_billed": "Asset Received But Not Billed",
	"default_expense_account": "Cost of Goods Sold",
	"default_income_account": "Income Account",
	"stock_received_but_not_billed": "Stock Received But Not Billed",
	"default_inventory_account": "Stock",
	"stock_adjustment_account": "Stock Adjustment",
}
# Fields ERPNext itself fills by account name (Company.set_default_accounts).
DEFAULT_ACCOUNTS_BY_NAME = {
	"write_off_account": "Write Off",
	"exchange_gain_loss_account": "Exchange Gain/Loss",
}


def apply_egypt_defaults(company: str, abbr: str | None = None) -> None:
	"""Create or update `company` with Egyptian defaults. Safe to call repeatedly.

	`abbr` is only used when the company does not exist yet (default: initials of the name).
	"""
	if frappe.db.exists("Company", company):
		# Refuse before changing anything: a custom chart is never replaced.
		if not _chart_present(company) and not _company_has_replaceable_chart(company):
			frappe.throw(
				_(
					"Company {0} already has its own chart of accounts (or ledger entries). Mizan will "
					"not replace it; import the Egyptian chart manually or use a new company."
				).format(frappe.bold(company))
			)
		_update_company(company)
	else:
		_create_company(company, abbr or _initials(company))

	_remove_placeholder_tax(company)
	if not _chart_present(company):
		_import_chart(company)
	_set_default_accounts(company)
	_ensure_vat_templates(company)
	_ensure_fiscal_year(company)
	_set_time_zone()


def _initials(name: str) -> str:
	return "".join(word[0] for word in name.split()).upper()


def _create_company(company: str, abbr: str) -> None:
	# With ignore_chart_of_accounts, Company.on_update() does not create the standard chart and
	# does not set frappe.flags.country_change, so install_country_fixtures() and
	# create_default_tax_template() (the GST placeholder) are skipped for the new company.
	previous = frappe.local.flags.ignore_chart_of_accounts
	frappe.local.flags.ignore_chart_of_accounts = True
	try:
		frappe.get_doc(
			{
				"doctype": "Company",
				"company_name": company,
				"abbr": abbr,
				"country": EGYPT_COUNTRY,
				"default_currency": EGYPT_CURRENCY,
			}
		).insert(ignore_permissions=True)
	finally:
		frappe.local.flags.ignore_chart_of_accounts = previous


def _update_company(company: str) -> None:
	doc = frappe.get_doc("Company", company)
	if doc.country == EGYPT_COUNTRY and doc.default_currency == EGYPT_CURRENCY:
		return
	doc.country = EGYPT_COUNTRY
	doc.default_currency = EGYPT_CURRENCY
	# A country change makes Company.on_update() seed the placeholder; it is removed next.
	doc.save(ignore_permissions=True)


# --- ERPNext placeholder ------------------------------------------------------------------


def _is_placeholder_template(doctype: str, name: str) -> bool:
	"""True only for ERPNext's seeded template: a single row at the placeholder 10% rate."""
	rows = frappe.get_doc(doctype, name).taxes
	rate_field = "tax_rate" if doctype == "Item Tax Template" else "rate"
	return len(rows) == 1 and flt(rows[0].get(rate_field)) == PLACEHOLDER_RATE


def _remove_placeholder_tax(company: str) -> None:
	for doctype in (SALES_TEMPLATE, PURCHASE_TEMPLATE, "Item Tax Template"):
		for name in frappe.get_all(
			doctype, filters={"company": company, "title": PLACEHOLDER_TEMPLATE_TITLE}, pluck="name"
		):
			if _is_placeholder_template(doctype, name):
				frappe.delete_doc(doctype, name, ignore_permissions=True)

	for name in frappe.get_all(
		"Account",
		filters={
			"company": company,
			"account_name": PLACEHOLDER_ACCOUNT_NAME,
			"account_type": "Tax",
			"is_group": 0,
		},
		pluck="name",
	):
		if frappe.db.exists("GL Entry", {"account": name}):
			continue  # used in the books: leave it for the accountant
		try:
			frappe.delete_doc("Account", name, ignore_permissions=True)
		except frappe.LinkExistsError:
			pass  # still referenced (e.g. a user-edited template): leave it

	# Our chart has no "Duties and Taxes" group; if ERPNext added one for the placeholder, drop it.
	if _chart_present(company):
		for name in frappe.get_all(
			"Account",
			filters={"company": company, "account_name": PLACEHOLDER_GROUP_NAME, "is_group": 1},
			pluck="name",
		):
			if not frappe.db.exists("Account", {"parent_account": name}):
				frappe.delete_doc("Account", name, ignore_permissions=True)


# --- Chart of accounts --------------------------------------------------------------------


def _chart_rows() -> list[list[str]]:
	with open(CHART_OF_ACCOUNTS_CSV, encoding="utf-8") as f:
		return list(csv.reader(f))[1:]


def _chart_present(company: str) -> bool:
	"""True when most of the chart's (number, name) pairs exist for the company.

	Pairs, not numbers alone: ERPNext's "Standard with Numbers" chart reuses numbers such as
	1100, 1300 and 2100. A majority, not one account: a renamed or renumbered account must not
	make the chart look absent (that would trigger a destructive re-import).
	"""
	wanted = {(row[2].strip(), row[0].strip().lower()) for row in _chart_rows()}
	existing = frappe.get_all(
		"Account",
		filters={"company": company, "account_number": ("in", [number for number, _name in wanted])},
		fields=["account_number", "account_name"],
	)
	found = {(a.account_number, (a.account_name or "").strip().lower()) for a in existing} & wanted
	return len(found) * 2 > len(wanted)


def _chart_account_names(tree: dict, metadata: set) -> set:
	names = set()
	for key, value in tree.items():
		if key not in metadata and isinstance(value, dict):
			names.add(key.strip().lower())
			names |= _chart_account_names(value, metadata)
	return names


def _company_has_replaceable_chart(company: str) -> bool:
	"""No accounts at all, or only the standard chart ERPNext created, and no GL entries."""
	accounts = frappe.get_all("Account", filters={"company": company}, pluck="account_name")
	if not accounts:
		return True
	if frappe.db.exists("GL Entry", {"company": company}):
		return False

	from erpnext.accounts.doctype.account.chart_of_accounts.chart_of_accounts import (
		get_chart,
		get_chart_metadata_fields,
	)

	based_on, chart_name = frappe.db.get_value(
		"Company", company, ["create_chart_of_accounts_based_on", "chart_of_accounts"]
	)
	if based_on != "Standard Template" or not chart_name:
		return False
	tree = get_chart(chart_name) or {}
	standard_names = _chart_account_names(tree, set(get_chart_metadata_fields()))
	# ERPNext may have added its Egypt placeholder account to that chart.
	standard_names |= {PLACEHOLDER_ACCOUNT_NAME.lower(), PLACEHOLDER_GROUP_NAME.lower()}
	return bool(standard_names) and {a.strip().lower() for a in accounts} <= standard_names


class _AppFile:
	"""Stands in for a File document: the importer's CSV reader only calls get_full_path()."""

	def __init__(self, path: str):
		self.path = path

	def get_full_path(self) -> str:
		return self.path


def _import_chart(company: str) -> None:
	"""Import the chart with the Chart of Accounts Importer's own parser, validators and loader.

	This is import_coa() without its last step: import_coa() ends with
	set_default_accounts() -> Company.create_default_tax_template(), which seeds the GST
	placeholder. import_coa() also needs an uploaded File record; the app's CSV is read directly.
	Only called when _company_has_replaceable_chart() allows it.
	"""
	from erpnext.accounts.doctype.account.chart_of_accounts.chart_of_accounts import create_charts
	from erpnext.accounts.doctype.chart_of_accounts_importer.chart_of_accounts_importer import (
		build_forest,
		generate_data_from_csv,
		unset_existing_data,
		validate_accounts,
		validate_columns,
		validate_company,
	)
	from erpnext.accounts.doctype.financial_report_template.financial_report_template import (
		sync_financial_report_templates,
	)

	file_doc = _AppFile(CHART_OF_ACCOUNTS_CSV)
	data = generate_data_from_csv(file_doc)
	validate_columns(data)
	validate_accounts(file_doc, "csv")  # root types and mandatory account types
	forest = build_forest(data)

	validate_company(company)  # refuses a company that already has GL entries
	unset_existing_data(company)  # removes ERPNext's default chart and its tax templates

	previous = frappe.local.flags.ignore_root_company_validation
	frappe.local.flags.ignore_root_company_validation = True
	try:
		create_charts(company, custom_chart=forest, from_coa_importer=True)
	finally:
		if previous is None:
			frappe.local.flags.pop("ignore_root_company_validation", None)
		else:
			frappe.local.flags.ignore_root_company_validation = previous
	# Company.on_update() normally does these with the chart; they were skipped on creation.
	sync_financial_report_templates()
	frappe.get_doc("Company", company).create_default_warehouses()


def _set_default_accounts(company: str) -> None:
	"""Fill empty company default-account fields from the chart. Never overwrites a value."""
	doc = frappe.get_doc("Company", company)
	updates = {}
	for fieldname, account_type in DEFAULT_ACCOUNTS_BY_TYPE.items():
		if not doc.get(fieldname):
			updates[fieldname] = frappe.db.get_value(
				"Account",
				{"company": company, "account_type": account_type, "is_group": 0},
				order_by="account_number asc",
			)
	for fieldname, account_name in DEFAULT_ACCOUNTS_BY_NAME.items():
		if not doc.get(fieldname):
			updates[fieldname] = frappe.db.get_value(
				"Account", {"company": company, "account_name": account_name, "is_group": 0}
			)
	updates = {key: value for key, value in updates.items() if value}
	if updates:
		doc.db_set(updates)

	if doc.default_cash_account:
		doc.set_mode_of_payment_account()  # no-op when the Cash mode already has this company


# --- VAT templates ------------------------------------------------------------------------


def _vat_account(company: str, account_number: str) -> str:
	account = frappe.db.get_value(
		"Account",
		{"company": company, "account_number": account_number, "account_type": "Tax", "is_group": 0},
	)
	if not account:
		frappe.throw(
			_("VAT account {0} from the Egyptian chart is missing for company {1}").format(
				account_number, company
			)
		)
	return account


def _wanted_vat_row(doctype: str) -> dict:
	row = {"rate": EGYPT_VAT_RATE, "description": f"VAT @ {EGYPT_VAT_RATE}%"}
	if doctype == SALES_TEMPLATE:
		row["included_in_print_rate"] = cint(PRICES_INCLUDE_VAT)
	return row


def _template_used(doctype: str, name: str) -> bool:
	return any(frappe.db.exists(txn, {"taxes_and_charges": name}) for txn in TEMPLATE_TRANSACTIONS[doctype])


def _ensure_vat_templates(company: str) -> None:
	cost_center = frappe.get_cached_value("Company", company, "cost_center")
	for doctype, account_number in (
		(SALES_TEMPLATE, SALES_VAT_ACCOUNT_NUMBER),
		(PURCHASE_TEMPLATE, PURCHASE_VAT_ACCOUNT_NUMBER),
	):
		account = _vat_account(company, account_number)
		name = frappe.db.get_value(doctype, {"company": company, "title": TAX_TEMPLATE_TITLE})
		if name:
			_sync_vat_template(doctype, name, account)
			continue
		row = {
			"category": "Total",
			"charge_type": "On Net Total",
			"account_head": account,
			"cost_center": cost_center,
			**_wanted_vat_row(doctype),
		}
		if doctype == PURCHASE_TEMPLATE:
			row["add_deduct_tax"] = "Add"
		frappe.get_doc(
			{
				"doctype": doctype,
				"title": TAX_TEMPLATE_TITLE,
				"company": company,
				"is_default": 1,
				"taxes": [row],
			}
		).insert(ignore_permissions=True)


def _sync_vat_template(doctype: str, name: str, account: str) -> None:
	"""Bring an existing "Egypt VAT" template's VAT row in line with the constants.

	Unused templates are updated in place. A template already used by a transaction is never
	edited (history must not change): the admin is told to create a new template instead.
	"""
	doc = frappe.get_doc(doctype, name)
	rows = [row for row in doc.taxes if row.account_head == account]
	if len(rows) != 1:
		frappe.throw(
			_("Tax template {0} must have exactly one row on VAT account {1}.").format(
				frappe.bold(name), frappe.bold(account)
			)
		)
	row = rows[0]
	wanted = _wanted_vat_row(doctype)
	changed = flt(row.rate) != flt(wanted["rate"]) or (
		"included_in_print_rate" in wanted
		and cint(row.included_in_print_rate) != wanted["included_in_print_rate"]
	)
	if not changed:
		return
	if _template_used(doctype, name):
		frappe.throw(
			_(
				"Tax template {0} has a VAT rate or price-inclusion setting that differs from Mizan's "
				"Egyptian defaults (VAT {1}%, prices include VAT: {2}), but it is already used in "
				"transactions, so it will not be edited. Create a new tax template with the new "
				"settings, make it the default, and disable {0}."
			).format(frappe.bold(name), EGYPT_VAT_RATE, PRICES_INCLUDE_VAT)
		)
	row.update(wanted)
	doc.save(ignore_permissions=True)


# --- Fiscal year and system settings -------------------------------------------------------


def _fiscal_year_for(company: str, date) -> str | None:
	"""An enabled Fiscal Year covering `date` that applies to `company` (global or listed)."""
	candidates = frappe.get_all(
		"Fiscal Year",
		filters={"disabled": 0, "year_start_date": ("<=", date), "year_end_date": (">=", date)},
		pluck="name",
	)
	for name in candidates:
		companies = frappe.get_all("Fiscal Year Company", filters={"parent": name}, pluck="company")
		if not companies or company in companies:
			return name
	return None


def _ensure_fiscal_year(company: str) -> None:
	"""Make sure a fiscal year (1 Jan - 31 Dec) covering today exists for the company.

	Created for this company only, so it cannot overlap with other companies' years.
	"""
	today = getdate(nowdate())
	if _fiscal_year_for(company, today):
		return
	year = str(today.year)
	if frappe.db.exists("Fiscal Year", year):
		year = f"{today.year} ({frappe.get_cached_value('Company', company, 'abbr')})"
	frappe.get_doc(
		{
			"doctype": "Fiscal Year",
			"year": year,
			"year_start_date": f"{today.year}-01-01",
			"year_end_date": f"{today.year}-12-31",
			"companies": [{"company": company}],
		}
	).insert(ignore_permissions=True)
	frappe.cache().delete_key("fiscal_years")


def _set_time_zone() -> None:
	if frappe.db.get_single_value("System Settings", "time_zone") != EGYPT_TIME_ZONE:
		settings = frappe.get_single("System Settings")
		settings.time_zone = EGYPT_TIME_ZONE
		settings.save(ignore_permissions=True)
