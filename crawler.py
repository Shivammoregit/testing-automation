"""
Page crawler module - discovers all pages and elements on the website.
"""

import time
from urllib.parse import urljoin, urlparse
from typing import Set, List, Tuple, Optional
from playwright.sync_api import Page, ElementHandle
import config
from models import NetworkError, ConsoleError, PageTest, ElementTest, TestStatus


def is_url_in_module(url: str, module_name: str) -> bool:
    """Return True if url belongs to the module's seed path(s)."""
    if not module_name:
        return True
    module_urls = config.MODULES.get(module_name, [])
    if not module_urls:
        return False

    parsed = urlparse(url)
    for seed_url in module_urls:
        seed_parsed = urlparse(seed_url)
        if parsed.scheme != seed_parsed.scheme or parsed.netloc != seed_parsed.netloc:
            continue
        seed_path = seed_parsed.path.rstrip("/")
        url_path = parsed.path.rstrip("/")
        if url_path == seed_path or url_path.startswith(seed_path + "/"):
            return True
    return False


class PageCrawler:
    """Crawls and discovers pages on a website."""
    
    def __init__(self, page: Page, base_url: str, module_name: Optional[str] = None):
        self.page = page
        self.base_url = base_url
        parsed_base = urlparse(base_url)
        self.base_domain = parsed_base.netloc
        self.base_scheme = parsed_base.scheme
        self.module_name = module_name or None
        self.visited_urls: Set[str] = set()
        self.urls_to_visit: List[Tuple[str, int]] = []  # (url, depth)
        self.network_errors: List[NetworkError] = []
        self.console_errors: List[ConsoleError] = []
        
        # Set up network and console listeners
        self._setup_listeners()
    
    def _setup_listeners(self):
        """Set up listeners for network and console errors."""
        
        def handle_response(response):
            if response.status in config.ERROR_STATUS_CODES:
                for pattern in config.IGNORE_NETWORK_ERROR_PATTERNS:
                    if pattern.lower() in response.url.lower():
                        return
                try:
                    request = response.request
                    self.network_errors.append(NetworkError(
                        url=response.url,
                        method=request.method,
                        status_code=response.status,
                        status_text=response.status_text,
                        request_headers=dict(request.headers) if request.headers else {},
                        response_headers=dict(response.headers) if response.headers else {}
                    ))
                except Exception as e:
                    print(f"Error capturing network error: {e}")
        
        def handle_console(msg):
            if msg.type in config.CONSOLE_ERROR_TYPES:
                self.console_errors.append(ConsoleError(
                    message=msg.text,
                    error_type=msg.type,
                    source=msg.location.get("url", "") if msg.location else "",
                    line_number=msg.location.get("lineNumber", 0) if msg.location else 0
                ))
        
        def handle_page_error(error):
            self.console_errors.append(ConsoleError(
                message=str(error),
                error_type="pageerror",
                source="page"
            ))
        
        self.page.on("response", handle_response)
        self.page.on("console", handle_console)
        self.page.on("pageerror", handle_page_error)
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if URL should be crawled."""
        if not url:
            return False

        # Resolve to absolute URL before checks
        absolute_url = urljoin(self.page.url, url)
        parsed = urlparse(absolute_url)

        # Only http(s) links
        if parsed.scheme and parsed.scheme not in ("http", "https"):
            return False

        # Must be same domain
        if parsed.netloc and parsed.netloc != self.base_domain:
            return False
        if parsed.scheme and parsed.scheme != self.base_scheme:
            return False

        # Check excluded patterns
        for pattern in config.EXCLUDED_URL_PATTERNS:
            if pattern.lower() in absolute_url.lower():
                return False

        if self.module_name and not is_url_in_module(absolute_url, self.module_name):
            return False
        
        return True

    def _url_in_selected_module(self, url: str) -> bool:
        """Check if url belongs to the selected module (if any)."""
        if not self.module_name:
            return True
        return is_url_in_module(url, self.module_name)

    def _get_element_target_url(self, element) -> str:
        """Extract target URL from element attributes, if any."""
        for attr in ("href", "data-href", "data-route", "data-url"):
            try:
                value = element.get_attribute(attr)
            except Exception:
                value = None
            if not value:
                continue
            if attr == "href":
                lower_value = value.lower()
                if value == "#" or lower_value.startswith("javascript:") or "void(0)" in lower_value:
                    continue
            return value
        return ""

    def _should_include_element(self, element) -> bool:
        """Apply module-aware filtering for element testing."""
        if not self._should_test_element(element):
            return False
        if not self.module_name:
            return True

        target_url = self._get_element_target_url(element)
        if not target_url:
            return True

        target_lower = target_url.lower()
        if target_url.startswith("#") or target_lower.startswith("javascript:"):
            return True

        absolute_url = urljoin(self.page.url, target_url)
        parsed = urlparse(absolute_url)
        if parsed.scheme and parsed.scheme not in ("http", "https"):
            return False
        if parsed.netloc and parsed.netloc != self.base_domain:
            return False
        return self._url_in_selected_module(absolute_url)

    def _is_excluded_discovery_text(self, element) -> bool:
        """Skip discovery clicks for elements with excluded text."""
        if not config.DISCOVERY_EXCLUDED_TEXT:
            return False
        try:
            text = (self._get_element_text(element) or "").lower()
        except Exception:
            return False
        if not text or text in ("[no text]", "[unknown]"):
            return False
        for token in config.DISCOVERY_EXCLUDED_TEXT:
            if token and token.lower() in text:
                return True
        return False

    def _is_safe_discovery_target(self, element) -> bool:
        """Limit discovery clicks to low-risk toggles."""
        if not self._should_include_element(element):
            return False
        if self._is_excluded_discovery_text(element):
            return False
        try:
            if not element.is_visible():
                return False
        except Exception:
            return False
        try:
            if not element.is_enabled():
                return False
        except Exception:
            pass
        try:
            href = element.get_attribute("href")
        except Exception:
            href = None
        if href:
            href_lower = href.lower()
            if href == "#" or href_lower.startswith("javascript:") or "void(0)" in href_lower:
                return True
            return False
        return True

    def expand_discovery_elements(self) -> int:
        """Try expanding navigation or toggles to reveal hidden links."""
        if not config.DISCOVERY_EXPAND_NAV:
            return 0
        max_clicks = max(0, int(config.DISCOVERY_MAX_EXPAND_CLICKS))
        if max_clicks == 0:
            return 0

        clicked = 0
        seen = set()
        for selector in config.DISCOVERY_CLICK_SELECTORS:
            if clicked >= max_clicks:
                break
            query = selector if ":visible" in selector else f"{selector}:visible"
            try:
                elements = self.page.query_selector_all(query)
            except Exception:
                continue
            for element in elements:
                if clicked >= max_clicks:
                    break
                if not self._is_safe_discovery_target(element):
                    continue
                key = f"{self._get_selector(element)}|{self._get_element_text(element)}"
                if key in seen:
                    continue
                seen.add(key)
                try:
                    element.click(timeout=config.ELEMENT_TIMEOUT)
                    clicked += 1
                    time.sleep(config.ELEMENT_INTERACTION_DELAY)
                except Exception:
                    continue

        return clicked

    def scroll_page(self) -> bool:
        """Scroll the page to trigger lazy-loaded content."""
        if not config.DISCOVERY_SCROLL:
            return False
        try:
            total_height = self.page.evaluate("() => document.body.scrollHeight") or 0
            if total_height <= 0:
                return False
            steps = max(1, int(config.DISCOVERY_SCROLL_STEPS))
            step_size = max(1, int(total_height / steps))
            for step in range(1, steps + 1):
                position = min(total_height, step * step_size)
                self.page.evaluate("(y) => window.scrollTo(0, y)", position)
                time.sleep(config.DISCOVERY_SCROLL_PAUSE_MS / 1000)
            if config.DISCOVERY_SCROLL_TO_TOP:
                self.page.evaluate("() => window.scrollTo(0, 0)")
                time.sleep(config.DISCOVERY_SCROLL_PAUSE_MS / 1000)
            return True
        except Exception:
            return False
    
    def _normalize_url(self, url: str) -> str:
        """Normalize URL for comparison."""
        # Make absolute URL
        absolute_url = urljoin(self.page.url, url)

        # Remove fragments
        parsed = urlparse(absolute_url)
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

        if config.INCLUDE_QUERY_PARAMS and parsed.query:
            normalized = f"{normalized}?{parsed.query}"
        if config.INCLUDE_HASH and parsed.fragment:
            normalized = f"{normalized}#{parsed.fragment}"
        
        # Remove trailing slash for consistency
        if normalized.endswith("/") and len(normalized) > len(f"{parsed.scheme}://{parsed.netloc}/"):
            normalized = normalized[:-1]
        
        return normalized
    
    def discover_links(self) -> List[str]:
        """Discover all links on the current page."""
        discovered = []

        try:
            # Find all anchor tags
            links = self.page.query_selector_all("a[href]")

            for link in links:
                try:
                    href = link.get_attribute("href")
                    if href and self._is_valid_url(href):
                        normalized = self._normalize_url(href)
                        if normalized not in self.visited_urls:
                            discovered.append(normalized)
                except Exception:
                    continue
        except Exception as e:
            print(f"Error discovering links: {e}")

        attribute_selectors = [
            ("[data-href]", "data-href"),
            ("[data-route]", "data-route"),
            ("[data-url]", "data-url"),
        ]
        for selector, attribute in attribute_selectors:
            try:
                elements = self.page.query_selector_all(selector)
                for elem in elements:
                    try:
                        href = elem.get_attribute(attribute)
                        if href and self._is_valid_url(href):
                            normalized = self._normalize_url(href)
                            if normalized not in self.visited_urls:
                                discovered.append(normalized)
                    except Exception:
                        continue
            except Exception:
                continue

        return list(set(discovered))
    
    def discover_interactive_elements(self) -> List[dict]:
        """Discover all interactive elements on the current page."""
        elements = []
        
        # Buttons
        try:
            buttons = self.page.query_selector_all("button:visible, [role='button']:visible, input[type='button']:visible, input[type='submit']:visible")
            for btn in buttons:
                if self._should_include_element(btn):
                    elements.append({
                        "type": "button",
                        "element": btn,
                        "text": self._get_element_text(btn),
                        "selector": self._get_selector(btn)
                    })
        except Exception:
            pass
        
        # Clickable elements (not links)
        try:
            clickables = self.page.query_selector_all("[onclick]:visible, [data-action]:visible")
            for elem in clickables:
                if self._should_include_element(elem):
                    elements.append({
                        "type": "clickable",
                        "element": elem,
                        "text": self._get_element_text(elem),
                        "selector": self._get_selector(elem)
                    })
        except Exception:
            pass
        
        # Form inputs
        try:
            inputs = self.page.query_selector_all("input:visible:not([type='hidden']), select:visible, textarea:visible")
            for inp in inputs:
                if self._should_include_element(inp):
                    elements.append({
                        "type": "input",
                        "element": inp,
                        "text": self._get_element_text(inp),
                        "selector": self._get_selector(inp)
                    })
        except Exception:
            pass
        
        # Navigation items
        try:
            nav_items = self.page.query_selector_all("nav a:visible, .nav a:visible, .navbar a:visible, .menu a:visible")
            for nav in nav_items:
                if self._should_include_element(nav):
                    elements.append({
                        "type": "nav_link",
                        "element": nav,
                        "text": self._get_element_text(nav),
                        "selector": self._get_selector(nav)
                    })
        except Exception:
            pass
        
        # Dropdowns and toggles
        try:
            dropdowns = self.page.query_selector_all("[data-toggle]:visible, [data-bs-toggle]:visible, .dropdown-toggle:visible")
            for dd in dropdowns:
                if self._should_include_element(dd):
                    elements.append({
                        "type": "dropdown",
                        "element": dd,
                        "text": self._get_element_text(dd),
                        "selector": self._get_selector(dd)
                    })
        except Exception:
            pass
        
        # Modals triggers
        try:
            modals = self.page.query_selector_all("[data-modal]:visible, [data-bs-target^='#']:visible")
            for modal in modals:
                if self._should_include_element(modal):
                    elements.append({
                        "type": "modal_trigger",
                        "element": modal,
                        "text": self._get_element_text(modal),
                        "selector": self._get_selector(modal)
                    })
        except Exception:
            pass
        
        return elements
    
    def _should_test_element(self, element) -> bool:
        """Check if element should be tested (not in excluded list)."""
        for selector in config.EXCLUDED_ELEMENT_SELECTORS:
            try:
                if element.evaluate(f"el => el.matches('{selector}')"):
                    return False
            except Exception:
                continue
        return True
    
    def _get_element_text(self, element) -> str:
        """Get readable text from element."""
        try:
            # Try inner text
            text = element.inner_text()
            if text and text.strip():
                return text.strip()[:100]

            # Try aria-label
            aria = element.get_attribute("aria-label")
            if aria:
                return aria.strip()[:100]

            # Try aria-labelledby
            try:
                labelled = element.get_attribute("aria-labelledby")
                if labelled:
                    label_text = element.evaluate(
                        """
                        (el) => {
                            const ids = (el.getAttribute('aria-labelledby') || '').split(/\s+/).filter(Boolean);
                            if (!ids.length) return '';
                            const parts = ids.map(id => {
                                const target = document.getElementById(id);
                                return target ? (target.innerText || target.textContent || '').trim() : '';
                            }).filter(Boolean);
                            return parts.join(' ');
                        }
                        """
                    )
                    if label_text:
                        return label_text[:100]
            except Exception:
                pass

            # Try text content
            try:
                text_content = element.evaluate("el => (el.textContent || '').trim()")
                if text_content:
                    return text_content[:100]
            except Exception:
                pass

            # Try value
            value = element.get_attribute("value")
            if value:
                return value[:100]
            
            # Try placeholder
            placeholder = element.get_attribute("placeholder")
            if placeholder:
                return placeholder[:100]
            
            # Try title
            title = element.get_attribute("title")
            if title:
                return title[:100]

            # Try name attribute
            name_attr = element.get_attribute("name")
            if name_attr:
                return name_attr[:100]

            # Try alt text
            alt = element.get_attribute("alt")
            if alt:
                return alt[:100]

            # Try data-testid
            testid = element.get_attribute("data-testid")
            if testid:
                return testid[:100]
            
            return "[No text]"
        except Exception:
            return "[Unknown]"
    
    def _get_selector(self, element) -> str:
        """Generate a selector for the element."""
        try:
            # Try ID
            elem_id = element.get_attribute("id")
            if elem_id:
                return f"#{elem_id}"
            
            # Try data-testid
            testid = element.get_attribute("data-testid")
            if testid:
                return f"[data-testid='{testid}']"
            
            # Try class + text combination
            classes = element.get_attribute("class")
            text = self._get_element_text(element)
            if classes and text != "[No text]":
                main_class = classes.split()[0] if classes else ""
                return f".{main_class}:has-text('{text[:30]}')"
            
            # Fallback to tag name
            tag = element.evaluate("el => el.tagName.toLowerCase()")
            return tag
        except Exception:
            return "[unknown]"
    
    def clear_errors(self):
        """Clear collected errors (call before testing a new page)."""
        self.network_errors = []
        self.console_errors = []
    
    def get_collected_errors(self) -> Tuple[List[NetworkError], List[ConsoleError]]:
        """Get collected errors."""
        return self.network_errors.copy(), self.console_errors.copy()
