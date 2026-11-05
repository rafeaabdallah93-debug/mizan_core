# Egyptian chart of accounts: UNVERIFIED DRAFT

**Status: UNVERIFIED.** `egypt_chart_of_accounts.csv` is a draft for a small Egyptian retail
shop, taken from a research briefing built on secondary sources. No Egyptian accountant has
reviewed it. The 14% VAT rate (`EGYPT_VAT_RATE` in `mizan_core/setup/egypt_defaults.py`) is
also unverified. Do not use either on a live company until an accountant confirms them.

Why the marker is here and not in the CSV: ERPNext's Chart of Accounts Importer rejects any
row that does not have exactly 8 columns, and treats the first row as the header, so the CSV
cannot carry a comment or marker row. The marker is kept in this file and in the
`CHART_OF_ACCOUNTS_STATUS` constant in `egypt_defaults.py`.

## Files

- `egypt_chart_of_accounts.csv`: the chart in the importer's own template format
  (Account Name, Parent Account, Account Number, Parent Account Number, Is Group,
  Account Type, Root Type, Account Currency). Account names are English. Account Currency is
  left blank so accounts take the company currency (EGP).
- `egypt_chart_of_accounts_ar.csv`: Arabic name for every account, by account number. The
  importer has no column for a second name, so the Arabic is kept here.

## Changes from the research draft

- Names shortened and hyphens removed (ERPNext builds account IDs as
  `number - name - abbreviation`).
- "Cost of Sales" (5000) and "Operating Expenses" (6000) are two separate expense roots.
- Added because ERPNext needs them for a working company: 1900 Temporary Opening,
  2110 Stock Received But Not Billed, 2120 Asset Received But Not Billed,
  5300 Expenses Included In Valuation, 6910 Write Off, 6920 Exchange Gain/Loss,
  6930 Round Off. Their Arabic names were written by us, not taken from the briefing.

## Accountant review checklist

1. Confirm the standard VAT rate (14%) and the accounts used: sales VAT posts to
   2200 Output VAT Payable, purchase VAT to 1500 Input VAT Recoverable.
2. Correct codes, English names and Arabic wording; add missing accounts (stamp duty,
   social insurance detail, Table Tax by rate).
3. Then remove the UNVERIFIED markers here, in `CHART_OF_ACCOUNTS_STATUS` and on
   `EGYPT_VAT_RATE`.
