# WooCommerce Fusion: research for Mizan (multi-branch retail on ERPNext 16)

Source: clone at `/home/user/starktail/woocommerce_fusion`, branch `version-16`. All paths below are relative to that clone. `WF/` means `woocommerce_fusion/` (the inner app folder).

## Summary for the owner (no jargon)

- **Stock goes one way: ERPNext to the website.** The website never changes your stock. You choose which warehouses count by ticking them in the WooCommerce Server settings. The connector adds up the stock of the ticked warehouses and sends that single number to the website.
- **You can tick every branch, or only one "Online" warehouse.** Either works technically. If you tick all branches, the website sells the combined stock of all branches. If you tick only an Online warehouse, the website sells only what you moved there.
- **New website orders are always created in ONE warehouse and ONE company.** Both are fixed in the WooCommerce Server settings. The connector does not pick the branch closest to the customer, and it does not split an order across branches.
- **The shop is one company, so one WooCommerce Server record per website is enough.** The app also supports several websites, each with its own settings.
- **Prices come from ONE Price List per website.** Prices go ERPNext to website. The app does not support a different price per branch.
- **Recommendation:** use a dedicated "Online" warehouse (see section 6). It makes the website's stock accurate. It also makes the online order picking process clear, and it keeps branch POS sales and website sales from overselling each other.

Two things to watch:
1. The stock number is only sent to the website when stock documents are submitted (Stock Entry, Stock Reconciliation, Sales Invoice with Update Stock, Delivery Note), plus once a day. It is not instant for every POS sale unless the POS invoice updates stock (it normally does).
2. The website's secret check on incoming order webhooks is currently disabled in the code (see section 5). That is a security point to raise with the developers.

---

## Technical detail

### 1. Which warehouses stock is synced FROM

**Direction:** ERPNext to WooCommerce only. The label says "Sync stock levels from ERPNext to WooCommerce (1-way)" (`WF/woocommerce/doctype/woocommerce_server/woocommerce_server.json:415-417`, field `enable_stock_level_synchronisation`).

**Settings doctype and fields** (all on the **WooCommerce Server** doctype):
- `enable_stock_level_synchronisation` (checkbox), `woocommerce_server.json:415`.
- `warehouses` (Table MultiSelect of child doctype **WooCommerce Server Warehouse**), `woocommerce_server.json:467-470`. Description: "Select the Warehouses that should be taken into account when synchronising Item Stock Levels". It is only shown when stock sync is enabled (`depends_on`, line 465). The child doctype has a single required Link field `warehouse` (`WF/woocommerce/doctype/woocommerce_server_warehouse/woocommerce_server_warehouse.json:13-18`). The picker is limited to enabled warehouses (`woocommerce_server.js:30-31`).
- `subtract_reserved_stock` ("Reserved Stock Adjustment"), `woocommerce_server.json:613-615`. When on, sends actual qty minus reserved qty. Saving is blocked unless "Enable Stock Reservation" is on in Stock Settings (`woocommerce_server.py:168-178`).
- `sync_in_sales_uom` (`woocommerce_server.json:423`) sends the quantity in the Item's Sales UOM instead of the Stock UOM, dividing by the UOM conversion factor (`WF/tasks/stock_update.py:116-123`; helper at `WF/tasks/utils.py:10-25`).
- `push_zero_stock_for_disabled_items` (`woocommerce_server.json:622`).

**Single vs multiple warehouses:** multiple are supported. The code is at `WF/tasks/stock_update.py:104-110`:

```
qty_in_stock_uom = sum( bin.actual_qty  [or actual_qty - reserved_qty]
                        for bin in bins
                        if bin.warehouse in [row.warehouse for row in wc_server.warehouses] )
```

So quantities from several warehouses are **summed** (plain addition of `Bin.actual_qty`, fetched at `stock_update.py:84-86`). The total is then rounded down with `math.floor` and sent as `stock_quantity` (`stock_update.py:126-129`), by `PUT products/{id}` or `products/{parent}/variations/{id}` (lines 131-150). The batch API path is used if `enable_batch_api` is on (lines 152-163).

**Pitfalls:**
- If stock sync is on but **no warehouses are ticked**, the sum is 0 and every linked product is pushed as 0 stock. I found no validation that makes the table mandatory (`woocommerce_server.py:33-48` calls only the validators for status map, item map, reserved stock, batch settings and tax accounts).
- The shipped doc is wrong or out of date. `docs/woocommerce_fusion_item-stock-levels.md:9` says "sum all quantities from all warehouses". The code sums only the selected ones. Trust the code.
- No per-warehouse reserve or buffer. There is no way to subtract a safety stock.
- Only Items with `is_stock_item` and a linked WooCommerce server row with a WooCommerce ID are pushed (`stock_update.py:76-78, 88-90`). The per-item row must have `enabled` ticked (line 95).

**When it fires:**
- Hooks on submit and cancel of Stock Entry, Stock Reconciliation, Sales Invoice, Delivery Note (`WF/hooks.py:110-125`). For Sales Invoice, only if `update_stock == 1` (`stock_update.py:28-30`). It needs at least one server with `enable_sync` and stock sync on (lines 17-26).
- Daily job: `daily_long` runs `update_stock_levels_for_all_enabled_items_in_background` (`hooks.py:151-154`). It enqueues a push for every Item (disabled ones only if `push_zero_stock_for_disabled_items`) (`stock_update.py:43-81`).
- Manual: button on the Item form (`docs/woocommerce_fusion_item-stock-levels.md:20-21`).
- POS Invoices are not in the hook list. A POS Invoice is consolidated into a Sales Invoice later (POS Closing / Invoice Consolidation), and that Sales Invoice is what triggers the sync. If Mizan's branches use POS Invoices with closing entries, website stock updates at consolidation time or at the next daily run. **This is an inference from the hook list; verify on a test site.**

### 2. Which Warehouse and Company new website Sales Orders use

Both come from the **WooCommerce Server** record that received the order. There is no branch routing logic.
- **Company:** `WooCommerce Server.company`, required Link to Company (`woocommerce_server.json:160-166`, description "This company will be used to create Sales Orders."). Applied at `WF/tasks/sync_sales_orders.py:570` (`new_sales_order.company = wc_server.company`).
- **Warehouse:** `WooCommerce Server.warehouse`, required Link to Warehouse, described as "Default warehouse for Sales Orders" (`woocommerce_server.json:195-200`). Applied to **every order line** (`sync_sales_orders.py:780`, `"warehouse": wc_server.warehouse`). If it is blank, order creation fails with "Please set Warehouse in WooCommerce Server" (lines 735-736).
- **Important:** this `warehouse` field is separate from the stock-sync `warehouses` table. Nothing forces the two to be consistent. Set them deliberately.
- Other Sales Order settings on the same record: `sales_order_series` (`woocommerce_server.json:150`), `delivery_after_days` (default 7, `sync_sales_orders.py:567-569`), `creation_user` (the user the webhook runs as, `woocommerce_endpoint.py:36`), `submit_sales_orders` (auto-submit, line 113), `sales_taxes_and_charges_template`, `use_actual_tax_type`, `tax_account`, `f_n_f_account`.
- Order lines are matched to Items through the Item's `woocommerce_servers` child table (WooCommerce ID plus server, only enabled Items) (`sync_sales_orders.py:742-757`).
- The app creates a Sales Order only. Delivery Note and Sales Invoice are made by Mizan's normal flow. Stock is deducted when the Delivery Note or Sales Invoice with Update Stock is submitted. That submit then triggers the stock push back to the website (section 1).

### 3. Multiple WooCommerce servers

- Doctype: **WooCommerce Server**, one record per website. The document name is derived from the URL domain (`woocommerce_server.py:25-29`).
- Per-server settings include: URL, API consumer key and secret (`woocommerce_server.json:239-255`), `enable_sync` (232), `secret` for webhooks (219, auto-generated at `woocommerce_server.py:41-42`), `company`, `warehouse`, `warehouses` table, `price_list` and `sales_price_list`, `item_group`, `uom`, `name_by`, tax and shipping mappings, status map, payment mappings, batch API options. Every one of these is per server.
- Items link to servers through the child doctype **Item WooCommerce Server** (fields `woocommerce_id`, `woocommerce_server` (required), `enabled`, `woocommerce_last_sync_hash`), shown on the Item form as the "WooCommerce Servers" table (`WF/woocommerce/doctype/item_woocommerce_server/item_woocommerce_server.json:17-44`). One Item can be on several sites.
- All sync tasks loop over every server (`WF/tasks/sync.py:18-26`, `get_wc_servers` returns all WooCommerce Server docs).
- Sales Orders and Customers carry `woocommerce_server` custom fields (`hooks.py:~240` fixtures).
- Incoming webhooks find the server from the `x-wc-webhook-source` header (`woocommerce_endpoint.py:19-24`).
- README confirms: "synchronise your ERPNext site with **multiple** WooCommerce websites" (`README.md:30`, `docs/woocommerce_fusion_introduction.md:6`).
- Global settings doctype **WooCommerce Integration Settings** only holds sync timestamps: `wc_last_sync_date`, `minimum_creation_date`, `wc_last_sync_date_items` (`woocommerce_integration_settings.json:14-27`). The order sync task raises an error if `wc_last_sync_date` is empty (`sync_sales_orders.py:114-128`). Set it at go-live.

For Mizan (one website per customer) this means one WooCommerce Server record. Nothing else is needed.

### 4. Item and price sync

**Items:**
- Direction is **two-way, last-modified wins** (`docs/woocommerce_fusion_items.md:20-25`). Hourly task `sync_woocommerce_products_modified_since` (`hooks.py:147-150`), plus hooks on Item `after_insert` and `on_update` (`hooks.py:131-134`, `WF/tasks/sync_items.py:36`).
- Core fields: item code (from WooCommerce ID or SKU, `name_by`), `item_name` to product `name` (`sync_items.py:464-466, 503-504`), variants and attributes. Image is one-way from WooCommerce to ERPNext, optional via `enable_image_sync`.
- New Items created from WooCommerce get `stock_uom = server.uom or "Nos"` and `item_group = server.item_group` (`sync_items.py:690-691`). Existing ERPNext Items can be matched by SKU if `match_items_by_sku` is on (`docs/woocommerce_fusion_items.md:30-39`).
- Extra fields can be mapped with the server's `item_field_map` using JSONPath (`sync_items.py:828-870`). The docs warn it is for advanced users.

**Prices (ERPNext to WooCommerce only):**
- Enable with `enable_price_list_sync` (`woocommerce_server.json:303`). The Price List named in `price_list` (required when sync is on) is pushed to the WooCommerce **Regular Price**.
- Optionally `enable_sales_price_list_sync` plus `sales_price_list` pushes to the WooCommerce **Sale Price**, including the Item Price `valid_from` and `valid_upto` as sale dates (`woocommerce_server.json:339-341`).
- Source is the **Item Price** doctype, field `price_list_rate`. Only rows with no batch, customer or supplier are used (`WF/tasks/sync_item_prices.py:39-49, 102-111`). Disabled Items are skipped unless `sync_prices_for_disabled_items`. If `sync_in_sales_uom` is on, the Item Price must be in the Item's Sales UOM (`sync_items.py:980-1010`).
- Push logic: `regular_price` compared and updated at `sync_item_prices.py:216-229`. Triggers are the Item Price `on_update` hook (`hooks.py:127-129`) and the daily job (`hooks.py:151-154`).
- Price is per website (per server). There is no per-warehouse or per-branch price. Branch-specific POS prices in other Price Lists are not touched.
- Taxes: whether the website price includes tax is not decided by Fusion. It only affects how the order rate is read back (`sync_sales_orders.py:760-768`). Align the Egypt VAT setup with the WooCommerce tax setting.

### 5. Install requirements and what the site needs

- **ERPNext version:** `pyproject.toml` `[tool.bench.frappe-dependencies]` pins `frappe >=16.0.0,<17.0.0` and `erpnext >=16.0.0,<17.0.0`. This is the `version-16` branch, so ERPNext 16 is required and v15 or v17 is not allowed.
- **Python:** `requires-python = ">=3.14"` (`pyproject.toml:5`). This needs to match ERPNext 16's Python. Check the hosting image.
- **Python dependencies:** `woocommerce~=3.0.0` and `jsonpath-ng~=1.7.0` (`pyproject.toml:8-11`).
- **required_apps:** `WF/hooks.py` has **no `required_apps`** line, so the install does not auto-check for ERPNext. The version pin in `pyproject.toml` is the only constraint. Install ERPNext first.
- **Scheduler:** it must be enabled. The app relies on `hourly_long` (orders and products from WooCommerce), `daily_long` (stock and prices), and a **per-minute cron** (`check_and_flush_all_servers`, batch API queue) (`hooks.py:146-160`). Background workers must run, including the `long` queue (`sync_sales_orders.py` and `woocommerce_endpoint.py:70` enqueue on `queue="long"`).
- **API keys:** a WooCommerce REST API key with **Read/Write** permission (WordPress admin, WooCommerce, Settings, Advanced, REST API) goes in `api_consumer_key` and `api_consumer_secret` (`docs/woocommerce_fusion_configure.md:7-9`). The site URL must be reachable from the ERPNext server over HTTPS (`woocommerce_api.py` uses `verify_ssl = not frappe._dev_server`, `stock_update.py:11`).
- **Webhook (recommended, not mandatory):** create an "Order created" webhook in WooCommerce pointing at the app's `order_created` endpoint (`WF/woocommerce_endpoint.py:48-49`, whitelisted with `allow_guest=True`), using the server's generated `secret` (`docs/woocommerce_fusion_sales-order.md:15-20`). Without it, new orders arrive at the next hourly run instead of immediately.
  - **Security note:** the signature check is **commented out** (`woocommerce_endpoint.py:29-39`; the HMAC is computed but never compared). The endpoint is a guest endpoint that then runs as `creation_user` (`woocommerce_endpoint.py:41`), identified only by the `x-wc-webhook-source` header. Anyone who knows the site domain could post a fake "created" event. The sync then fetches the order from the real WooCommerce API by id, which limits damage, but it can still trigger syncs. Raise this with the developers or restrict the URL at the proxy.
- **Other prerequisites:** a Company, a Warehouse, an Item Group, a UOM, a creation user, and (if used) a Sales Taxes template, bank or GL accounts for payment mapping, shipping rules. `enable_sync` must be ticked on the server record or nothing runs.
- **Custom fields** are installed through fixtures on Customer, Sales Order, Address and Item (`hooks.py` fixtures list, `Item-woocommerce_servers` etc.).
- Dev-only requirement (not needed in production): `hypothesis` and `parameterized` (`pyproject.toml` `[tool.bench.dev-dependencies]`).

### 6. Multi-branch limitations and recommendation

**Limitations for a multi-branch shop:**
1. **One selling warehouse per website for orders.** All lines of every website order are booked on `WooCommerce Server.warehouse` (`sync_sales_orders.py:780`). There is no routing by customer city, stock availability, or branch, and no split fulfilment.
2. **Stock shown on the site is a plain sum** of the ticked warehouses (`stock_update.py:104-110`). If you tick all branches, the site can show "5 in stock" when the 5 units are in 5 different branches. The order will still be booked on the one configured warehouse, which may hold 0 and so goes negative or gets blocked, depending on Stock Settings (allow negative stock).
3. **No per-warehouse safety buffer** and no "ignore stock below N" rule.
4. **Reserved stock** can be subtracted (`subtract_reserved_stock`), but only if ERPNext Stock Reservation is enabled. This may help if online orders reserve stock.
5. **No per-branch price.** One Price List per website (section 4).
6. **Stock updates are event-based.** A walk-in POS sale in a ticked warehouse updates the website only when the Sales Invoice (update stock) is submitted or at the next daily run (section 1). Under POS Invoice consolidation this can lag.
7. The docs say "all warehouses" but the code uses the selected ones (section 1). Do not rely on the doc.

**Recommendation for Mizan: use a dedicated "Online" warehouse (for example "Online - Mizan"), not an aggregate of branches.**

Reasoning:
- It fixes the order-booking mismatch (limitation 1 and 2). The same warehouse is set as `WooCommerce Server.warehouse` (orders) and as the only row in `warehouses` (stock sync). What the website shows equals what orders are booked against, so no overselling from a mismatch.
- Branch POS sales cannot silently drain the stock the website promised, because the site sells only what you moved to Online. Moving stock to Online is a normal Stock Entry (Material Transfer), which also triggers the website update (`hooks.py:111-114`).
- It matches the way multi-branch retailers actually fulfil web orders (a fulfilment point or the main store). It leaves branch POS Profiles unchanged.
- One simple Company plus Warehouse pairing is easy to explain to the owner and to support.

Trade-offs to explain to the owner:
- Stock must be transferred into Online before it can be sold on the web. Someone owns that process.
- If the owner wants "sell any branch's stock online", the aggregate option exists (tick all branch warehouses), but then also set `WooCommerce Server.warehouse` to the branch or central warehouse that will really ship, and accept the oversell risk in limitation 2. A middle option is to tick only a few warehouses (central store plus Online).
- Per-branch click-and-collect or nearest-branch fulfilment is **not** supported by this connector. It would need custom work (for example a script that reassigns the Sales Order warehouse after creation).

**Suggested config checklist for a Mizan site:**
1. Create the "Online" Warehouse under the one Company (not a POS Profile warehouse).
2. WooCommerce Server: `company` = the Mizan company, `warehouse` = Online, `warehouses` table = Online only, `enable_stock_level_synchronisation` on, and `subtract_reserved_stock` only if Stock Reservation is in use.
3. Create a dedicated Price List for the website (for example "Online Retail") and set it as `price_list`, with price sync on.
4. Set `creation_user` to a restricted user and `delivery_after_days`. Set `wc_last_sync_date` in WooCommerce Integration Settings.
5. Confirm the scheduler is enabled. Create the WooCommerce "Order created" webhook with the server's secret. Handle the webhook signature gap (section 5).
6. Test on staging: a POS sale in a branch, a web order, and a transfer into Online. Check the website stock after each. Also test whether POS Invoice consolidation triggers the push at the time you expect.
