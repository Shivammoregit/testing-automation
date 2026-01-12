# 🔍 Automated Website Testing Tool

A Python + Playwright tool that automatically discovers and tests all pages, buttons, links, and interactive elements on your website. Captures screenshots and error logs when functionality fails.

## ✨ Features

- **Auto-Discovery**: Automatically crawls and discovers all pages on your website
- **Element Testing**: Tests buttons, links, forms, dropdowns, and other interactive elements
- **Error Capture**: Captures network errors (4xx, 5xx) and console errors
- **Screenshots**: Takes screenshots when elements fail or errors occur
- **Beautiful Reports**: Generates HTML reports with dark theme and filters
- **OTP Login Support**: Allows manual login (for OTP) before automated testing begins

## 📦 Installation

1. **Create a virtual environment** (recommended):
   ```bash
   cd c:\christ\petyosa\testing
   python -m venv venv
   venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Playwright browsers**:
   ```bash
   playwright install chromium
   ```

## ⚙️ Configuration

Edit `config.py` to customize the testing:

```python
# Your website URL
WEBSITE_URL = "https://your-website.com"

# Login page (leave empty to use WEBSITE_URL)
LOGIN_URL = ""

# Time to wait for manual OTP login (seconds)
LOGIN_WAIT_TIME = 120

# Maximum pages to test
MAX_PAGES_TO_CRAWL = 100

# Run browser in headless mode (no UI)
BROWSER_HEADLESS = False
```

### Key Configuration Options

| Setting | Description | Default |
|---------|-------------|---------|
| `WEBSITE_URL` | Your website's URL | - |
| `LOGIN_URL` | Login page URL (optional) | Same as WEBSITE_URL |
| `LOGIN_WAIT_TIME` | Seconds to wait for OTP login | 120 |
| `MAX_PAGES_TO_CRAWL` | Maximum pages to discover/test | 100 |
| `MAX_DEPTH` | Link depth to crawl | 5 |
| `BROWSER_HEADLESS` | Run without visible browser | False |
| `SCREENSHOT_ON_ERROR` | Take screenshots on failures | True |
| `EXCLUDED_URL_PATTERNS` | URL patterns to skip | logout, api, etc. |
| `PAGE_WAIT_UNTIL` | Navigation wait state for page loads | domcontentloaded |
| `NAVIGATION_WAIT_UNTIL` | Wait state for link/button navigation | domcontentloaded |
| `INCLUDE_QUERY_PARAMS` | Keep query params while crawling | True |
| `INCLUDE_HASH` | Keep URL fragments while crawling | False |
| `LOGIN_SUCCESS_SELECTOR` | CSS selector to detect login success | "" |
| `LOGIN_SUCCESS_URL_KEYWORDS` | URL keywords to detect login success | dashboard, home |
| `POPUP_WAIT_TIMEOUT_MS` | Time to wait for popup after click | 1500 |
| `IGNORE_NETWORK_ERROR_PATTERNS` | Network error URL patterns to ignore | google-analytics.com, sentry.io |
| `MODULES` | Module name to seed URLs mapping | See config.py |
| `SINGLE_MODULE` | Test only one module by name | "" |
| `CRAWL_STRATEGY` | Crawl order (bfs or dfs) | bfs |

## 🚀 Usage

1. **Update config.py** with your website URL

2. **Run the tool**:
   ```bash
   python main.py
   ```

### Smoke Test (Homepage Only)
Runs a quick check that the homepage loads without console errors:
```bash
python smoke_test.py
```
You can also pass a URL:
```bash
python smoke_test.py https://devapp.petyosa.com/
```

3. **Login manually** when the browser opens:
   - The browser will open your website/login page
   - Complete the OTP login process manually
   - The tool will detect when you're logged in and continue automatically

4. **Wait for testing to complete**:
   - The tool will discover and test all pages
   - Progress is shown in the terminal
   - Screenshots are captured on failures

5. **View the report**:
   - Report opens automatically in your browser
   - Located in `test_results/run_YYYYMMDD_HHMMSS/test_report.html`

## 📁 Output Structure

```
test_results/
└── run_20260112_001745/
    ├── test_report.html     # Main HTML report
    ├── test_data.json       # Raw test data
    └── screenshots/         # Failure screenshots
        ├── button_error_*.png
        ├── link_timeout_*.png
        └── ...
```

## 📊 HTML Report Features

- **Summary Dashboard**: Quick overview of test results
- **Filter Options**: Filter by All/Errors/Passed
- **Expandable Pages**: Click to see detailed results
- **Error Details**: Network and console errors with full info
- **Element Tests**: Status of each tested element
- **Screenshot Links**: Direct links to failure screenshots

## 🛡️ What Gets Tested

### Pages
- ✅ Page load success/timeout
- ✅ Page load time
- ✅ Network errors (400, 401, 403, 404, 500, etc.)
- ✅ Console errors and warnings

### Elements
- ✅ **Buttons**: Click functionality
- ✅ **Links**: Navigation and response
- ✅ **Forms**: Input focus and interactivity
- ✅ **Dropdowns**: Toggle open/close
- ✅ **Modals**: Trigger functionality
- ✅ **Navigation**: Menu items

## 🔧 Customization

### Add Excluded URLs
Edit `config.py` to skip certain URLs:
```python
EXCLUDED_URL_PATTERNS = [
    "logout",  # Skip logout links
    "/api/",   # Skip API endpoints
    ".pdf",    # Skip PDF files
]
```

### Add Excluded Elements
Prevent certain elements from being tested:
```python
EXCLUDED_ELEMENT_SELECTORS = [
    "[data-testid='logout']",
    ".delete-btn",
    "#dangerous-action",
]
```

## Module-wise Testing

Define modules in `config.py` to seed crawling and group results in the report:
```python
MODULES = {
    "Vet Appointment": ["https://devapp.petyosa.com/book-appointment"],
    "GroomUp": ["https://devapp.petyosa.com/grooming"],
}
```

## 🐛 Troubleshooting

### Browser doesn't open
- Make sure `BROWSER_HEADLESS = False` in config.py
- Try running `playwright install chromium` again

### Login detection not working
- Increase `LOGIN_WAIT_TIME` in config.py
- Make sure your site redirects after login

### Too many pages being tested
- Reduce `MAX_PAGES_TO_CRAWL` in config.py
- Add patterns to `EXCLUDED_URL_PATTERNS`

### Elements not being found
- Some elements may be dynamically loaded
- Try increasing `CRAWL_DELAY` in config.py

## 📝 License

MIT License - Feel free to modify and use as needed!
