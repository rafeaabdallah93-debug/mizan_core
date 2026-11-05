# Phase 1 decisions log

Decisions made during Phase 1 implementation on the owner's behalf. Each line: decision — reason — cost if wrong. Change any of them by asking.

- apps are named mizan_core and mizan_retail (repos rafeaabdallah93-debug/mizan_core, /mizan_retail), replacing egypt_core / egypt_retail everywhere — owner's choice — cost if wrong: rename.
- Docker images pinned to v16.53.0 (ERPNext) with the matching Frappe 16 release, not a floating version-16 tag — spec requires stability and Task 1 pins v16.53.0 — cost if wrong: re-pull images.
- Task 2 dev environment lives at /home/user/mizan-dev, not version-controlled; Task 9 edition packaging goes into mizan_retail/deploy/ — no packaging repo exists and the retail edition owns the edition definitions — cost if wrong: move files.
- branding uses plain-text logo "Mizan" / "ميزان" and a neutral default primary color until the owner supplies assets — owner said leave the logo for now — cost if wrong: swap two constants.
- Task 8 guard test is allowed to pass on first run — it guards independence, not new behavior — cost if wrong: none.
- mizan_core and mizan_retail start on branch `main` (repos were empty, so the first push sets the default branch) — no existing branch to protect — cost if wrong: rename the branch.
- app git repos are cloned straight into /home/user/mizan-dev/custom-apps/<app> (bench mounts only that folder; symlinks don't resolve inside containers); /home/user/mizan_core and /home/user/mizan_retail clones stay empty and unused — cost if wrong: re-clone elsewhere.
- desk app switcher/sidebar still showing "ERPNext" (from ERPNext hooks via frappe/boot.py) is in scope for Task 4, not a later follow-up — spec forbids ERPNext branding — dispatched as follow-up to the Task 4 implementer — cost if wrong: one extra small commit.
- the asset 404 is a Task 2 environment defect, fixed by the Task 2 implementer in /home/user/mizan-dev, then Task 4 re-checked in a browser — cost if wrong: none.
- Task 8 docs recommend a dedicated "Online" warehouse used as both the order warehouse and the only stock-sync warehouse — research shows orders book to one fixed warehouse — cost if wrong: reconfigure settings.
- Task 6 uses EGYPT_VAT_RATE = 14.0 marked # UNVERIFIED, and the research's draft bilingual chart as the CSV draft marked UNVERIFIED — best available sources agree on 14% — cost if wrong: change one constant and the CSV after accountant review.
- Task 6 runs in parallel with Task 5's review (same repo, disjoint files; implementer rebases on conflicts) — owner asked to use more agents — cost if wrong: a rebase or a fix round touching hooks.
- Task 6 implementer on the most capable model — accounting defaults are high-stakes and need API verification — cost: higher spend.
- Task 6 also creates a demo company "Mizan Demo" (MD) on the dev site so the owner sees EGP — cost if wrong: delete one company on a dev site.
- Task 7 starts in parallel with Task 6 review (different repo; consumes apply_egypt_defaults as-is; reports, doesn't fix, mizan_core bugs) — owner asked for more agents — cost if wrong: Task 7 rework if Task 6 API changes.
- retail prices are VAT-inclusive (PRICES_INCLUDE_VAT = True, UNVERIFIED) — Egyptian consumer prices are normally shown inclusive — cost if wrong: flip one constant and re-apply; POS totals change.
- Fiscal Year creation is fixed now (was Minor) — real customers have no _Test Fiscal Year and POS/stock would fail — cost: small.
- chart-present detection uses >half of (number, name) pairs instead of the reviewer's "any number" rule — ERPNext's numbered standard chart reuses our numbers; re-reviewer judged it sound — cost if wrong: a heavily renamed chart is refused (never wiped).
- fresh-site failure is a Task 6 load-bearing defect (every real customer install is a fresh site), sent back to Task 6 rather than parked — cost if wrong: none.
- fix round 3 (3 script lines) verified by controller reading the script and checking /login=200 instead of a reviewer dispatch — trivial, non-product dev tooling — cost if wrong: a 502 after install, fixed by restarting frontend.
- ERPNext setup wizard is bypassed by a Mizan provisioning command added in Task 9 (creates the customer's company via apply_egypt_defaults, then marks setup complete) — prevents a second company with the GST placeholder on first login — cost if wrong: customers see ERPNext's wizard.
- default UI language on a new site stays English with Arabic enabled and switchable per user — spec says switchable; Arabic translation gaps are documented — cost if wrong: one setting in provisioning.
- persistent install of woocommerce_fusion's Python deps belongs to Task 9 (shop-web image build), not the dev env — the plan's Task 9 builds edition images — cost if wrong: dev env loses deps on recreate until re-run.
- Task 9 split into 9a (mizan_core provisioning command: create company via apply_egypt_defaults + mark setup wizard complete) and 9b (edition images/compose in mizan_retail/deploy) — 9b depends on 9a; 9a can run alongside Task 6's read-only re-review — cost if wrong: none.
- usage-data sharing (Frappe telemetry) is turned OFF by provisioning — customers' business data privacy; owner can re-enable — cost if wrong: one setting.
- 9b documents creating the shop's first real user from the desk (Administrator → Users); automated user creation is out of Phase 1 scope — cost if wrong: one manual step per install.
- Task 9b must rebuild images from mizan_core's HEAD after 9a fix round 1 lands (it started from 0bdc4fc) — cost if wrong: edition images miss telemetry-off.
- editions bind to 127.0.0.1 by default; LAN access is an explicit opt-in (HTTP_BIND=0.0.0.0) with an unencrypted-connection warning — safest default for non-technical owners — cost if wrong: owners must set one variable to add tills on other PCs.
- build scripts made portable AND README states Linux / WSL2 / macOS+Docker Desktop prerequisites — cost: small.
- customer editions and the CLI both default to Arabic (`ar`) — target users are Egyptian shop staff; supersedes the earlier "English default" ruling — cost if wrong: one default in two places.
- placeholder email dev@mizan.example removed from package metadata (no owner contact address supplied; owner's personal email not used) — cost if wrong: owner adds a contact later.
- shop-web webhook security stays a release gate for the owner, not fixed in Phase 1 — installed unchanged per spec — cost if wrong: shop-web can't be sold until resolved.

## Open security item

- woocommerce_fusion's webhook HMAC signature check is commented out upstream (woocommerce_endpoint.py). The shop-web edition must not go live until it is fixed upstream or patched, or the order_created endpoint is blocked at a reverse proxy.

## Deferred minor items (from task and final reviews)

- Task 2: minor (deferred): any dir under custom-apps is registered as an app
- Task 2: minor (deferred): .env is generated state; gitignore if mizan-dev ever becomes a repo
- Task 2: minor (deferred): `hypothesis` not in image (some frappe tests need it)
- Task 3: minor (deferred): license.txt is a short GPL notice, not full GPL-3.0 text (matters for distribution)
- Task 3: minor (deferred): placeholder email dev@mizan.example in hooks.py and pyproject.toml
- Task 3: minor (deferred): CI actions v4/v5 vs template v6; CI untested on GitHub
- Task 4: minor (deferred): after_migrate re-applies branding and overwrites admin changes to logo/favicon/brand_html/footer on each migrate
- Task 4: minor (deferred): SVG hardcodes the color instead of using BRAND_COLOR; BRAND_NAME_AR unused outside tests
- Task 4: minor (deferred): `bench build --app mizan_core` killed (exit 143) — no bundles yet, watch in later tasks
- Task 4: minor (deferred): workspace.py:707 re-calls get_app_data() without a hook — no visible leak observed
- Task 2: minor (deferred): socket.io "Invalid origin" in dev stack
- Task 5: minor (deferred): enable_languages() calls frappe.clear_cache() on every migrate; no test locks install.py ordering; arabic-gaps.md mixes speculative notes
- Task 5: minor (deferred): language test cleanup re-enables ar/en unconditionally rather than restoring prior state
- Task 6: minor (deferred): default_provisional_account, capital_work_in_progress_account, unrealized_exchange_gain_loss_account, default_discount_account left empty
- Task 6: minor (deferred): Arabic chart names mapping not applied anywhere yet
- Task 6: minor (deferred): VAT template with restructured rows fails every re-apply ("exactly one row")
- Task 6: minor (deferred): used-template throw aborts before fiscal year/time zone steps
- Task 6: minor (deferred): no negative test for signature-restricted placeholder cleanup
- Task 6: minor (deferred): Mizan Demo relies on leftover global "_Test Fiscal Year 2026"
- Task 7: minor (deferred): sale test uses Sales Invoice is_pos+update_stock, not POS Invoice (needs POS Opening Entry)
- Task 7: minor (deferred): CI pulls mizan_core main unpinned
- Task 2: minor (deferred): plain `up -d` recreating backend may still leave frontend with stale IP (documented in README)
- Task 7: minor (deferred): suffix check case-sensitive; no Price List permission pre-check; success message shows same name twice
- Task 6: minor (deferred): fixtures skip doctypes with any rows (no partial repair); time zone forced to Africa/Cairo on every call
- Task 8: minor (deferred): import guard is regex-only (wheel path since fixed)
- Task 6: minor (deferred): positive branch of real _is_bare_site not unit-tested
- Task 6: minor (deferred): add_uom_data only when UOM table empty (unrequested tweak; partial UOM sets not repaired)
- Task 9a: minor (deferred): two System Settings saves on first run; hard-coded "setup-wizard"/"workspace" constants
- Task 9a: minor (deferred): unpatched refusal test assumes other companies exist (environment-dependent; CI green because earlier tests create companies); CLI generic-error path untested
- Task 9b: minor (deferred): restore.sh passes DB root password on the command line inside the container
- Task 9b: minor (deferred): no explicit "MIGRATION FAILED" line; README lacks chmod command for .env; weak DB root password caught only after db volume init (documented); mid-new-site crash path unverified
