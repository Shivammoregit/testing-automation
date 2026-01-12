"""
Configuration settings for the automated testing tool.
Update these values according to your testing requirements.
"""

# Website configuration
WEBSITE_URL = "https://devapp.petyosa.com/"  # Replace with your website URL

# Login configuration
LOGIN_URL = ""  # Leave empty to use WEBSITE_URL, or specify login page URL
LOGIN_WAIT_TIME = 120  # Seconds to wait for manual OTP login

# Crawling configuration
MAX_PAGES_TO_CRAWL = 100  # Maximum number of pages to discover and test
MAX_DEPTH = 5  # Maximum link depth to crawl
CRAWL_DELAY = 1  # Seconds to wait between page loads
ELEMENT_INTERACTION_DELAY = 0.5  # Seconds to wait between element interactions
INCLUDE_QUERY_PARAMS = True  # Keep query params when normalizing URLs
INCLUDE_HASH = False  # Keep URL hash fragments when normalizing URLs

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
