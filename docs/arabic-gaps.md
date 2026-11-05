# Arabic gaps seen on the Sales Invoice form (ERPNext 16.53, language `ar`)

Checked with a throwaway user (deleted afterwards) on the new Sales Invoice form. Layout is right-to-left (`<html dir="rtl" lang="ar">`), tabs, sidebar and fields mirror correctly.

## Untranslated or wrong
- Table column "Item" is still English (items grid).
- Field help text "Is customer exempted from sales tax?" is English.
- Sidebar entry "Chart of Accounts" is English.
- Two buttons both read "تحميل" (Upload/Download) in the items grid, ambiguous.
- Raw fieldnames (`customer`, `naming_series`, `is_pos`, `items` ...) appear in the page text next to labels (hidden description/screen-reader text; verify whether visible in a real session).
- Odd machine wording: "نشر التوقيت" (Posting Time), "كمية (INR)" for Amount, "سعر السلعة المفردة" for Rate, "لا." for No., "هو العودة (ملاحظة الائتمان)" for Is Return.
- "Naming series" value `ACC-SINV-.YYYY.-` renders with the dash misplaced under RTL (bidi): needs `dir=ltr` on code-like fields.

## Other
- Currency shows INR/₹ because no Egyptian company or EGP default is set yet (Egyptian defaults task).
- Print preview of an unsaved invoice returns 404 (expected); `dir="rtl"` is set on that error page. Print of a saved invoice not checked (no company/customer data on the dev site).
