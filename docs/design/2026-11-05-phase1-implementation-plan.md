# Egypt Retail ERP, Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A runnable ERPNext 16 based product with Egyptian defaults, Arabic/English, its own branding, a multi-branch retail setup and optional WooCommerce Fusion, packaged with Docker.

**Architecture:** The ERPNext fork stays on upstream `version-16`. Two new Frappe apps in separate repos sit on top: `egypt_core` (brand, languages, Egyptian defaults) and `egypt_retail` (branch setup). `woocommerce_fusion` is installed unchanged and only for customers with a website. Editions are sets of installed apps.

**Tech Stack:** Frappe 16, ERPNext 16, Python 3.14, MariaDB, Redis, Docker (frappe_docker), GitHub Actions.

**Spec:** `docs/design/2026-11-05-egypt-retail-erp-design.md`

## Global Constraints

- ERPNext and Frappe must be `>=16.0.0,<17.0.0` (required by `woocommerce_fusion`).
- Product code lives only in `egypt_core` and `egypt_retail`; edits to ERPNext files are exceptional and each is listed in `docs/fork-edits.md` of the fork.
- The name "ERPNext" and its logo must not appear in product branding.
- Interface left as ERPNext ships it; no hiding of modules or forms in this phase.
- One company with many branches; multi-company is out of scope.
- Languages: Arabic (`ar`) and English (`en`), switchable per user.
- Egyptian VAT rate and chart of accounts are unverified: values come from one constant each and are marked `# UNVERIFIED` until an accountant confirms them.
- `egypt_core` and `egypt_retail` must not import `woocommerce_fusion`.

## Review Focus

1. Arabic characters in branch, item and customer names must save, display and search correctly.
2. Stock sold or transferred at one branch must never change another branch's quantity.
3. Creating a branch with a name that already exists must fail with a clear message, not create a duplicate.
4. A branch that still holds stock must refuse deletion.
5. Both apps must install and run on a site where `woocommerce_fusion` is absent.

Findings from the code that shape the tasks:
- ERPNext's built-in Egypt tax entry in `erpnext/setup/setup_wizard/data/country_wise_tax.json` is a placeholder (`"GST"`, 10%) and must not be used.
- ERPNext has no Egyptian chart of accounts (`ar_chart_of_accounts.json` is Argentina's).

---

### Task 0: Decide the product name (owner decision, blocks Task 4)

**Files:** none.

- [x] **Step 1:** Product name decided: **Mizan** (Arabic: ميزان, to be confirmed). Still needed from the owner: a logo file (SVG or PNG) and a primary color (hex).
- [ ] **Step 2:** Confirm the name is not "ERPNext" or contains it (see `TRADEMARK_POLICY.md`).

### Task 1: Move the fork to version 16

**Files:**
- Create: `docs/fork-edits.md` (empty list of edits to ERPNext files, with a header)
- Branch: `version-16` in the fork

**Interfaces:**
- Produces: a `version-16` branch whose `erpnext/__init__.py` reports `16.x`, with an `upstream` remote pointing to `https://github.com/frappe/erpnext`.

- [ ] **Step 1:** `git remote add upstream https://github.com/frappe/erpnext`, then `git fetch upstream version-16`.
- [ ] **Step 2:** `git switch -c version-16 upstream/version-16`.
- [x] **Ruling:** the fork's `version-16` branch tracks upstream; customer builds pin the release tag `v16.53.0`, recorded in `docs/fork-edits.md`.
- [ ] **Step 3:** Verify `grep __version__ erpnext/__init__.py` prints a value starting with `16.` and `grep '>=3' pyproject.toml` shows the Python floor.
- [ ] **Step 4:** Add `docs/fork-edits.md`; commit; push `version-16` to `origin` (owner's fork).

### Task 2: Local development environment

**Files:**
- Create (in a new `egypt-erp-dev` folder, not in the fork): `compose.yaml` based on `frappe_docker`, `README.md` with start and stop commands.

**Interfaces:**
- Produces: a site `dev.localhost` on `http://localhost:8080` with `frappe` and `erpnext` 16 installed. Later tasks run `bench --site dev.localhost ...` against it.

- [ ] **Step 1:** Use `frappe_docker`'s published `version-16` images and compose files; do not build ERPNext from the fork yet.
- [ ] **Step 2:** Start the stack and create the site `dev.localhost`, installing `erpnext`.
- [ ] **Step 3:** Verify `curl -s http://localhost:8080/api/method/ping` returns `{"message":"pong"}` and `bench --site dev.localhost list-apps` lists `frappe` and `erpnext` at 16.x.

### Task 3: Scaffold the `egypt_core` app

**Files:**
- Create: new repo `egypt_core` with `egypt_core/hooks.py`, `egypt_core/tests/test_install.py`, `.github/workflows/ci.yml`

**Interfaces:**
- Produces: installable app `egypt_core` declaring `required_apps = ["erpnext"]`.

- [ ] **Step 1: Write the failing test** `test_install.py::test_app_is_installed` asserting `"egypt_core" in frappe.get_installed_apps()`.
- [ ] **Step 2:** Run `bench --site dev.localhost run-tests --app egypt_core`; expect FAIL (app not installed).
- [ ] **Step 3:** `bench new-app egypt_core`, set `required_apps`, then `bench --site dev.localhost install-app egypt_core`.
- [ ] **Step 4:** Rerun the tests; expect PASS.
- [ ] **Step 5:** CI workflow runs the tests on pushes and nightly against upstream `version-16`; commit.

### Task 4: Branding

**Files:**
- Modify: `egypt_core/hooks.py` (`app_title`, `app_logo_url`, `app_color`, `brand_html`)
- Create: `egypt_core/branding.py`, `egypt_core/public/images/logo.svg`, `egypt_core/tests/test_branding.py`

**Interfaces:**
- Consumes: product name, logo and color from Task 0.
- Produces: `BRAND_NAME_EN: str`, `BRAND_NAME_AR: str` in `egypt_core/branding.py`; `apply_branding() -> None`, run on install, which sets System Settings and Website Settings (app name, logo, favicon).

- [ ] **Step 1: Write the failing tests** in `test_branding.py`: `test_app_name_is_brand` asserts `frappe.get_website_settings("app_name") == BRAND_NAME_EN`; `test_no_erpnext_in_brand` asserts `"erpnext" not in BRAND_NAME_EN.lower()` and the same for the Arabic name.
- [ ] **Step 2:** Run; expect FAIL.
- [ ] **Step 3:** Implement `apply_branding()` and call it from `after_install` in `hooks.py`.
- [ ] **Step 4:** Rerun; expect PASS. Check the login page in a browser shows the brand and not ERPNext's logo.
- [ ] **Step 5:** Commit.

### Task 5: Arabic and English

**Files:**
- Create: `egypt_core/setup/languages.py`, `egypt_core/tests/test_languages.py`

**Interfaces:**
- Produces: `enable_languages() -> None`, run on install, enabling Language records `ar` and `en`.

- [ ] **Step 1: Write the failing tests**: `test_ar_and_en_enabled` asserts both Language docs have `enabled == 1`; `test_user_can_switch_language` sets a test user's `language` to `ar`, then `en`, and asserts each save succeeds; `test_arabic_is_rtl` asserts Frappe's own RTL helper (locate it in the installed Frappe source first) returns True for `ar` and False for `en`.
- [ ] **Step 2:** Run; expect FAIL.
- [ ] **Step 3:** Implement `enable_languages()` and call it from `after_install`.
- [ ] **Step 4:** Rerun; expect PASS.
- [ ] **Step 5:** Manual check: switch a user to Arabic, open a Sales Invoice, confirm right-to-left layout and print preview. List any untranslated or wrong strings in `docs/arabic-gaps.md`. Commit.

### Task 6: Egyptian defaults

**Files:**
- Create: `egypt_core/setup/egypt_defaults.py`, `egypt_core/data/egypt_chart_of_accounts.csv`, `egypt_core/tests/test_egypt_defaults.py`

**Interfaces:**
- Produces: `EGYPT_VAT_RATE: float  # UNVERIFIED`, `apply_egypt_defaults(company: str) -> None` which sets country `Egypt`, default currency `EGP`, timezone `Africa/Cairo`, creates a sales and a purchase Tax Template named `Egypt VAT` at `EGYPT_VAT_RATE`, and imports the chart via ERPNext's Chart of Accounts Importer.

- [ ] **Step 1: Write the failing tests**: `test_company_currency_is_egp`; `test_vat_template_uses_constant` asserts the template's rate equals `EGYPT_VAT_RATE`; `test_placeholder_gst_not_created` asserts no tax account named `GST` exists for the company; `test_chart_has_cash_and_vat_accounts` asserts accounts for cash and VAT payable exist.
- [ ] **Step 2:** Run; expect FAIL.
- [ ] **Step 3:** Implement. Until an accountant supplies the chart, the CSV is a minimal draft marked `UNVERIFIED` in its first row.
- [ ] **Step 4:** Rerun; expect PASS.
- [ ] **Step 5:** Owner asks an Egyptian accountant to confirm VAT rate and chart; replace the draft values and remove the `UNVERIFIED` markers. Commit.

### Task 7: Scaffold `egypt_retail` and the branch flow

**Files:**
- Create: new repo `egypt_retail` with `egypt_retail/branches.py`, `egypt_retail/tests/test_branches.py`

**Interfaces:**
- Consumes: a company set up by Task 6.
- Produces:
  - `create_branch(company: str, branch_name: str) -> dict` returning `{"warehouse": str, "pos_profile": str}`; creates one Warehouse and one POS Profile tied to it. Whitelisted for the desk UI.
  - `delete_branch(company: str, branch_name: str) -> None`.

- [ ] **Step 1: Write the failing tests**: `test_create_branch_makes_warehouse_and_pos_profile`; `test_duplicate_branch_name_raises` (expects `frappe.ValidationError`); `test_arabic_branch_name_saves` with a name such as `فرع المعادي`; `test_delete_branch_with_stock_refused`; `test_sale_reduces_only_that_branch_stock` (two branches, same item; a POS sale at branch A leaves B unchanged); `test_transfer_moves_stock_between_branches` (Material Transfer Stock Entry).
- [ ] **Step 2:** Run; expect FAIL.
- [ ] **Step 3:** Implement `create_branch` and `delete_branch`; `required_apps = ["erpnext", "egypt_core"]`.
- [ ] **Step 4:** Rerun; expect PASS.
- [ ] **Step 5:** Add a simple "Add Branch" desk page calling `create_branch`; verify manually. CI as in Task 3; commit.

### Task 8: Optional WooCommerce Fusion

**Files:**
- Create: `docs/woocommerce.md` in `egypt_retail`; `egypt_retail/tests/test_without_woocommerce.py`

**Interfaces:**
- Consumes: `woocommerce_fusion` `version-16` branch from `Starktail/woocommerce_fusion`, installed unchanged.

- [ ] **Step 1: Write the failing test** `test_apps_work_without_woocommerce` asserting `"woocommerce_fusion" not in frappe.get_installed_apps()` on the dev site and that `create_branch` still succeeds.
- [ ] **Step 2:** Run on the dev site without the connector; expect PASS once Task 7 is done, which confirms the apps do not depend on it.
- [ ] **Step 3:** On a second site `shop.localhost`, `bench get-app` the connector at `version-16`, install it, and verify `bench --site shop.localhost list-apps` shows it and the site loads.
- [ ] **Step 4:** Read the connector's settings to find how a WooCommerce site maps to a warehouse; record the answer and any multi-branch limits in `docs/woocommerce.md`. Commit.

### Task 9: Docker packaging

**Files:**
- Create: `egypt-erp-dev/editions/shop.yaml`, `egypt-erp-dev/editions/shop-web.yaml`, `egypt-erp-dev/README.md` additions

**Interfaces:**
- Produces: two start commands, one per edition: `shop` installs `erpnext`, `egypt_core`, `egypt_retail`; `shop-web` adds `woocommerce_fusion`.

- [ ] **Step 1:** Build an image from `frappe_docker` that includes the apps for each edition.
- [ ] **Step 2:** Verify each edition starts from empty: `curl .../api/method/ping` returns `pong`, and `bench list-apps` matches the edition table.
- [ ] **Step 3:** Document start, stop and backup commands in plain language for a non-technical reader. Commit.

---

## Self-review

- **Spec coverage:** version 16 (Task 1), layers (3, 7), rebrand (4), Arabic and English (5), EGP, VAT and chart (6), multi-branch (7), optional WooCommerce (8), Docker (9), tests against upstream (3, CI), fork-edit record (1). Phases 2 to 4 are intentionally absent.
- **Types:** `create_branch` and `apply_egypt_defaults` signatures are used identically in the tasks that consume them.
- **Open items outside code:** product name (Task 0) and accountant confirmation (Task 6, step 5).
