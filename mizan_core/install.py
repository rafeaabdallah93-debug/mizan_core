"""Entry points for after_install and after_migrate hooks."""

from mizan_core.branding import apply_branding
from mizan_core.setup.languages import enable_languages


def after_install() -> None:
	apply_branding()
	enable_languages()


def after_migrate() -> None:
	apply_branding()
	enable_languages()
