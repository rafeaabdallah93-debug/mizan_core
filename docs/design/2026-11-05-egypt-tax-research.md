# Egypt tax defaults and chart of accounts: briefing for accountant review (Mizan)

Prepared 2026-11-05. DRAFT. Research limitation: the session's network allowed web search but blocked direct fetch of eta.gov.eg, pwc.com/taxsummaries, kpmg.com, ey.com and others (DNS failure). Everything below comes from search-result snippets, not from reading the official pages. No claim here was verified against the ETA site or the law text. Treat every figure as a lead to check, not a fact. Items marked UNCONFIRMED were not seen on an official or Big-4 source.

## Plain-language summary for the owner

- The normal VAT (sales tax) rate in Egypt is 14%. Many sources agree. ERPNext's built-in "GST 10%" for Egypt is wrong and should not be used.
- Basic foods and medicines are generally exempt from VAT (not "0%"). Exports are 0%. Cigarettes, alcohol and some other goods carry an extra "Table Tax" (also called schedule tax) as well as VAT. These goods are the likely trap for a retail shop.
- You must register for VAT once your sales over the last 12 months reach about EGP 500,000. One secondary source claims the threshold dropped to EGP 250,000 in 2026. The other sources I found disagree, so ask your accountant.
- Normal VAT returns are monthly, due around the end of the following month. A new small-business regime (Law 6 of 2025, turnover up to EGP 20 million) allows a flat turnover tax of roughly 0.4% to 1.5% and quarterly VAT returns. Ask your accountant whether you qualify and whether it replaces or sits alongside VAT. This choice affects how Mizan should be set up.
- When your shop buys goods or services from a registered company, a small percentage (reported as 1% for goods, 3% for services, 5% for commissions and professional fees) may be withheld and paid to the tax authority. It is an advance on income tax, not an extra cost. Whether your shop must withhold, or only gets withheld from, depends on its type.
- Larger retailers must issue electronic receipts through the tax authority's system. The list grows in waves. Your accountant must check whether your shop is on the list.
- Egypt has no single mandatory chart of accounts that I could confirm for private shops. A simple draft chart is proposed at the end for the accountant to correct.

## 1. VAT rates (Law 67 of 2016 and amendments)

| Claim | Source | Date/version | Status |
|---|---|---|---|
| Standard VAT rate is 14% (in force from FY starting 1 July 2017) | KPMG TaxNewsFlash, Oct 2016: https://assets.kpmg.com/content/dam/kpmg/xx/pdf/2016/10/tnf-egypt-october-13-2016.pdf (seen as a search snippet only) | 2016 | Big-4, snippet only. Re-check for 2026 |
| 14% still standard after Law 157 of 2025 (published in Official Gazette 17 July 2025, effective next day) | KPMG Egypt Tax Alert No. 2, July 2025: https://assets.kpmg.com/content/dam/kpmg/eg/tax-newsletter/2025/Tax%20Alert%20No.%20(2)%20July%202025.pdf ; EY: https://taxnews.ey.com/news/2025-1554 (22 Jul 2025) and https://taxnews.ey.com/news/2025-2316 (18 Nov 2025) | 2025 | Big-4 existence of amendment confirmed via snippets. "Rate unchanged at 14%" comes from Kintsugi guide https://trykintsugi.com/sales-tax-guides/middle-east/egypt (2026) = UNCONFIRMED against official text |
| 5% reduced rate on production machinery and equipment | Kintsugi guide above; KPMG 2016 newsletter lists the 5% band | 2016 / 2026 | Partly Big-4 |
| Exports of goods and services: 0% | KPMG 2016 above; Avalara https://www.avalara.com/vatlive/en/country-guides/africa-and-middle-east/egypt-vat/egyptian-vat-rates.html | n/d | Partly Big-4 |
| Basic foodstuffs, medicines, medical supplies: exempt (input VAT not recoverable). An older Avalara article said nil-rated; it predates the enacted law | Kintsugi guide; Avalara https://www.avalara.com/vatlive/en/vat-news/egypt-vat-exemptions.html | 2016 / 2026 | UNCONFIRMED. Exact exempt list must come from Law 67/2016 Article 3 and annex |
| Construction supply-and-install moved from 5% schedule tax to standard VAT (not retail-relevant) | Deloitte: https://www.deloitte.com/middle-east/en/services/tax/perspectives/construction-contracting-activities-treatment-following-the-vat-law-amendments.html ; EY above | 2025 | Big-4 |
| EY reports Ministerial Decrees 417 and 418 of 2025 (Oct 2025) further amended VAT | EY https://taxnews.ey.com/news/2025-2316 | 18 Nov 2025 | Big-4 snippet. Content not read |
| Table Tax / schedule tax: applies once at first sale or import, in addition to VAT for scheduled goods; tobacco and alcohol are the main retail-relevant items. Law 157 of 2025 changed treatment of cigarettes and alcohol | KPMG Alert July 2025 (above); Kintsugi guide | 2025/2026 | Rate table NOT found. UNCONFIRMED |

Implication for Mizan: seed tax templates 14% (standard), 0% (export), Exempt (basic food and medicine). Do not seed a rate for Table Tax goods until the accountant gives the current schedule. Note that an exempt supply means input VAT on those purchases cannot be reclaimed, so mixed shops need an apportionment decision.

## 2. Registration threshold and filing

- Mandatory registration at EGP 500,000 of taxable plus exempt sales over the prior 12 months, register within 30 days. Sources: ETA FAQ as quoted by https://lookuptax.com/docs/country/egypt-vat-guidelines-indirect-tax (checked 2026-09-20 per that page); https://accounts-os.com/eg/questions/what-is-the-vat-rate-in-egypt.md (updated 25 Oct 2026); Kintsugi (19 Jul 2026). All secondary. UNCONFIRMED against eta.gov.eg directly.
- CONFLICT: Beancount https://beancount.io/blog/2026/07/26/egypt-law-6-2025-sme-simplified-tax-regime-guide and VATupdate (https://www.vatupdate.com/?p=357047) claim Resolution 281 of 2025 halved the threshold to EGP 250,000 with a March 2026 deadline. Other sources found tie Decision 281 of 2025 to the e-receipt rollout instead, so this claim may be a confusion. UNCONFIRMED. Accountant must settle.
- Voluntary registration below the threshold: sources conflict. UNCONFIRMED.
- Filing: monthly return (Form 10), due by the end of the month following the period. Source: lookuptax compliance calendar https://lookuptax.com/compliance-calendar/egypt and https://www.vatupdate.com/2026/07/29/egypt-monthly-vat-filing-compliance-2026-deadlines-form-no-10-penalties/ (29 Jul 2026). UNCONFIRMED (secondary). Exact day (30th vs last day) unclear.
- Small-business regime, Law 6 of 2025, effective 1 March 2025, turnover up to EGP 20 million, registered or not: EY, "Egypt introduces tax incentives and benefits for small enterprises", 28 Feb 2025: https://www.ey.com/en_gl/technical/tax-alerts/egypt-introduces-tax-incentives-and-benefits-for-small-enterprises (Big-4, snippet read). Reported turnover-tax brackets (Beancount, secondary, UNCONFIRMED): 0.4% to EGP 500k; 0.5% to 2m; 0.75% to 3m; 1% to 10m; 1.5% to 20m. Sources differ on the top rate (Andersen says up to 1%; ETA chief reportedly 1.5%). Reported benefits: quarterly VAT filing, exemption from advance tax payments and stamp duty (secondary, UNCONFIRMED). Whether it replaces VAT for a retailer is NOT confirmed.

## 3. Withholding tax (WHT / "deduction at source")

- Local payments above EGP 300 for supplies, contracting and services (Income Tax Law 91 of 2005, Art. 59, as amended; Law 30 of 2023 referenced): reported 1% on supplies and contracting, 3% on services, 5% on commissions, brokerage and non-commercial professional fees (professional fees threshold EGP 100, Art. 70). Sources: PwC Tax Summaries https://taxsummaries.pwc.com/egypt/corporate/withholding-taxes (page last reviewed 13 Aug 2025 per search snippet); Andersen https://eg.andersen.com/withholding-taxes-in-egypt/ . Treated as an advance payment of income tax, not an extra cost (PwC). The 1/3/5 set is consistently reported but I did not read the Ministerial decision text (one source cites Decree 405 of 2018). Older commentary cites 0.5%/2%/5%. UNCONFIRMED for 2026; "recently updated" per PwC.
- Calculated on net amount before VAT (Ecovis https://global.ecovis.com/egypt/tax-guide/). Secondary.
- Who withholds: generally companies and registered entities paying other registered persons. Whether a small individually-owned shop must withhold is UNCONFIRMED. Suppliers in the advance payment system may be exempt (Arabic secondary summary). Form 41 is the periodic WHT return (npiegypt.com, secondary).
- Mizan implication: keep WHT as a configurable rate on purchase documents plus a "WHT receivable/payable" account, do not hardcode rates.

## 4. Invoice and receipt content, e-receipt note

- Tax registration number on receipts: I could not confirm the receipt content rules from any official source. Search returned nothing on it. Generally an invoice shows seller name, address, tax registration number, date, description, quantities, prices, VAT amount. UNCONFIRMED; ask accountant.
- E-receipt (B2C) note: the ETA e-receipt system is mandatory only for taxpayers named in ETA decisions, issued in waves, with every branch and POS of a listed taxpayer included. Rollout began 2022 with large retailers, expanding through 2025: sixth wave from 15 Jan 2025 (Resolution 405/2024); Decision 281 of 2025 added taxpayers from 15 Sep 2025 (phase 8). One source mentions "Decision 361" with 15 Nov 2025 (unreconciled). Sources: KPMG https://kpmg.com/us/en/taxnewsflash/news/2025/01/tnf-egypt-taxpayers-required-comply-mandate-electronic-receipts-b2c-transactions.html (Jan 2025) and https://kpmg.com/us/en/taxnewsflash/news/2025/07/tnf-egypt-new-taxpayers-required-to-comply-with-mandate-to-issue-electronic-receipts-for-b2c-transactions.html (Jul 2025) (Big-4, snippets only); Comarch, Sovos (secondary). Status in late 2026 not found. Small shops should check the ETA lookup of their registration number.

## 5. Chart of accounts

- Mandatory unified chart for private SMEs: NOT confirmed. A World Bank review (https://openknowledge.worldbank.org/bitstreams/28719a1e-dbcb-5a61-b1f6-c8bb4b2658db/download, date not captured) says the Finance Ministry is authorised to set a standardised chart, and calls Accounting Practice Law 133/1951 outdated. The government Unified Accounting System applies to public bodies. I found no source requiring private SMEs to use a prescribed chart. UNCONFIRMED.
- Standards: Egyptian Accounting Standards (EAS), largely IFRS-aligned. A micro-entity accounting standard exists for very small businesses (from memory, UNCONFIRMED).
- Common structure: five groups (1 assets, 2 liabilities, 3 equity, 4 revenue, 5 expenses) is typical in Egyptian practice (from memory, UNCONFIRMED). Odoo's Egypt localisation vendor guide https://ecosire.com/blog/odoo-egypt-localization-guide-2026 uses a different scheme (2xxxx liabilities, 3xxxx equity, 4xxxx revenue, 5xxxx cost of sales, 6xxxx-7xxxx opex); it is a vendor blog, not official.

### Draft minimal SME retail chart (DRAFT FOR ACCOUNTANT REVIEW, not an official chart)

| Code | English | Arabic |
|---|---|---|
| 1000 | Assets | الأصول |
| 1100 | Cash on hand (tills) | النقدية بالصندوق |
| 1110 | Cash in drawer / petty cash | عهدة نقدية / نثرية |
| 1200 | Banks | البنوك |
| 1210 | Bank - current account | البنك - حساب جاري |
| 1300 | Accounts receivable | العملاء |
| 1400 | Inventory (merchandise) | المخزون السلعي |
| 1500 | Input VAT (recoverable) | ضريبة القيمة المضافة - مدخلات |
| 1510 | Withholding tax receivable (deducted by customers) | ضريبة خصم وإضافة مدينة (مخصومة من العملاء) |
| 1600 | Fixed assets | الأصول الثابتة |
| 1690 | Accumulated depreciation | مجمع الإهلاك |
| 2000 | Liabilities | الالتزامات |
| 2100 | Accounts payable | الموردون |
| 2200 | Output VAT payable | ضريبة القيمة المضافة - مخرجات |
| 2210 | Net VAT due to tax authority | ضريبة القيمة المضافة المستحقة للمصلحة |
| 2220 | Withholding tax payable (deducted from suppliers) | ضريبة خصم وإضافة دائنة (مخصومة من الموردين) |
| 2230 | Table (schedule) tax payable | ضريبة الجدول المستحقة |
| 2240 | Payroll tax and social insurance payable | ضريبة كسب العمل والتأمينات المستحقة |
| 2300 | Accrued expenses | مصروفات مستحقة |
| 3000 | Equity | حقوق الملكية |
| 3100 | Owner's capital | رأس المال |
| 3200 | Retained earnings | الأرباح المرحلة |
| 3300 | Owner's drawings | مسحوبات الشريك / المالك |
| 4000 | Revenue | الإيرادات |
| 4100 | Sales | المبيعات |
| 4190 | Sales returns and discounts | مردودات ومسموحات المبيعات |
| 5000 | Cost of goods sold | تكلفة البضاعة المباعة |
| 5100 | Cost of goods sold | تكلفة المبيعات |
| 5200 | Inventory adjustments and shrinkage | فروق جرد وتالف |
| 6000 | Operating expenses | المصروفات التشغيلية |
| 6100 | Salaries and wages | الأجور والمرتبات |
| 6200 | Rent | الإيجار |
| 6300 | Utilities (electricity, water, internet) | مرافق (كهرباء ومياه وإنترنت) |
| 6400 | Bank and card fees | عمولات بنكية وبطاقات |
| 6500 | Depreciation | الإهلاك |
| 6900 | Other expenses | مصروفات أخرى |

Mizan note: ERPNext requires root types (Asset, Liability, Equity, Income, Expense) and account types (Cash, Bank, Stock, Tax, Receivable, Payable, COGS); mapping is straightforward.

## Questions for your accountant

1. Confirm the 2026 standard VAT rate is 14%, and the current official list of exempt and 0% items relevant to our shop (food, medicine, other).
2. Which of our products (cigarettes, alcohol, others) carry Table Tax, at what rates, and does it show on the receipt?
3. Is the VAT registration threshold EGP 500,000 or EGP 250,000 for 2026? Is voluntary registration allowed below it?
4. Should we use the Law 6 of 2025 simplified turnover-tax regime? Does it replace VAT for us? Does it change filing to quarterly?
5. Monthly VAT return: exact due day, and how do we handle input VAT when we sell both exempt and taxable goods?
6. Withholding tax: are we required to withhold from suppliers, and are our customers allowed to withhold from us? Current rates (1/3/5%?) and the EGP 300 threshold.
7. What must appear on our receipts and invoices (tax registration number, VAT breakdown, wording)?
8. Are we on the ETA e-receipt list, and from what date? What device or POS integration is needed?
9. Is any prescribed chart of accounts required for our legal form? Please correct the draft chart (codes, names, Arabic wording, missing accounts such as stamp duty, social insurance, and Table Tax).
10. Do we need the micro-entity accounting standard, and what financial statements are required?
