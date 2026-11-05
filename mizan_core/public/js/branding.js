// Replaces ERPNext's name/logo in the apps screen payload. Frappe fills
// boot.apps_data after all server boot hooks have run, so it is rewritten here.
(function () {
	const brand = "Mizan";
	const logo = "/assets/mizan_core/images/logo.svg";
	const isErp = (v) => typeof v === "string" && v.toLowerCase().includes("erpnext");
	const boot = (window.frappe && frappe.boot) || {};
	((boot.apps_data && boot.apps_data.apps) || []).forEach((app) => {
		if (isErp(app.title)) app.title = brand;
		if (isErp(app.logo)) app.logo = logo;
	});
})();
