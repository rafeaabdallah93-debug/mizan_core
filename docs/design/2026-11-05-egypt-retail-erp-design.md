# Egypt Retail ERP: Design Spec

Date: 2026-11-05
Status: draft, awaiting owner review

## 1. Purpose

Build a simpler ERP tailored to the Egyptian market, based on ERPNext, for small and medium Egyptian retail businesses. The product is meant to be distributed or sold to others. It ships in editions (retail first) that are combinations of installable apps.

### Agreed facts (stated by the owner)
- Target: small and medium Egyptian shops, with or without a website.
- First use case: retail, one owner with many branches, each branch with its own inventory.
- Interface languages: Arabic and English, switchable per user.
- Interface simplification happens only after the owner has seen the working product.
- Owner wants to keep receiving upstream ERPNext updates.
- WooCommerce integration uses `Starktail/woocommerce_fusion`, optional per customer.
- Egyptian e-invoicing is the last phase.

### Assumptions confirmed by the owner
- Customers are SMEs, not large enterprises.
- "Tailored to Egypt" includes Arabic/RTL, chart of accounts, VAT and e-invoicing.
- "Simpler" means hiding or removing screens, not rewriting accounting.

## 2. Architecture: layers on top (Approach B)

```
Retail edition app          retail setup, multi-branch helpers
Egypt core app              branding, languages, Egyptian defaults
WooCommerce Fusion          optional, installed unchanged
ERPNext 16 (fork)           kept nearly pristine, tracks upstream
Frappe 16                   framework, from upstream
```

- The ERPNext fork stays on the stable `version-16` line (upstream branches `version-16` and `version-16-hotfix`) and pulls upstream fixes. Edits to ERPNext's own files are exceptional, each one recorded.
- Product code lives in separate repositories (Egypt core app, Retail edition app) so upstream merges never collide with it.
- An "edition" is the set of apps installed on a customer's site:
  - Shop, no website: Egypt core + Retail
  - Shop with website: Egypt core + Retail + WooCommerce Fusion

### Why version 16
WooCommerce Fusion declares `frappe >=16.0.0,<17.0.0` and `erpnext >=16.0.0,<17.0.0`. The fork was on `develop` (17.0.0-dev), which that connector refuses. Version 16 is the released, stable line. Move to 17 later, once released and supported by the connector.

## 3. Multi-branch retail

One company with many branches. Mapped onto ERPNext built-ins:

| Need | ERPNext concept |
|---|---|
| Separate inventories | Warehouse (one per branch) |
| Moving goods between branches | Stock Entry (Material Transfer) |
| Each branch sells independently | POS Profile tied to the branch warehouse |
| Per-branch reports | Stock and sales reports filtered by warehouse |

The Retail edition app provides an easy "add a branch" flow that creates the warehouse and till together. Multi-company (separate legal entities) is out of scope for now.

WooCommerce: with several branches and one website, the connector must know which warehouse the site sells from. To be confirmed when the integration is designed in detail.

## 4. Build order

1. **Product you can see.** ERPNext 16 base, rebrand (name, logo, colors), Arabic and English with RTL, EGP currency and Egyptian defaults (chart of accounts, VAT rate), Retail edition with multi-branch setup, optional WooCommerce Fusion, Docker packaging. Interface left as ERPNext ships it.
2. **Simplification.** Hide modules, trim forms, automate setup. Guided by what the owner sees in phase 1. Done inside the product apps through settings, not edits to ERPNext.
3. **Other editions** (services, manufacturing) and possibly an installer or desktop wrapper.
4. **Egyptian e-invoicing.** Integration with the Egyptian Tax Authority e-invoice and e-receipt systems. Requirements to be confirmed with an Egyptian accountant and official sources before design.

## 5. Legal and licensing

- ERPNext is GPL v3. Distributing the product requires making the modified source available under GPL v3.
- The name "ERPNext" and its logo are trademarks of Frappe Technologies. The product must use its own name and logo and must not imply affiliation (see `TRADEMARK_POLICY.md` in the fork).

## 6. Risks and open items

- **Egypt has no regional code in ERPNext.** The Egypt layer starts from scratch.
- **Unverified Egyptian rules.** VAT rate, chart of accounts and e-invoicing requirements are not yet verified.
- **Upstream drift.** Hooks and overrides in our apps can break on ERPNext updates, so we need tests that run against each upstream release.
- **Arabic quality.** ERPNext's Arabic translation quality varies. Review is needed for retail-facing screens.
- **Product name** not chosen yet.
- **Where the fork's current work goes.** The fork's working branch is still on `develop`, and moving it to `version-16` is not done yet.

## 7. Out of scope for now
- Interface simplification (phase 2)
- E-invoicing (phase 4)
- Multi-company setups
- Desktop `.exe` installer
