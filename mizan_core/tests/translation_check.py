"""Shared check (also used by mizan_retail): the app's translatable strings, extracted the way
`bench generate-pot-file` does, that have no Arabic translation in <app>/locale/ar.po."""

import os

import frappe

SKIPPED_DIRS = {"tests", "node_modules", "locale", "deploy"}


def app_messages(app: str) -> set[tuple[str, str | None]]:
	from babel.messages.extract import extract_from_dir
	from frappe.gettext.translate import PYTHON_KEYWORDS, get_method_map

	def directory_filter(dirpath) -> bool:
		name = os.path.basename(dirpath)
		return not (name.startswith((".", "_")) or name in SKIPPED_DIRS)

	# The hooks.py (navbar items) extractor imports the hooks module by its path under the bench,
	# which fails for apps mounted outside it (the dev setup); Mizan's hooks have no navbar items.
	method_map = [
		(pattern, method)
		for pattern, method in get_method_map(app) + get_method_map("frappe")
		if not pattern.endswith("hooks.py")
	]
	return {
		(message, context)
		for _file, _line, message, _comments, context in extract_from_dir(
			frappe.get_app_path(app), method_map, directory_filter=directory_filter, keywords=PYTHON_KEYWORDS
		)
		if message
	}


def missing_arabic_translations(app: str) -> list[str]:
	from babel.messages.pofile import read_po

	po_path = frappe.get_app_path(app, "locale", "ar.po")
	if not os.path.exists(po_path):
		return sorted(message for message, _context in app_messages(app))
	with open(po_path, "rb") as f:
		catalog = read_po(f)
	missing = []
	for message, context in app_messages(app):
		entry = catalog.get(message, context) or catalog.get(message)
		if not entry or not entry.string:
			missing.append(message)
	return sorted(missing)
