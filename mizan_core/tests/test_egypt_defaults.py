import frappe
from erpnext.accounts.utils import get_fiscal_year
from frappe.tests import IntegrationTestCase
from frappe.utils import nowdate

from mizan_core.setup.egypt_defaults import (
	EGYPT_VAT_RATE,
	PRICES_INCLUDE_VAT,
	TAX_TEMPLATE_TITLE,
	apply_egypt_defaults,
)

TEST_COMPANY = "Mizan Test Co"
TEST_ABBR = "MTC"
SALES_TEMPLATE = "Sales Taxes and Charges Template"
PURCHASE_TEMPLATE = "Purchase Taxes and Charges Template"
TEMPLATE_DOCTYPES = (SALES_TEMPLATE, PURCHASE_TEMPLATE)
ROW_DOCTYPE = {SALES_TEMPLATE: "Sales Taxes and Charges", PURCHASE_TEMPLATE: "Purchase Taxes and Charges"}


def template_row(doctype, company=TEST_COMPANY):
	name = frappe.db.get_value(doctype, {"title": TAX_TEMPLATE_TITLE, "company": company})
	rows = frappe.get_doc(doctype, name).taxes if name else []
	return name, rows


class TestEgyptDefaults(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		# Registered first so it runs last (LIFO), after the class rollback: drop cached
		# settings/defaults that tests changed only inside the rolled-back transaction.
		cls.addClassCleanup(frappe.clear_cache)
		super().setUpClass()
		# Rerunnable: works whether or not an earlier run left the company behind.
		apply_egypt_defaults(TEST_COMPANY, abbr=TEST_ABBR)

	def snapshot(self):
		return {
			"accounts": frappe.get_all(
				"Account",
				filters={"company": TEST_COMPANY},
				fields=["name", "modified"],
				order_by="name",
			),
			"templates": [
				frappe.get_all(
					doctype,
					filters={"company": TEST_COMPANY},
					fields=["name", "modified"],
					order_by="name",
				)
				for doctype in TEMPLATE_DOCTYPES
			],
			"company_modified": frappe.db.get_value("Company", TEST_COMPANY, "modified"),
		}

	def test_company_currency_is_egp(self):
		company = frappe.db.get_value("Company", TEST_COMPANY, ["country", "default_currency"], as_dict=True)
		self.assertEqual(company.default_currency, "EGP")
		self.assertEqual(company.country, "Egypt")
		self.assertEqual(frappe.db.get_single_value("System Settings", "time_zone"), "Africa/Cairo")

	def test_vat_template_uses_constant(self):
		for doctype in TEMPLATE_DOCTYPES:
			name, taxes = template_row(doctype)
			self.assertTrue(name, f"{doctype} '{TAX_TEMPLATE_TITLE}' missing")
			self.assertEqual(len(taxes), 1)
			self.assertEqual(taxes[0].rate, EGYPT_VAT_RATE)
			account_type = frappe.db.get_value("Account", taxes[0].account_head, "account_type")
			self.assertEqual(account_type, "Tax")

	def test_sales_prices_include_vat_purchase_exclusive(self):
		_name, sales = template_row(SALES_TEMPLATE)
		self.assertEqual(bool(sales[0].included_in_print_rate), PRICES_INCLUDE_VAT)
		_name, purchase = template_row(PURCHASE_TEMPLATE)
		self.assertFalse(purchase[0].included_in_print_rate)

	def test_placeholder_gst_not_created(self):
		# ERPNext's country_wise_tax.json seeds Egypt with an "Egypt Tax" template on a "GST" account.
		self.assertFalse(frappe.db.exists("Account", {"company": TEST_COMPANY, "account_name": "GST"}))
		for doctype in (*TEMPLATE_DOCTYPES, "Item Tax Template"):
			self.assertFalse(frappe.db.exists(doctype, {"title": "Egypt Tax", "company": TEST_COMPANY}))

	def test_chart_has_cash_and_vat_accounts(self):
		def ledgers(**filters):
			return frappe.get_all(
				"Account", filters={"company": TEST_COMPANY, "is_group": 0, **filters}, pluck="name"
			)

		self.assertTrue(ledgers(account_type="Cash"))
		self.assertTrue(ledgers(account_type="Tax", root_type="Liability", account_name=("like", "%VAT%")))
		self.assertTrue(frappe.db.get_value("Company", TEST_COMPANY, "default_cash_account"))

	def test_apply_egypt_defaults_is_idempotent(self):
		before = self.snapshot()
		apply_egypt_defaults(TEST_COMPANY, abbr=TEST_ABBR)
		self.assertEqual(self.snapshot(), before)

	def test_reapply_after_account_renamed_does_not_wipe(self):
		cash = frappe.db.get_value("Account", {"company": TEST_COMPANY, "account_number": "1100"})
		self.assertTrue(cash)
		original = frappe.db.get_value("Account", cash, ["account_number", "account_name"], as_dict=True)
		try:
			frappe.db.set_value("Account", cash, {"account_number": "1199", "account_name": "Main Till"})
			before = self.snapshot()
			apply_egypt_defaults(TEST_COMPANY, abbr=TEST_ABBR)
			self.assertEqual(self.snapshot(), before)
		finally:
			frappe.db.set_value("Account", cash, original)

	def test_changed_rate_reaches_unused_template(self):
		for doctype in TEMPLATE_DOCTYPES:
			_name, rows = template_row(doctype)
			frappe.db.set_value(ROW_DOCTYPE[doctype], rows[0].name, "rate", 10)
		frappe.db.set_value(
			ROW_DOCTYPE[SALES_TEMPLATE],
			template_row(SALES_TEMPLATE)[1][0].name,
			"included_in_print_rate",
			int(not PRICES_INCLUDE_VAT),
		)

		apply_egypt_defaults(TEST_COMPANY, abbr=TEST_ABBR)

		for doctype in TEMPLATE_DOCTYPES:
			_name, rows = template_row(doctype)
			self.assertEqual(rows[0].rate, EGYPT_VAT_RATE)
		self.assertEqual(bool(template_row(SALES_TEMPLATE)[1][0].included_in_print_rate), PRICES_INCLUDE_VAT)

	def test_used_template_is_not_edited(self):
		name, rows = template_row(SALES_TEMPLATE)
		invoice = frappe.get_doc(
			{
				"doctype": "Sales Invoice",
				"name": "MIZAN-TEST-VAT-USED",
				"company": TEST_COMPANY,
				"customer": "Mizan Test Customer",
				"taxes_and_charges": name,
			}
		)
		invoice.db_insert()  # only needs to exist as a reference to the template
		try:
			frappe.db.set_value(ROW_DOCTYPE[SALES_TEMPLATE], rows[0].name, "rate", 10)
			with self.assertRaises(frappe.ValidationError):
				apply_egypt_defaults(TEST_COMPANY, abbr=TEST_ABBR)
			self.assertEqual(template_row(SALES_TEMPLATE)[1][0].rate, 10)
		finally:
			frappe.db.delete("Sales Invoice", {"name": invoice.name})
			frappe.db.set_value(ROW_DOCTYPE[SALES_TEMPLATE], rows[0].name, "rate", EGYPT_VAT_RATE)

	def test_fiscal_year_covers_today(self):
		today = nowdate()
		covering = frappe.get_all(
			"Fiscal Year",
			filters={"year_start_date": ("<=", today), "year_end_date": (">=", today)},
			pluck="name",
		)
		self.addCleanup(frappe.cache().delete_key, "fiscal_years")
		# Simulate a real customer site, which has no fiscal year for today. Raw deletes inside
		# the test transaction; the class rollback restores them.
		for name in covering:
			frappe.db.delete("Fiscal Year Company", {"parent": name})
			frappe.db.delete("Fiscal Year", {"name": name})
		frappe.cache().delete_key("fiscal_years")

		apply_egypt_defaults(TEST_COMPANY, abbr=TEST_ABBR)
		count = frappe.db.count("Fiscal Year")
		apply_egypt_defaults(TEST_COMPANY, abbr=TEST_ABBR)
		self.assertEqual(frappe.db.count("Fiscal Year"), count)

		frappe.cache().delete_key("fiscal_years")
		fiscal_year = get_fiscal_year(today, company=TEST_COMPANY, as_dict=True)
		self.assertEqual(str(fiscal_year.year_start_date)[5:], "01-01")
		self.assertEqual(str(fiscal_year.year_end_date)[5:], "12-31")

	def test_existing_standard_company_is_converted_custom_chart_refused(self):
		company = "Mizan Test Std Co"
		if not frappe.db.exists("Company", company):
			# Plain ERPNext creation: standard chart plus the GST placeholder.
			frappe.get_doc(
				{
					"doctype": "Company",
					"company_name": company,
					"abbr": "MTSC",
					"country": "Egypt",
					"default_currency": "EGP",
				}
			).insert()
		if not frappe.db.exists("Account", {"company": company, "account_number": "2200"}):
			parent = frappe.db.get_value(
				"Account",
				{"company": company, "root_type": "Expense", "parent_account": ("is", "not set")},
			)
			custom = frappe.get_doc(
				{
					"doctype": "Account",
					"account_name": "Mizan Custom Expense",
					"parent_account": parent,
					"company": company,
				}
			).insert()
			count = frappe.db.count("Account", {"company": company})
			with self.assertRaises(frappe.ValidationError):
				apply_egypt_defaults(company)
			self.assertEqual(frappe.db.count("Account", {"company": company}), count)
			frappe.delete_doc("Account", custom.name)

		apply_egypt_defaults(company)
		self.assertTrue(
			frappe.db.exists(
				"Account",
				{"company": company, "account_number": "2200", "account_name": "Output VAT Payable"},
			)
		)
		self.assertFalse(frappe.db.exists("Account", {"company": company, "account_name": "GST"}))
		self.assertFalse(frappe.db.exists(SALES_TEMPLATE, {"company": company, "title": "Egypt Tax"}))

	def test_new_company_without_setup_wizard_records(self):
		# Reproduces a fresh site (setup wizard never ran): no Warehouse Type "Transit", which
		# Company.create_default_warehouses() links to. Raw delete; the class rollback restores it.
		frappe.db.delete("Warehouse Type", {"name": "Transit"})
		company = "Mizan Test Fresh Co"
		apply_egypt_defaults(company, abbr="MTFC")
		self.assertTrue(frappe.db.exists("Warehouse Type", "Transit"))
		self.assertTrue(frappe.db.exists("Warehouse", {"company": company, "warehouse_type": "Transit"}))
		self.assertTrue(frappe.db.get_value("Company", company, "default_cash_account"))

	def test_system_settings_saved_on_bare_site(self):
		# A fresh site (setup wizard never ran): no System Settings language, so saving System
		# Settings failed; no default company and ERPNext's install default currency INR.
		frappe.db.set_single_value("System Settings", {"language": "", "time_zone": "Asia/Kolkata"})
		frappe.db.set_single_value("Global Defaults", {"default_company": "", "default_currency": "INR"})
		apply_egypt_defaults(TEST_COMPANY, abbr=TEST_ABBR)
		self.assertEqual(frappe.db.get_single_value("System Settings", "time_zone"), "Africa/Cairo")
		self.assertTrue(frappe.db.get_single_value("System Settings", "language"))
		self.assertEqual(frappe.db.get_single_value("System Settings", "country"), "Egypt")
		self.assertEqual(frappe.db.get_single_value("Global Defaults", "default_company"), TEST_COMPANY)
		self.assertEqual(frappe.db.get_single_value("Global Defaults", "default_currency"), "EGP")
