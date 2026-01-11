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
from crawler import PageCrawler
from tester import ElementTester
from report_generator import ReportGenerator
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


def wait_for_manual_login(page, login_url: str, wait_time: int):
    """Wait for user to complete manual login (OTP)."""
    print_status(f"\n{'='*60}", "highlight")
    print_status("MANUAL LOGIN REQUIRED", "highlight")
    print_status(f"{'='*60}\n", "highlight")
    
    print_status(f"Opening login page: {login_url}", "info")
    page.goto(login_url, timeout=config.PAGE_LOAD_TIMEOUT)
    
    print_status(f"\n[WAIT] Please complete the login process (OTP) in the browser.", "warning")
    print_status(f"[WAIT] You have {wait_time} seconds to complete login.", "warning")
    print_status(f"[WAIT] The test will continue automatically after you log in.\n", "warning")
    
    # Wait for URL change or timeout
    initial_url = page.url
    start_time = time.time()
    
    while time.time() - start_time < wait_time:
        current_url = page.url
        
        # Check if we've navigated away from login page
        if current_url != initial_url and "login" not in current_url.lower():
            print_status(f"[OK] Login detected! Continuing with tests...", "success")
            time.sleep(2)  # Give page time to fully load
            return True
        
        time.sleep(1)
        remaining = int(wait_time - (time.time() - start_time))
        if remaining % 10 == 0 and remaining > 0:
            print_status(f"[WAIT] {remaining} seconds remaining...", "info")
    
    print_status("[!] Login timeout reached. Continuing anyway...", "warning")
    return False


def test_page(page, crawler: PageCrawler, tester: ElementTester, url: str) -> PageTest:
    """Test a single page."""
    page_test = PageTest(
        url=url,
        title="",
        status=TestStatus.PASSED
    )
    
    # Clear previous errors
    crawler.clear_errors()
    
    try:
        # Navigate to page
        start_time = time.time()
        page.goto(url, timeout=config.PAGE_LOAD_TIMEOUT, wait_until="networkidle")
        page_test.load_time_ms = (time.time() - start_time) * 1000
        
        # Get page title
        page_test.title = page.title()
        
        # Wait a moment for any dynamic content
        time.sleep(config.CRAWL_DELAY)
        
        # Discover links
        page_test.discovered_links = crawler.discover_links()
        
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
                    test_result.suggestion = explanation["suggestion"]
                    test_result.severity = explanation["severity"]
                
                page_test.element_tests.append(test_result)
                
                if test_result.status == TestStatus.FAILED:
                    page_test.status = TestStatus.FAILED
            except Exception as e:
                print_status(f"  Error testing element: {str(e)[:50]}", "warning")
        
        # Collect errors and add explanations
        network_errors, console_errors = crawler.get_collected_errors()
        
        # Add explanations to network errors
        for error in network_errors:
            explanation = get_network_error_explanation(error.status_code, error.url)
            error.explanation_title = explanation["title"]
            error.explanation_text = explanation["explanation"]
            error.suggestion = explanation["suggestion"]
            error.severity = explanation["severity"]
        
        # Add explanations to console errors
        for error in console_errors:
            explanation = get_console_error_explanation(error.message, error.error_type)
            error.explanation_title = explanation["title"]
            error.explanation_text = explanation["explanation"]
            error.suggestion = explanation["suggestion"]
            error.severity = explanation["severity"]
        
        page_test.network_errors = network_errors
        page_test.console_errors = console_errors
        
        if network_errors or console_errors:
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
        crawler = PageCrawler(page, config.WEBSITE_URL)
        tester = ElementTester(page, output_folder)
        
        # Handle login
        login_url = config.LOGIN_URL or config.WEBSITE_URL
        wait_for_manual_login(page, login_url, config.LOGIN_WAIT_TIME)
        
        # Start crawling from current page
        base_url = page.url
        # Store tuples of (url, discovered_from, depth)
        urls_to_test = [(base_url, "Start Page", 0)]
        tested_urls = set()
        url_sources = {base_url: ("Start Page", 0)}  # Track where each URL was discovered from
        
        print_status(f"\n{'='*60}", "highlight")
        print_status("STARTING AUTOMATED TESTS", "highlight")
        print_status(f"{'='*60}\n", "highlight")
        
        page_count = 0
        
        while urls_to_test and page_count < config.MAX_PAGES_TO_CRAWL:
            url, discovered_from, depth = urls_to_test.pop(0)
            
            # Skip if already tested
            if url in tested_urls:
                continue
            
            tested_urls.add(url)
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
            
            # Add discovered links to queue with source tracking
            new_links_count = 0
            for link in page_test.discovered_links:
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
