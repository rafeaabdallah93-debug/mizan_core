import frappe
from frappe.tests import IntegrationTestCase

from mizan_core.setup.egypt_defaults import (
	EGYPT_VAT_RATE,
	TAX_TEMPLATE_TITLE,
	apply_egypt_defaults,
)

TEST_COMPANY = "Mizan Test Co"
TEST_ABBR = "MTC"
TEMPLATE_DOCTYPES = ("Sales Taxes and Charges Template", "Purchase Taxes and Charges Template")


class TestEgyptDefaults(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		# Rerunnable: works whether or not an earlier run left the company behind.
		apply_egypt_defaults(TEST_COMPANY, abbr=TEST_ABBR)

	def test_company_currency_is_egp(self):
		company = frappe.db.get_value("Company", TEST_COMPANY, ["country", "default_currency"], as_dict=True)
		self.assertEqual(company.default_currency, "EGP")
		self.assertEqual(company.country, "Egypt")
		self.assertEqual(frappe.db.get_single_value("System Settings", "time_zone"), "Africa/Cairo")

	def test_vat_template_uses_constant(self):
		for doctype in TEMPLATE_DOCTYPES:
			name = frappe.db.get_value(doctype, {"title": TAX_TEMPLATE_TITLE, "company": TEST_COMPANY})
			self.assertTrue(name, f"{doctype} '{TAX_TEMPLATE_TITLE}' missing")
			taxes = frappe.get_doc(doctype, name).taxes
			self.assertEqual(len(taxes), 1)
			self.assertEqual(taxes[0].rate, EGYPT_VAT_RATE)
			account_type = frappe.db.get_value("Account", taxes[0].account_head, "account_type")
			self.assertEqual(account_type, "Tax")

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
		def snapshot():
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

		before = snapshot()
		apply_egypt_defaults(TEST_COMPANY, abbr=TEST_ABBR)
		self.assertEqual(snapshot(), before)
