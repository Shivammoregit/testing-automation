"""
Automated Website Testing Tool
Main entry point - handles browser launch, login, and orchestrates testing.
"""

import os
import sys
import time
from datetime import datetime
from urllib.parse import urlparse
from colorama import init, Fore, Style
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

import config
from models import TestSession, PageTest, TestStatus, CrawlPathStep
from crawler import PageCrawler, is_url_in_module
from tester import ElementTester
from report_generator import ReportGenerator
from route_seeds import (
    build_route_matchers,
    expand_route_paths,
    extract_param_values_from_urls,
    load_route_paths,
    normalize_param_values,
)
from error_explanations import (
    get_network_error_explanation,
    get_console_error_explanation,
    get_element_error_explanation
)

# Initialize colorama for Windows
init()


def print_banner():
    """Print welcome banner."""
    print(f"""
{Fore.CYAN}+====================================================================+
|                                                                    |
|   {Fore.MAGENTA}AUTOMATED WEBSITE TESTING TOOL{Fore.CYAN}                                 |
|                                                                    |
|   {Fore.WHITE}Features:{Fore.CYAN}                                                        |
|   - Auto-discovers pages and interactive elements                  |
|   - Tests buttons, links, forms, and dropdowns                     |
|   - Captures screenshots on failures                               |
|   - Logs network and console errors                                |
|   - Generates beautiful HTML reports                               |
|                                                                    |
+===================================================================={Style.RESET_ALL}
""")


def print_status(message: str, status: str = "info"):
    """Print colored status message."""
    colors = {
        "info": Fore.CYAN,
        "success": Fore.GREEN,
        "warning": Fore.YELLOW,
        "error": Fore.RED,
        "highlight": Fore.MAGENTA
    }
    color = colors.get(status, Fore.WHITE)
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"{Fore.WHITE}[{timestamp}]{Style.RESET_ALL} {color}{message}{Style.RESET_ALL}")


def _click_when_enabled(page, selector: str, timeout_ms: int, pick: str = "first") -> bool:
    try:
        locator = page.locator(selector)
        if pick == "last":
            locator = locator.last
        else:
            locator = locator.first
        locator.wait_for(state="visible", timeout=timeout_ms)
        try:
            locator.scroll_into_view_if_needed()
        except Exception:
            pass

        start_time = time.time()
        timeout_seconds = timeout_ms / 1000
        while time.time() - start_time < timeout_seconds:
            try:
                if locator.is_enabled():
                    locator.click()
                    return True
            except Exception:
                pass
            time.sleep(0.2)
        return False
    except Exception:
        return False


def _ensure_checkbox_checked(page, selector: str, timeout_ms: int) -> bool:
    try:
        checkbox = page.wait_for_selector(selector, timeout=timeout_ms)
        if checkbox:
            try:
                if checkbox.is_checked():
                    return True
            except Exception:
                pass
            try:
                checkbox.check()
            except Exception:
                try:
                    checkbox.click()
                except Exception:
                    pass
        return bool(page.evaluate(
            """
            sel => {
                const input = document.querySelector(sel);
                if (!input) return false;
                if (input.checked) return true;
                try {
                    input.checked = true;
                    input.dispatchEvent(new Event('input', { bubbles: true }));
                    input.dispatchEvent(new Event('change', { bubbles: true }));
                } catch (e) {}
                if (input.checked) return true;
                const clickable = input.closest("label") || input.parentElement || input;
                clickable.click();
                return input.checked;
            }
            """,
            selector
        ))
    except Exception:
        return False


def _click_stage_button(page, timeout_ms: int, labels: list[str]) -> bool:
    start_time = time.time()
    timeout_seconds = timeout_ms / 1000
    labels_norm = [label.lower() for label in labels if label]
    while time.time() - start_time < timeout_seconds:
        clicked = page.evaluate(
            """
            args => {
                const buttons = [...document.querySelectorAll(args.buttonSelector)]
                    .filter(btn => btn.textContent)
                    .filter(btn => args.labels.some(label => btn.textContent.toLowerCase().includes(label)))
                    .filter(btn => btn.offsetParent !== null);
                const target = buttons.find(btn => !btn.disabled && btn.getAttribute("aria-disabled") !== "true");
                if (!target) return false;
                target.click();
                return true;
            }
            """,
            {
                "buttonSelector": "button.auth-btn.auth-btn-primary",
                "labels": labels_norm,
            }
        )
        if clicked:
            return True
        time.sleep(0.2)
    return False


def attempt_auto_login(page) -> bool:
    """Attempt automated login if enabled in config."""
    if not config.AUTO_LOGIN_ENABLED:
        return False

    try:
        print_status("[INFO] Attempting auto-login...", "info")
        phone_input = page.wait_for_selector(
            config.AUTO_LOGIN_PHONE_SELECTOR,
            timeout=config.AUTO_LOGIN_STEP_TIMEOUT_MS
        )
        phone_value = config.AUTO_LOGIN_PHONE.strip()
        max_len = phone_input.get_attribute("maxlength")
        if max_len and max_len.isdigit():
            max_len_int = int(max_len)
            if len(phone_value) > max_len_int:
                phone_value = phone_value[-max_len_int:]
        phone_input.fill("")
        phone_input.click()
        page.keyboard.type(phone_value, delay=50)
        try:
            phone_input.dispatch_event("input")
            phone_input.dispatch_event("change")
        except Exception:
            pass
        try:
            page.keyboard.press("Tab")
        except Exception:
            pass
        time.sleep(0.3)

        if config.AUTO_LOGIN_CHECKBOX_SELECTOR:
            _ensure_checkbox_checked(
                page,
                config.AUTO_LOGIN_CHECKBOX_SELECTOR,
                config.AUTO_LOGIN_STEP_TIMEOUT_MS
            )

        if config.AUTO_LOGIN_SEND_OTP_BUTTON_SELECTOR:
            clicked = _click_when_enabled(
                page,
                config.AUTO_LOGIN_SEND_OTP_BUTTON_SELECTOR,
                config.AUTO_LOGIN_STEP_TIMEOUT_MS,
                pick="first"
            )
            if not clicked:
                clicked = _click_stage_button(
                    page,
                    config.AUTO_LOGIN_STEP_TIMEOUT_MS,
                    ["Send OTP", "Proceed"]
                )
            if not clicked:
                print_status("[WARN] Send OTP button did not enable in time.", "warning")
                return False

        if config.AUTO_LOGIN_OTP_CONTAINER_SELECTOR:
            page.wait_for_selector(
                config.AUTO_LOGIN_OTP_CONTAINER_SELECTOR,
                timeout=config.AUTO_LOGIN_OTP_WAIT_MS
            )

        otp_inputs = []
        if config.AUTO_LOGIN_OTP_INPUT_SELECTOR:
            otp_inputs = page.query_selector_all(config.AUTO_LOGIN_OTP_INPUT_SELECTOR)

        if otp_inputs:
            def _otp_sort_key(el):
                try:
                    el_id = el.get_attribute("id") or ""
                    if el_id.startswith("otp-"):
                        return int(el_id.split("-")[1])
                except Exception:
                    pass
                return 0

            otp_inputs = sorted(otp_inputs, key=_otp_sort_key)
            otp_digits = list(config.AUTO_LOGIN_OTP)
            for idx, input_el in enumerate(otp_inputs):
                if idx >= len(otp_digits):
                    break
                input_el.fill(otp_digits[idx])
        elif config.AUTO_LOGIN_OTP:
            page.keyboard.type(config.AUTO_LOGIN_OTP)

        if config.AUTO_LOGIN_SUBMIT_BUTTON_SELECTOR:
            clicked = _click_when_enabled(
                page,
                config.AUTO_LOGIN_SUBMIT_BUTTON_SELECTOR,
                config.AUTO_LOGIN_STEP_TIMEOUT_MS,
                pick="last"
            )
            if not clicked:
                clicked = _click_stage_button(
                    page,
                    config.AUTO_LOGIN_STEP_TIMEOUT_MS,
                    ["Proceed", "Verify", "Submit"]
                )
            if not clicked:
                print_status("[WARN] Submit button did not enable in time.", "warning")
                return False

        return True
    except Exception as e:
        print_status(f"[WARN] Auto-login failed: {str(e)[:80]}", "warning")
        return False


def wait_for_manual_login(page, login_url: str, wait_time: int):
    """Wait for user to complete manual login (OTP)."""
    print_status(f"\n{'='*60}", "highlight")
    print_status("MANUAL LOGIN REQUIRED", "highlight")
    print_status(f"{'='*60}\n", "highlight")
    
    print_status(f"Opening login page: {login_url}", "info")
    page.goto(login_url, timeout=config.PAGE_LOAD_TIMEOUT)

    if config.AUTO_LOGIN_ENABLED:
        attempt_auto_login(page)
    
    print_status(f"\n[WAIT] Please complete the login process (OTP) in the browser.", "warning")
    print_status(f"[WAIT] You have {wait_time} seconds to complete login.", "warning")
    print_status(f"[WAIT] The test will continue automatically after you log in.\n", "warning")
    
    # Wait for URL change or timeout
    initial_url = page.url
    start_time = time.time()
    
    while time.time() - start_time < wait_time:
        current_url = page.url
        current_url_lower = current_url.lower()

        if config.LOGIN_SUCCESS_SELECTOR:
            try:
                selector = page.query_selector(config.LOGIN_SUCCESS_SELECTOR)
                if selector and selector.is_visible():
                    print_status(f"[OK] Login detected (selector). Continuing with tests...", "success")
                    time.sleep(2)
                    return True
            except Exception:
                pass
        
        # Check if we've navigated away from login page
        if current_url != initial_url and "login" not in current_url_lower:
            print_status(f"[OK] Login detected! Continuing with tests...", "success")
            time.sleep(2)  # Give page time to fully load
            return True

        for keyword in config.LOGIN_SUCCESS_URL_KEYWORDS:
            if keyword.lower() in current_url_lower:
                print_status(f"[OK] Login detected (url keyword). Continuing with tests...", "success")
                time.sleep(2)
                return True
        
        time.sleep(1)
        remaining = int(wait_time - (time.time() - start_time))
        if remaining % 10 == 0 and remaining > 0:
            print_status(f"[WAIT] {remaining} seconds remaining...", "info")
    
    print_status("[!] Login timeout reached. Continuing anyway...", "warning")
    return False


def get_module_name(url: str) -> str:
    """Resolve a module name for the given URL."""
    parsed = urlparse(url)
    for module_name, module_urls in config.MODULES.items():
        for seed_url in module_urls:
            seed_parsed = urlparse(seed_url)
            if parsed.scheme != seed_parsed.scheme or parsed.netloc != seed_parsed.netloc:
                continue
            seed_path = seed_parsed.path.rstrip("/")
            url_path = parsed.path.rstrip("/")
            if url_path == seed_path or url_path.startswith(seed_path + "/"):
                return module_name
    return "Uncategorized"


def get_verification_text(error_type: str, status_code: int = None) -> str:
    """Provide a short verification step for the reported issue."""
    if error_type == "network":
        if status_code is None:
            return "Retry the request after the fix and confirm it returns a 2xx response."
        if status_code >= 500:
            return "Retry the action and confirm the endpoint returns 2xx without server errors."
        if status_code in (401, 403):
            return "Retry with a valid session and confirm access is allowed."
        if status_code == 404:
            return "Confirm the URL/resource exists and returns 200 after the fix."
        if status_code == 400:
            return "Retry with corrected inputs and confirm a successful response."
        return "Retry the request after the fix and confirm it returns 2xx."
    if error_type == "console":
        return "Repeat the same user action and confirm no console errors appear."
    if error_type == "element":
        return "Repeat the interaction and confirm the expected UI response occurs."
    return ""


def test_page(page, crawler: PageCrawler, tester: ElementTester, url: str) -> PageTest:
    """Test a single page."""
    page_test = PageTest(
        url=url,
        title="",
        status=TestStatus.PASSED
    )
    page_test.module = get_module_name(url)
    
    # Clear previous errors
    crawler.clear_errors()
    
    try:
        # Navigate to page
        start_time = time.time()
        page.goto(url, timeout=config.PAGE_LOAD_TIMEOUT, wait_until=config.PAGE_WAIT_UNTIL)
        page_test.load_time_ms = (time.time() - start_time) * 1000
        
        # Get page title
        page_test.title = page.title()
        
        # Wait a moment for any dynamic content
        time.sleep(config.CRAWL_DELAY)

        if config.DISCOVERY_WAIT_FOR_SELECTOR:
            try:
                page.wait_for_selector(
                    config.DISCOVERY_WAIT_FOR_SELECTOR,
                    timeout=config.DISCOVERY_WAIT_TIMEOUT_MS
                )
            except Exception:
                pass

        def _merge_links(target, new_links):
            for link in new_links:
                if link not in target:
                    target.append(link)

        if config.DISCOVERY_EXPAND_NAV:
            crawler.expand_discovery_elements()
        
        # Discover links
        page_test.discovered_links = crawler.discover_links()

        if config.DISCOVERY_SCROLL:
            scrolled = crawler.scroll_page()
            if scrolled and config.DISCOVERY_RESCAN_AFTER_SCROLL:
                _merge_links(page_test.discovered_links, crawler.discover_links())
        
        # Discover and test interactive elements
        elements = crawler.discover_interactive_elements()
        print_status(f"  Found {len(elements)} interactive elements", "info")
        
        for elem_info in elements:
            try:
                test_result = tester.test_element(elem_info)
                
                # Add explanation for element errors
                if test_result.status == TestStatus.FAILED and test_result.error_message:
                    explanation = get_element_error_explanation(
                        test_result.error_message,
                        test_result.element_type
                    )
                    test_result.explanation_title = explanation["title"]
                    test_result.explanation_text = explanation["explanation"]
                    test_result.simple_explanation = explanation.get("simple_explanation", "")
                    test_result.suggestion = explanation["suggestion"]
                    test_result.severity = explanation["severity"]
                    test_result.verification = get_verification_text("element")
                
                page_test.element_tests.append(test_result)
                
                if test_result.status == TestStatus.FAILED:
                    page_test.status = TestStatus.FAILED
            except Exception as e:
                print_status(f"  Error testing element: {str(e)[:50]}", "warning")

        if config.DISCOVERY_RESCAN_AFTER_INTERACTIONS:
            _merge_links(page_test.discovered_links, crawler.discover_links())

        extra_links = []
        for test_result in page_test.element_tests:
            if not test_result.navigated_url:
                continue
            normalized = crawler._normalize_url(test_result.navigated_url)
            if not crawler._is_valid_url(normalized):
                continue
            if normalized not in page_test.discovered_links and normalized not in extra_links:
                extra_links.append(normalized)
        if extra_links:
            _merge_links(page_test.discovered_links, extra_links)

        for test_result in page_test.element_tests:
            if test_result.status == TestStatus.FAILED and not test_result.screenshot_path and config.SCREENSHOT_ON_ERROR:
                test_result.screenshot_path = tester.take_page_screenshot("element_error")
        
        # Collect errors and add explanations
        network_errors, console_errors = crawler.get_collected_errors()
        
        # Add explanations to network errors
        for error in network_errors:
            explanation = get_network_error_explanation(error.status_code, error.url)
            error.explanation_title = explanation["title"]
            error.explanation_text = explanation["explanation"]
            error.simple_explanation = explanation.get("simple_explanation", "")
            error.suggestion = explanation["suggestion"]
            error.severity = explanation["severity"]
            error.verification = get_verification_text("network", error.status_code)
        
        # Add explanations to console errors
        for error in console_errors:
            explanation = get_console_error_explanation(error.message, error.error_type)
            error.explanation_title = explanation["title"]
            error.explanation_text = explanation["explanation"]
            error.simple_explanation = explanation.get("simple_explanation", "")
            error.suggestion = explanation["suggestion"]
            error.severity = explanation["severity"]
            error.verification = get_verification_text("console")
        
        page_test.network_errors = network_errors
        page_test.console_errors = console_errors

        if network_errors or console_errors:
            if config.SCREENSHOT_ON_ERROR:
                page_error_screenshot = tester.take_page_screenshot("page_error")
                for error in network_errors:
                    if not error.screenshot_path:
                        error.screenshot_path = page_error_screenshot
                for error in console_errors:
                    if not error.screenshot_path:
                        error.screenshot_path = page_error_screenshot
            if page_test.status != TestStatus.FAILED:
                page_test.status = TestStatus.WARNING
        
    except PlaywrightTimeout:
        page_test.status = TestStatus.FAILED
        print_status(f"  Page load timeout!", "error")
    except Exception as e:
        page_test.status = TestStatus.FAILED
        print_status(f"  Error: {str(e)[:100]}", "error")
    
    return page_test


def run_tests():
    """Main test runner."""
    print_banner()
    
    # Check configuration
    if "your-website" in config.WEBSITE_URL or not config.WEBSITE_URL.startswith("http"):
        print_status("ERROR: Please update WEBSITE_URL in config.py", "error")
        sys.exit(1)
    
    # Create output folder with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_folder = os.path.join(config.OUTPUT_FOLDER, f"run_{timestamp}")
    os.makedirs(output_folder, exist_ok=True)
    
    print_status(f"Output folder: {output_folder}", "info")
    print_status(f"Target website: {config.WEBSITE_URL}", "info")
    
    # Initialize session
    session = TestSession(website_url=config.WEBSITE_URL)
    
    with sync_playwright() as p:
        # Launch browser
        print_status("\n>> Launching browser...", "highlight")
        browser = p.chromium.launch(
            headless=config.BROWSER_HEADLESS,
            slow_mo=config.BROWSER_SLOW_MO
        )
        
        context = browser.new_context(
            viewport={"width": config.VIEWPORT_WIDTH, "height": config.VIEWPORT_HEIGHT}
        )
        
        page = context.new_page()
        
        # Set up timeout
        page.set_default_timeout(config.ELEMENT_TIMEOUT)
        page.set_default_navigation_timeout(config.NAVIGATION_TIMEOUT)
        
        # Initialize components
        crawler = PageCrawler(page, config.WEBSITE_URL, module_name=config.SINGLE_MODULE)
        tester = ElementTester(page, output_folder)
        
        # Handle login
        login_url = config.LOGIN_URL or config.WEBSITE_URL
        wait_for_manual_login(page, login_url, config.LOGIN_WAIT_TIME)
        
        # Start crawling from current page
        base_url = page.url
        # Store tuples of (url, discovered_from, depth)
        urls_to_test = []
        tested_urls = set()
        url_sources = {}  # Track where each URL was discovered from
        crawl_strategy = config.CRAWL_STRATEGY

        route_paths = []
        route_matchers = []
        route_param_values = normalize_param_values(config.ROUTE_SEED_DYNAMIC_PARAM_VALUES)
        route_seed_set = set()
        seed_base_url = config.ROUTE_SEED_BASE_URL or config.WEBSITE_URL

        def _enqueue_seed_url(seed_url: str, source_label: str) -> bool:
            normalized = crawler._normalize_url(seed_url)
            if not crawler._is_valid_url(normalized):
                return False
            if config.SINGLE_MODULE and not is_url_in_module(normalized, config.SINGLE_MODULE):
                return False
            if normalized in route_seed_set:
                return False
            if normalized in tested_urls or normalized in [u[0] for u in urls_to_test]:
                route_seed_set.add(normalized)
                return False
            urls_to_test.append((normalized, source_label, 0))
            url_sources[normalized] = (source_label, 0)
            route_seed_set.add(normalized)
            return True

        def _refresh_route_seeds(source_label: str) -> tuple[int, dict]:
            if not route_paths:
                return 0, {}
            expanded_urls, seed_stats = expand_route_paths(
                route_paths,
                seed_base_url,
                include_dynamic=config.ROUTE_SEED_INCLUDE_DYNAMIC,
                param_values=route_param_values,
                skip_missing=config.ROUTE_SEED_SKIP_MISSING_PARAMS
            )
            added = 0
            for seed_url in expanded_urls:
                if _enqueue_seed_url(seed_url, source_label):
                    added += 1
            return added, seed_stats

        def _update_route_params_from_urls(candidate_urls) -> int:
            if not route_matchers:
                return 0
            extracted = extract_param_values_from_urls(route_matchers, candidate_urls)
            if not extracted:
                return 0
            updated = 0
            for key, values in extracted.items():
                current = route_param_values.setdefault(key, [])
                for value in values:
                    if value not in current:
                        current.append(value)
                        updated += 1
            return updated

        if config.USE_ROUTE_SEEDS and config.ROUTE_SEED_FILE:
            route_paths, load_stats = load_route_paths(config.ROUTE_SEED_FILE)
            if load_stats.get("missing_file"):
                print_status(
                    f"[WARN] Route seed file not found: {config.ROUTE_SEED_FILE}",
                    "warning"
                )
            else:
                route_matchers = build_route_matchers(route_paths)
                added, seed_stats = _refresh_route_seeds("Route Seed")
                seed_stats["total_paths"] = load_stats.get("total_paths", seed_stats.get("total_paths", 0))
                print_status(
                    "Route seeds: "
                    f"{seed_stats.get('static_paths', 0)} static, "
                    f"{seed_stats.get('dynamic_expanded', 0)} dynamic (from "
                    f"{seed_stats.get('total_paths', 0)} paths)",
                    "info"
                )

        modules_to_test = config.MODULES
        if config.SINGLE_MODULE:
            if config.SINGLE_MODULE not in config.MODULES:
                print_status(f"ERROR: SINGLE_MODULE '{config.SINGLE_MODULE}' is not defined in MODULES.", "error")
                sys.exit(1)
            modules_to_test = {config.SINGLE_MODULE: config.MODULES[config.SINGLE_MODULE]}
            crawl_strategy = "dfs"

        if modules_to_test:
            for module_name, module_urls in modules_to_test.items():
                for seed_url in module_urls:
                    normalized = crawler._normalize_url(seed_url)
                    if normalized not in [u[0] for u in urls_to_test]:
                        urls_to_test.append((normalized, f"Module Seed: {module_name}", 0))
                        url_sources[normalized] = (f"Module Seed: {module_name}", 0)

        normalized_base = crawler._normalize_url(base_url)
        should_add_base = True
        if config.SINGLE_MODULE and not is_url_in_module(normalized_base, config.SINGLE_MODULE):
            should_add_base = False
            print_status(
                f"[SKIP] Start page outside selected module '{config.SINGLE_MODULE}': {normalized_base}",
                "warning"
            )
        if should_add_base and normalized_base not in [u[0] for u in urls_to_test]:
            urls_to_test.insert(0, (normalized_base, "Start Page", 0))
            url_sources[normalized_base] = ("Start Page", 0)
        
        print_status(f"\n{'='*60}", "highlight")
        print_status("STARTING AUTOMATED TESTS", "highlight")
        print_status(f"{'='*60}\n", "highlight")
        
        page_count = 0
        
        while urls_to_test and page_count < config.MAX_PAGES_TO_CRAWL:
            if crawl_strategy == "dfs":
                url, discovered_from, depth = urls_to_test.pop()
            else:
                url, discovered_from, depth = urls_to_test.pop(0)
            
            # Skip if already tested
            if url in tested_urls:
                continue
            if depth > config.MAX_DEPTH:
                continue
            
            tested_urls.add(url)
            crawler.visited_urls.add(url)
            page_count += 1
            
            print_status(f"\n[{page_count}/{config.MAX_PAGES_TO_CRAWL}] Testing: {url}", "highlight")
            
            # Test the page
            page_test = test_page(page, crawler, tester, url)
            
            # Add crawl path info
            page_test.discovered_from = discovered_from
            page_test.crawl_depth = depth
            
            session.pages_tested.append(page_test)
            
            # Add to crawl path
            crawl_step = CrawlPathStep(
                step_number=page_count,
                url=url,
                title=page_test.title,
                discovered_from=discovered_from,
                status=page_test.status,
                module=page_test.module,
                links_found=len(page_test.discovered_links)
            )
            session.crawl_path.append(crawl_step)
            
            # Status summary
            status_color = "success" if page_test.status == TestStatus.PASSED else (
                "warning" if page_test.status == TestStatus.WARNING else "error"
            )
            print_status(f"  Status: {page_test.status.value.upper()}", status_color)
            print_status(f"  Load time: {page_test.load_time_ms:.0f}ms", "info")
            print_status(f"  Network errors: {len(page_test.network_errors)}", 
                        "error" if page_test.network_errors else "success")
            print_status(f"  Console errors: {len(page_test.console_errors)}", 
                        "error" if page_test.console_errors else "success")
            print_status(f"  Elements tested: {page_test.total_elements_tested} (Failed: {page_test.elements_failed})",
                        "error" if page_test.elements_failed else "success")

            if config.USE_ROUTE_SEEDS and route_matchers:
                candidate_urls = set()
                candidate_urls.add(page_test.url)
                candidate_urls.update(page_test.discovered_links)
                for test_result in page_test.element_tests:
                    if test_result.navigated_url:
                        candidate_urls.add(test_result.navigated_url)
                if candidate_urls:
                    updated = _update_route_params_from_urls(candidate_urls)
                    if updated:
                        added, _ = _refresh_route_seeds("Route Seed (dynamic)")
                        if added:
                            print_status(
                                f"  Added {added} route seed URLs from dynamic params",
                                "info"
                            )
            
            # Add discovered links to queue with source tracking
            new_links_count = 0
            for link in page_test.discovered_links:
                if depth >= config.MAX_DEPTH:
                    continue
                if config.SINGLE_MODULE and not is_url_in_module(link, config.SINGLE_MODULE):
                    continue
                if link not in tested_urls and link not in [u[0] for u in urls_to_test]:
                    urls_to_test.append((link, url, depth + 1))
                    url_sources[link] = (url, depth + 1)
                    new_links_count += 1
            
            print_status(f"  Discovered {new_links_count} new links (depth: {depth})", "info")
        
        browser.close()
    
    # Finalize session
    session.end_time = datetime.now().isoformat()
    
    # Generate report
    print_status(f"\n{'='*60}", "highlight")
    print_status("GENERATING REPORT", "highlight")
    print_status(f"{'='*60}\n", "highlight")
    
    report_gen = ReportGenerator(output_folder)
    report_path = report_gen.generate_report(session)
    json_path = report_gen.save_session_data(session)
    
    # Print summary
    print_status("\n## TEST SUMMARY", "highlight")
    print_status(f"  Total pages tested: {session.total_pages}", "info")
    print_status(f"  Pages with errors: {session.pages_with_errors}", 
                "error" if session.pages_with_errors else "success")
    print_status(f"  Total network errors: {session.total_network_errors}",
                "error" if session.total_network_errors else "success")
    print_status(f"  Total console errors: {session.total_console_errors}",
                "error" if session.total_console_errors else "success")
    print_status(f"  Total elements tested: {session.total_element_tests}", "info")
    print_status(f"  Element failures: {session.total_element_failures}",
                "error" if session.total_element_failures else "success")
    print_status(f"  Duration: {session.duration_seconds:.1f} seconds", "info")
    
    print_status(f"\n[FILE] Report saved to: {report_path}", "success")
    print_status(f"[FILE] Data saved to: {json_path}", "success")
    
    # Open report in browser
    print_status("\n>> Opening report in browser...", "info")
    import webbrowser
    webbrowser.open(f"file://{os.path.abspath(report_path)}")
    
    return session


if __name__ == "__main__":
    run_tests()
