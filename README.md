# Mizan Core

Frappe app for Mizan, an Egyptian retail ERP built on ERPNext 16. Holds branding, language and Egyptian default settings.

Requires ERPNext 16. License: GPL-3.0 (see `license.txt`).

Arabic translations: `mizan_core/locale/ar.po`. After editing it on a bench, run
`bench compile-po-to-mo --app mizan_core` (the edition image build compiles it itself).

## Tests

    bench --site <site> run-tests --app mizan_core
