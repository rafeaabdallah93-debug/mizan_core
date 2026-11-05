"""bench commands for mizan_core (loaded by frappe.utils.bench_helper.get_app_commands)."""

import sys

import click
from frappe.commands import get_site, pass_context


@click.command("mizan-provision")
@click.option("--company", required=True, help="Name of the site's one company")
@click.option("--abbr", required=True, help="Company abbreviation, e.g. MZN")
@click.option("--language", default="en", show_default=True, help="Default language: en or ar")
@pass_context
def mizan_provision(context, company, abbr, language):
	"""Set up a new site: one company with Egyptian defaults; the setup wizard is skipped."""
	import frappe
	from frappe.utils import strip_html

	from mizan_core.setup.provision import provision_site

	site = get_site(context)
	frappe.init(site)
	frappe.connect()
	try:
		try:
			provision_site(company, abbr, language)
		except frappe.ValidationError as e:
			frappe.db.rollback()
			click.secho(f"mizan-provision failed on {site}: {strip_html(str(e))}", fg="red", err=True)
			sys.exit(1)
		frappe.db.commit()
		click.echo(f"Provisioned {site}: company {company!r}, language {language}.")
	finally:
		frappe.destroy()


commands = [mizan_provision]
