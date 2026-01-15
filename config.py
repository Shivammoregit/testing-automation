"""
Configuration settings for the automated testing tool.
Update these values according to your testing requirements.

============================================================
QUICK START - SINGLE MODULE TESTING
============================================================
To test a single module only, set SINGLE_MODULE to the module name:
    SINGLE_MODULE = "PawMatch"      # Test only PawMatch
    SINGLE_MODULE = "GroomUp"       # Test only GroomUp
    SINGLE_MODULE = None            # Test ALL modules

Available modules:
    - Vet Appointment
    - GroomUp
    - HomeVaxi
    - FeedaPaw
    - PawMatch
    - ShopYosa
    - Timeline
    - Pet BNB
    - FitYosa
    - Community
============================================================
"""

# Website configuration
WEBSITE_URL = "https://devapp.petyosa.com/login"  # Replace with your website URL

# # Login configuration
LOGIN_URL = "https://devapp.petyosa.com/login"  # Leave empty to use WEBSITE_URL, or specify login page URL
LOGIN_WAIT_TIME = 120  # Seconds to wait for manual OTP login

AUTO_LOGIN_ENABLED = True
AUTO_LOGIN_PHONE = "99999999999"
AUTO_LOGIN_OTP = "999999"
AUTO_LOGIN_PHONE_SELECTOR = "input.PhoneInputInput"
AUTO_LOGIN_CHECKBOX_SELECTOR = "input.PrivateSwitchBase-input"
AUTO_LOGIN_SEND_OTP_BUTTON_SELECTOR = "button.auth-btn.auth-btn-primary:has-text('Send OTP')"
AUTO_LOGIN_OTP_CONTAINER_SELECTOR = "div.auth-otp-fields"
AUTO_LOGIN_OTP_INPUT_SELECTOR = "div.auth-otp-fields input[id^='otp-']"
AUTO_LOGIN_SUBMIT_BUTTON_SELECTOR = "button.auth-btn.auth-btn-primary:has-text('Proceed')"
AUTO_LOGIN_STEP_TIMEOUT_MS = 10000
AUTO_LOGIN_OTP_WAIT_MS = 15000

# ============================================================
# SINGLE MODULE TESTING (Set to module name or None for all)
# ============================================================
SINGLE_MODULE = None  # Examples: "PawMatch", "GroomUp", None (for all)

# Crawling configuration
MAX_PAGES_TO_CRAWL = 400  # Maximum number of pages to discover and test
MAX_DEPTH = 5  # Maximum link depth to crawl
CRAWL_DELAY = 1  # Seconds to wait between page loads
ELEMENT_INTERACTION_DELAY = 0.5  # Seconds to wait between element interactions
INCLUDE_QUERY_PARAMS = True  # Keep query params when normalizing URLs
INCLUDE_HASH = False  # Keep URL hash fragments when normalizing URLs

# Discovery behavior (coverage improvements)
DISCOVERY_WAIT_FOR_SELECTOR = ""  # Optional CSS selector to wait for before discovery
DISCOVERY_WAIT_TIMEOUT_MS = 10000
DISCOVERY_EXPAND_NAV = True  # Try expanding menus/toggles before discovery
DISCOVERY_MAX_EXPAND_CLICKS = 12
DISCOVERY_CLICK_SELECTORS = [
    "button[aria-expanded='false']",
    "[aria-haspopup='true']",
    "[data-toggle='dropdown']",
    "[data-bs-toggle='dropdown']",
    "button[aria-controls]",
]
DISCOVERY_EXCLUDED_TEXT = [
    "logout",
    "sign out",
    "signout",
    "delete",
    "remove",
    "unsubscribe",
    "deactivate",
]
DISCOVERY_SCROLL = True  # Scroll to trigger lazy-loaded content
DISCOVERY_SCROLL_STEPS = 6
DISCOVERY_SCROLL_PAUSE_MS = 400
DISCOVERY_SCROLL_TO_TOP = True
DISCOVERY_RESCAN_AFTER_SCROLL = True
DISCOVERY_RESCAN_AFTER_INTERACTIONS = True

# Timeouts (in milliseconds)
PAGE_LOAD_TIMEOUT = 30000
ELEMENT_TIMEOUT = 5000
NAVIGATION_TIMEOUT = 30000
PAGE_WAIT_UNTIL = "domcontentloaded"  # domcontentloaded | load | networkidle | commit
NAVIGATION_WAIT_UNTIL = "domcontentloaded"  # domcontentloaded | load | networkidle | commit
POPUP_WAIT_TIMEOUT_MS = 1500  # How long to wait for a popup after click

# Screenshot settings
SCREENSHOT_ON_ERROR = True
SCREENSHOT_FULL_PAGE = True

# Excluded patterns (URLs matching these patterns will be skipped)
EXCLUDED_URL_PATTERNS = [
    "logout",
    "signout",
    "sign-out",
    "log-out",
    "/api/",
    ".pdf",
    ".zip",
    ".exe",
    "mailto:",
    "tel:",
    "javascript:",
    "#",
]

# Excluded elements (elements matching these selectors will not be clicked)
EXCLUDED_ELEMENT_SELECTORS = [
    "[data-testid='logout']",
    ".logout-btn",
    "#logout",
    "[href*='logout']",
    "[href*='signout']",
]

# Login detection
LOGIN_SUCCESS_SELECTOR = ""  # CSS selector that indicates login success (optional)
LOGIN_SUCCESS_URL_KEYWORDS = ["dashboard", "home"]  # URL keywords that indicate login success

# ============================================================
# MODULE CONFIGURATION
# Each module has a list of seed URLs to start crawling from
# ============================================================
MODULES = {
    "Vet Appointment": ["https://devapp.petyosa.com/book-appointment"],
    "GroomUp": ["https://devapp.petyosa.com/grooming"],
    "HomeVaxi": ["https://devapp.petyosa.com/homevaxi"],
    "FeedaPaw": ["https://devapp.petyosa.com/feedapaw"],
    "PawMatch": [
        "https://devapp.petyosa.com/pawmatch"
        # "https://devapp.petyosa.com/pawmatch/profile-setup",
        # "https://devapp.petyosa.com/pawmatch/verification",
        # "https://devapp.petyosa.com/pawmatch/swipe",
        # "https://devapp.petyosa.com/pawmatch/matches",
        # "https://devapp.petyosa.com/pawmatch/settings",
    ],
    "ShopYosa": ["https://devapp.petyosa.com/shopyosa"],
    "Timeline": ["https://devapp.petyosa.com/timeline-premium"],
    "Pet BNB": ["https://devapp.petyosa.com/pet-bnb"],
    "FitYosa": ["https://devapp.petyosa.com/fityosa-explore"],
    "Community": ["https://devapp.petyosa.com/community"],
}

# Route seed configuration (optional)
USE_ROUTE_SEEDS = True
ROUTE_SEED_FILE = r"C:\christ\petyosa\codebase\pet-frontend\src\Routes.js"
ROUTE_SEED_BASE_URL = ""  # Optional override; defaults to WEBSITE_URL origin
ROUTE_SEED_INCLUDE_DYNAMIC = True
ROUTE_SEED_SKIP_MISSING_PARAMS = True
ROUTE_SEED_DYNAMIC_PARAM_VALUES = {
    # "id": ["example-id"],
    # "orderId": ["example-order"],
}

# Crawl strategy: bfs (breadth-first) or dfs (depth-first)
# Note: dfs is automatically used when SINGLE_MODULE is set
CRAWL_STRATEGY = "bfs"

# Output settings
OUTPUT_FOLDER = "test_results"
REPORT_FILENAME = "test_report.html"

# Browser settings
BROWSER_HEADLESS = False  # Set to True for headless mode (no visible browser)
BROWSER_SLOW_MO = 100  # Slow down actions by this many milliseconds (for debugging)
VIEWPORT_WIDTH = 1920
VIEWPORT_HEIGHT = 1080

# Network error codes to capture
ERROR_STATUS_CODES = [400, 401, 403, 404, 405, 500, 502, 503, 504]

# Console error types to capture
CONSOLE_ERROR_TYPES = ["error", "pageerror", "warning"]

# Ignore noisy network errors (analytics, third-party, etc.)
IGNORE_NETWORK_ERROR_PATTERNS = [
    "google-analytics.com",
    "gtag/js",
    "googletagmanager.com",
    "facebook.com/tr",
    "sentry.io",
]
