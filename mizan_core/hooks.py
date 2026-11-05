app_name = "mizan_core"
app_title = "Mizan"
app_publisher = "Mizan"
app_description = "Egyptian retail ERP customizations for ERPNext: branding, languages and Egyptian defaults"
app_email = "dev@mizan.example"
app_license = "gpl-3.0"

required_apps = ["erpnext"]

# Branding
# --------
app_logo_url = "/assets/mizan_core/images/logo.svg"
app_color = "#1F4E79"

# Overrides ERPNext's website_context favicon/splash (hooks win over settings).
website_context = {
	"favicon": "/assets/mizan_core/images/logo.svg",
	"splash_image": "/assets/mizan_core/images/logo.svg",
}

after_install = "mizan_core.branding.apply_branding"
after_migrate = "mizan_core.branding.apply_branding"
boot_session = "mizan_core.branding.rewrite_boot_apps"
app_include_js = "/assets/mizan_core/js/branding.js"
