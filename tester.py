"""
Element tester module - tests interactive elements and captures failures.
"""

import os
import time
from datetime import datetime
from typing import Optional
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeout
import config
from models import ElementTest, TestStatus


class ElementTester:
    """Tests interactive elements on a page."""
    
    def __init__(self, page: Page, output_folder: str):
        self.page = page
        self.output_folder = output_folder
        self.screenshots_folder = os.path.join(output_folder, "screenshots")
        os.makedirs(self.screenshots_folder, exist_ok=True)
    
    def _take_screenshot(self, name: str) -> str:
        """Take a screenshot and return the path."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{name}_{timestamp}.png"
        filepath = os.path.join(self.screenshots_folder, filename)
        
        try:
            self.page.screenshot(
                path=filepath,
                full_page=config.SCREENSHOT_FULL_PAGE
            )
            return filepath
        except Exception as e:
            print(f"Failed to take screenshot: {e}")
            return ""

    def take_page_screenshot(self, name: str) -> str:
        """Take a screenshot of the current page."""
        return self._take_screenshot(name)

    def _ensure_interactable(self, element) -> bool:
        """Best-effort checks to reduce flaky interactions."""
        try:
            element.wait_for_element_state("visible", timeout=config.ELEMENT_TIMEOUT)
            element.wait_for_element_state("stable", timeout=config.ELEMENT_TIMEOUT)
        except Exception:
            return False
        return True

    def _maybe_go_back(self, initial_url: str):
        """Return to the initial URL when a navigation occurs."""
        try:
            if self.page.url != initial_url:
                self.page.go_back(wait_until=config.NAVIGATION_WAIT_UNTIL, timeout=config.NAVIGATION_TIMEOUT)
                time.sleep(config.ELEMENT_INTERACTION_DELAY)
        except Exception:
            pass

    def _click_with_optional_popup(self, element):
        """Click and handle a popup if one appears."""
        try:
            with self.page.expect_popup(timeout=config.POPUP_WAIT_TIMEOUT_MS) as popup_info:
                element.click(timeout=config.ELEMENT_TIMEOUT)
            popup = popup_info.value
            try:
                popup.wait_for_load_state("domcontentloaded", timeout=config.NAVIGATION_TIMEOUT)
                popup.close()
            except Exception:
                pass
            return True
        except PlaywrightTimeout:
            return True
        except Exception:
            return False
    
    def test_button(self, element_info: dict) -> ElementTest:
        """Test a button element."""
        element = element_info["element"]
        text = element_info["text"]
        selector = element_info["selector"]
        
        test_result = ElementTest(
            element_type="button",
            element_text=text,
            element_selector=selector,
            action="click",
            status=TestStatus.PASSED
        )
        
        try:
            # Store current URL to detect navigation
            current_url = self.page.url
            
            # Check if element is visible and enabled
            if not element.is_visible():
                test_result.status = TestStatus.SKIPPED
                test_result.error_message = "Element not visible"
                return test_result
            
            if not element.is_enabled():
                test_result.status = TestStatus.SKIPPED
                test_result.error_message = "Element not enabled"
                return test_result

            if not self._ensure_interactable(element):
                test_result.status = TestStatus.SKIPPED
                test_result.error_message = "Element not interactable"
                return test_result
            
            # Try to click
            if not self._click_with_optional_popup(element):
                raise Exception("Click failed")
            
            # Wait a moment for any reactions
            time.sleep(config.ELEMENT_INTERACTION_DELAY)
            
            # Check if we navigated away
            self._maybe_go_back(current_url)
            
            # Check for any error dialogs/modals
            if self._check_error_dialog():
                test_result.status = TestStatus.FAILED
                test_result.error_message = "Error dialog appeared after click"
                if config.SCREENSHOT_ON_ERROR:
                    test_result.screenshot_path = self._take_screenshot(f"button_error_{text[:20]}")
                self._close_dialogs()
            
        except PlaywrightTimeout:
            test_result.status = TestStatus.FAILED
            test_result.error_message = "Click action timed out"
            if config.SCREENSHOT_ON_ERROR:
                test_result.screenshot_path = self._take_screenshot(f"button_timeout_{text[:20]}")
        except Exception as e:
            test_result.status = TestStatus.FAILED
            test_result.error_message = str(e)[:500]
            if config.SCREENSHOT_ON_ERROR:
                test_result.screenshot_path = self._take_screenshot(f"button_error_{text[:20]}")
        
        return test_result
    
    def test_link(self, element_info: dict) -> ElementTest:
        """Test a link element."""
        element = element_info["element"]
        text = element_info["text"]
        selector = element_info["selector"]
        
        test_result = ElementTest(
            element_type="link",
            element_text=text,
            element_selector=selector,
            action="click",
            status=TestStatus.PASSED
        )
        
        try:
            if not element.is_visible():
                test_result.status = TestStatus.SKIPPED
                test_result.error_message = "Element not visible"
                return test_result

            if not self._ensure_interactable(element):
                test_result.status = TestStatus.SKIPPED
                test_result.error_message = "Element not interactable"
                return test_result
            
            href = element.get_attribute("href")
            current_url = self.page.url
            
            # Click the link
            if not self._click_with_optional_popup(element):
                raise Exception("Click failed")
            time.sleep(config.ELEMENT_INTERACTION_DELAY)
            
            # Wait for navigation
            try:
                self.page.wait_for_load_state(config.NAVIGATION_WAIT_UNTIL, timeout=config.NAVIGATION_TIMEOUT)
            except Exception:
                pass
            
            # Go back
            self._maybe_go_back(current_url)
            
        except PlaywrightTimeout:
            test_result.status = TestStatus.FAILED
            test_result.error_message = "Navigation timed out"
            if config.SCREENSHOT_ON_ERROR:
                test_result.screenshot_path = self._take_screenshot(f"link_timeout_{text[:20]}")
        except Exception as e:
            test_result.status = TestStatus.FAILED
            test_result.error_message = str(e)[:500]
            if config.SCREENSHOT_ON_ERROR:
                test_result.screenshot_path = self._take_screenshot(f"link_error_{text[:20]}")
        
        return test_result
    
    def test_input(self, element_info: dict) -> ElementTest:
        """Test an input element."""
        element = element_info["element"]
        text = element_info["text"]
        selector = element_info["selector"]
        
        test_result = ElementTest(
            element_type="input",
            element_text=text,
            element_selector=selector,
            action="focus",
            status=TestStatus.PASSED
        )
        
        try:
            if not element.is_visible():
                test_result.status = TestStatus.SKIPPED
                test_result.error_message = "Element not visible"
                return test_result
            
            # Get input type
            input_type = element.get_attribute("type") or "text"
            
            # Focus the element
            element.focus()
            time.sleep(0.2)
            
            # Don't actually fill - just verify it's interactable
            if element.is_editable():
                test_result.action = "focus (editable)"
            else:
                test_result.action = "focus (read-only)"
            
        except Exception as e:
            test_result.status = TestStatus.FAILED
            test_result.error_message = str(e)[:500]
            if config.SCREENSHOT_ON_ERROR:
                test_result.screenshot_path = self._take_screenshot(f"input_error_{text[:20]}")
        
        return test_result
    
    def test_dropdown(self, element_info: dict) -> ElementTest:
        """Test a dropdown element."""
        element = element_info["element"]
        text = element_info["text"]
        selector = element_info["selector"]
        
        test_result = ElementTest(
            element_type="dropdown",
            element_text=text,
            element_selector=selector,
            action="click",
            status=TestStatus.PASSED
        )
        
        try:
            if not element.is_visible():
                test_result.status = TestStatus.SKIPPED
                test_result.error_message = "Element not visible"
                return test_result
            
            # Click to open
            element.click(timeout=config.ELEMENT_TIMEOUT)
            time.sleep(config.ELEMENT_INTERACTION_DELAY)
            
            # Click again to close (or click elsewhere)
            try:
                element.click(timeout=config.ELEMENT_TIMEOUT)
            except Exception:
                # Click on body to close
                self.page.click("body", position={"x": 10, "y": 10})
            
            time.sleep(config.ELEMENT_INTERACTION_DELAY)
            
        except Exception as e:
            test_result.status = TestStatus.FAILED
            test_result.error_message = str(e)[:500]
            if config.SCREENSHOT_ON_ERROR:
                test_result.screenshot_path = self._take_screenshot(f"dropdown_error_{text[:20]}")
        
        return test_result
    
    def test_element(self, element_info: dict) -> ElementTest:
        """Test any element based on its type."""
        elem_type = element_info["type"]
        
        if elem_type == "button":
            return self.test_button(element_info)
        elif elem_type in ["nav_link", "clickable"]:
            return self.test_link(element_info)
        elif elem_type == "input":
            return self.test_input(element_info)
        elif elem_type in ["dropdown", "modal_trigger"]:
            return self.test_dropdown(element_info)
        else:
            # Generic test - just try to click
            return self.test_button(element_info)
    
    def _check_error_dialog(self) -> bool:
        """Check if an error dialog is visible."""
        error_selectors = [
            ".error-modal:visible",
            ".error-dialog:visible",
            "[role='alertdialog']:visible",
            ".alert-danger:visible",
            ".toast-error:visible",
            ".notification-error:visible"
        ]
        
        for selector in error_selectors:
            try:
                if self.page.query_selector(selector):
                    return True
            except Exception:
                continue
        
        return False
    
    def _close_dialogs(self):
        """Try to close any open dialogs."""
        close_selectors = [
            ".modal .close",
            ".modal .btn-close",
            "[aria-label='Close']",
            ".dialog-close",
            ".modal-close"
        ]
        
        for selector in close_selectors:
            try:
                btn = self.page.query_selector(selector)
                if btn and btn.is_visible():
                    btn.click()
                    time.sleep(0.3)
                    break
            except Exception:
                continue
        
        # Press Escape as fallback
        try:
            self.page.keyboard.press("Escape")
        except Exception:
            pass
