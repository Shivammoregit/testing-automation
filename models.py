"""
Data models for the automated testing tool.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from enum import Enum


class TestStatus(Enum):
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"


class ErrorType(Enum):
    NETWORK_ERROR = "network_error"
    CONSOLE_ERROR = "console_error"
    ELEMENT_ERROR = "element_error"
    PAGE_ERROR = "page_error"
    TIMEOUT_ERROR = "timeout_error"


@dataclass
class NetworkError:
    """Represents a network request/response error."""
    url: str
    method: str
    status_code: int
    status_text: str
    request_headers: dict = field(default_factory=dict)
    response_headers: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    # Explanation fields
    explanation_title: str = ""
    explanation_text: str = ""
    suggestion: str = ""
    severity: str = "medium"


@dataclass
class ConsoleError:
    """Represents a browser console error."""
    message: str
    error_type: str
    source: str = ""
    line_number: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    # Explanation fields
    explanation_title: str = ""
    explanation_text: str = ""
    suggestion: str = ""
    severity: str = "medium"


@dataclass
class ElementTest:
    """Represents a test performed on an element."""
    element_type: str  # button, link, input, etc.
    element_text: str
    element_selector: str
    action: str  # click, hover, fill, etc.
    status: TestStatus
    error_message: str = ""
    screenshot_path: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    # Explanation fields
    explanation_title: str = ""
    explanation_text: str = ""
    suggestion: str = ""
    severity: str = "medium"


@dataclass
class PageTest:
    """Represents all tests performed on a single page."""
    url: str
    title: str
    status: TestStatus
    load_time_ms: float = 0
    screenshot_path: str = ""
    network_errors: List[NetworkError] = field(default_factory=list)
    console_errors: List[ConsoleError] = field(default_factory=list)
    element_tests: List[ElementTest] = field(default_factory=list)
    discovered_links: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    # Crawl path info
    discovered_from: str = ""  # The URL from which this page was discovered
    crawl_depth: int = 0  # How many links deep from the start page
    
    @property
    def total_elements_tested(self) -> int:
        return len(self.element_tests)
    
    @property
    def elements_passed(self) -> int:
        return len([e for e in self.element_tests if e.status == TestStatus.PASSED])
    
    @property
    def elements_failed(self) -> int:
        return len([e for e in self.element_tests if e.status == TestStatus.FAILED])
    
    @property
    def has_errors(self) -> bool:
        return len(self.network_errors) > 0 or len(self.console_errors) > 0 or self.elements_failed > 0


@dataclass
class CrawlPathStep:
    """Represents a step in the crawl path."""
    step_number: int
    url: str
    title: str
    discovered_from: str
    status: TestStatus
    links_found: int = 0


@dataclass
class TestSession:
    """Represents an entire testing session."""
    website_url: str
    start_time: str = field(default_factory=lambda: datetime.now().isoformat())
    end_time: str = ""
    pages_tested: List[PageTest] = field(default_factory=list)
    crawl_path: List[CrawlPathStep] = field(default_factory=list)  # Ordered list of visited pages
    
    @property
    def total_pages(self) -> int:
        return len(self.pages_tested)
    
    @property
    def pages_with_errors(self) -> int:
        return len([p for p in self.pages_tested if p.has_errors])
    
    @property
    def total_network_errors(self) -> int:
        return sum(len(p.network_errors) for p in self.pages_tested)
    
    @property
    def total_console_errors(self) -> int:
        return sum(len(p.console_errors) for p in self.pages_tested)
    
    @property
    def total_element_tests(self) -> int:
        return sum(p.total_elements_tested for p in self.pages_tested)
    
    @property
    def total_element_failures(self) -> int:
        return sum(p.elements_failed for p in self.pages_tested)
    
    @property
    def duration_seconds(self) -> float:
        if not self.end_time:
            return 0
        start = datetime.fromisoformat(self.start_time)
        end = datetime.fromisoformat(self.end_time)
        return (end - start).total_seconds()
