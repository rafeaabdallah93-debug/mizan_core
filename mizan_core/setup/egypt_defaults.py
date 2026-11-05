"""Egyptian defaults for a company: country, currency, time zone, chart of accounts and VAT.

apply_egypt_defaults() is idempotent: calling it again on a configured company changes nothing.

ERPNext ships a placeholder for Egypt in setup/setup_wizard/data/country_wise_tax.json
("Egypt Tax" templates on a "GST" account at 10%). It is applied by
Company.create_default_tax_template(), which runs from Company.on_update() (new company with
no accounts, or a country change) and at the end of the Chart of Accounts Importer's
import_coa(). This module avoids both paths (see _create_company and _import_chart) and
removes the placeholder if it was created some other way (for example a country change on an
existing company).
"""

import os

import frappe
from frappe import _

# UNVERIFIED: 14% from secondary sources only (see data/README.md). An Egyptian accountant
# must confirm before go-live.
EGYPT_VAT_RATE = 14.0  # UNVERIFIED
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
CHART_MARKER_ACCOUNT_NUMBER = "1100"  # Cash on Hand; its presence means the chart is imported
SALES_VAT_ACCOUNT_NUMBER = "2200"  # Output VAT Payable
PURCHASE_VAT_ACCOUNT_NUMBER = "1500"  # Input VAT Recoverable

# ERPNext's placeholder from country_wise_tax.json for Egypt, and the group
# taxes_setup.get_or_create_tax_group() creates for it when the chart has no Tax group.
PLACEHOLDER_TEMPLATE_TITLE = "Egypt Tax"
PLACEHOLDER_ACCOUNT_NAME = "GST"
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
		_update_company(company)
	else:
		_create_company(company, abbr or _initials(company))

	_remove_placeholder_tax(company)
	if not _chart_imported(company):
		_import_chart(company)
	_set_default_accounts(company)
	_create_vat_templates(company)
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


def _remove_placeholder_tax(company: str) -> None:
	for doctype in (
		"Sales Taxes and Charges Template",
		"Purchase Taxes and Charges Template",
		"Item Tax Template",
	):
		for name in frappe.get_all(
			doctype, filters={"company": company, "title": PLACEHOLDER_TEMPLATE_TITLE}, pluck="name"
		):
			frappe.delete_doc(doctype, name, ignore_permissions=True)

	for name in frappe.get_all(
		"Account",
		filters={"company": company, "account_name": PLACEHOLDER_ACCOUNT_NAME, "is_group": 0},
		pluck="name",
	):
		if frappe.db.exists("GL Entry", {"account": name}):
			frappe.throw(_("Cannot remove placeholder tax account {0}: it has ledger entries.").format(name))
		frappe.delete_doc("Account", name, ignore_permissions=True)

	# Our chart has no "Duties and Taxes" group; if ERPNext added one for the placeholder, drop it.
	if _chart_imported(company):
		for name in frappe.get_all(
			"Account",
			filters={"company": company, "account_name": PLACEHOLDER_GROUP_NAME, "is_group": 1},
			pluck="name",
		):
			if not frappe.db.exists("Account", {"parent_account": name}):
				frappe.delete_doc("Account", name, ignore_permissions=True)


def _chart_imported(company: str) -> bool:
	return bool(
		frappe.db.exists("Account", {"company": company, "account_number": CHART_MARKER_ACCOUNT_NUMBER})
	)


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
	unset_existing_data(company)  # removes any previous chart and its tax templates

	frappe.local.flags.ignore_root_company_validation = True
	create_charts(company, custom_chart=forest, from_coa_importer=True)
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


def _create_vat_templates(company: str) -> None:
	cost_center = frappe.get_cached_value("Company", company, "cost_center")
	for doctype, account_number in (
		("Sales Taxes and Charges Template", SALES_VAT_ACCOUNT_NUMBER),
		("Purchase Taxes and Charges Template", PURCHASE_VAT_ACCOUNT_NUMBER),
	):
		if frappe.db.exists(doctype, {"company": company, "title": TAX_TEMPLATE_TITLE}):
			continue
		row = {
			"category": "Total",
			"charge_type": "On Net Total",
			"account_head": _vat_account(company, account_number),
			"description": f"VAT @ {EGYPT_VAT_RATE}%",
			"rate": EGYPT_VAT_RATE,
			"cost_center": cost_center,
		}
		if doctype == "Purchase Taxes and Charges Template":
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


def _set_time_zone() -> None:
	if frappe.db.get_single_value("System Settings", "time_zone") != EGYPT_TIME_ZONE:
		settings = frappe.get_single("System Settings")
		settings.time_zone = EGYPT_TIME_ZONE
		settings.save(ignore_permissions=True)
