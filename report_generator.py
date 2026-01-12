"""
HTML Report Generator - creates beautiful test reports.
"""

import os
from datetime import datetime
from jinja2 import Template
from models import TestSession, TestStatus


class ReportGenerator:
    """Generates HTML test reports."""
    
    def __init__(self, output_folder: str):
        self.output_folder = output_folder
        os.makedirs(output_folder, exist_ok=True)
    
    def _get_template(self) -> str:
        return open(os.path.join(os.path.dirname(__file__), "report_template.html"), "r", encoding="utf-8").read()
    
    def generate_report(self, session: TestSession) -> str:
        """Generate an HTML report for the test session."""
        template = Template(self._get_template())

        module_summary = {}
        module_errors = {}
        for page in session.pages_tested:
            module_name = page.module or "Uncategorized"
            if module_name not in module_summary:
                module_summary[module_name] = {
                    "pages": 0,
                    "errors": 0,
                    "network_errors": 0,
                    "console_errors": 0,
                    "element_failures": 0,
                }
            if module_name not in module_errors:
                module_errors[module_name] = {
                    "network": [],
                    "console": [],
                    "element": [],
                }
            module_summary[module_name]["pages"] += 1
            if page.has_errors:
                module_summary[module_name]["errors"] += 1
            module_summary[module_name]["network_errors"] += len(page.network_errors)
            module_summary[module_name]["console_errors"] += len(page.console_errors)
            module_summary[module_name]["element_failures"] += page.elements_failed

            console_logs = [err.message for err in page.console_errors]
            for error in page.network_errors:
                module_errors[module_name]["network"].append({
                    "page_url": page.url,
                    "page_title": page.title,
                    "status_code": error.status_code,
                    "status_text": error.status_text,
                    "method": error.method,
                    "url": error.url,
                    "severity": error.severity,
                    "explanation_title": error.explanation_title,
                    "explanation_text": error.explanation_text,
                    "simple_explanation": error.simple_explanation,
                    "suggestion": error.suggestion,
                    "screenshot_path": error.screenshot_path,
                    "console_logs": console_logs,
                })
            for error in page.console_errors:
                module_errors[module_name]["console"].append({
                    "page_url": page.url,
                    "page_title": page.title,
                    "error_type": error.error_type,
                    "message": error.message,
                    "source": error.source,
                    "line_number": error.line_number,
                    "severity": error.severity,
                    "explanation_title": error.explanation_title,
                    "explanation_text": error.explanation_text,
                    "simple_explanation": error.simple_explanation,
                    "suggestion": error.suggestion,
                    "screenshot_path": error.screenshot_path,
                    "console_logs": console_logs,
                })
            for test in page.element_tests:
                if test.status == TestStatus.FAILED:
                    module_errors[module_name]["element"].append({
                        "page_url": page.url,
                        "page_title": page.title,
                        "element_type": test.element_type,
                        "element_text": test.element_text,
                        "element_selector": test.element_selector,
                        "error_message": test.error_message,
                    "severity": test.severity,
                    "explanation_title": test.explanation_title,
                    "explanation_text": test.explanation_text,
                    "simple_explanation": test.simple_explanation,
                    "suggestion": test.suggestion,
                    "screenshot_path": test.screenshot_path,
                    "console_logs": console_logs,
                })
        
        # Make screenshot paths relative for the HTML report
        for page in session.pages_tested:
            for test in page.element_tests:
                if test.screenshot_path:
                    test.screenshot_path = os.path.relpath(
                        test.screenshot_path, 
                        self.output_folder
                    )
            for error in page.network_errors:
                if error.screenshot_path:
                    error.screenshot_path = os.path.relpath(
                        error.screenshot_path,
                        self.output_folder
                    )
            for error in page.console_errors:
                if error.screenshot_path:
                    error.screenshot_path = os.path.relpath(
                        error.screenshot_path,
                        self.output_folder
                    )

        html_content = template.render(
            session=session,
            module_summary=module_summary,
            module_errors=module_errors
        )
        
        report_path = os.path.join(self.output_folder, "test_report.html")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        return report_path
    
    def save_session_data(self, session: TestSession) -> str:
        """Save session data as JSON for later analysis."""
        import json
        
        def convert_to_dict(obj):
            if hasattr(obj, 'value'):
                return obj.value
            elif hasattr(obj, '__dict__'):
                return {k: convert_to_dict(v) for k, v in obj.__dict__.items()}
            elif isinstance(obj, list):
                return [convert_to_dict(item) for item in obj]
            elif isinstance(obj, dict):
                return {k: convert_to_dict(v) for k, v in obj.items()}
            return obj
        
        session_dict = convert_to_dict(session)
        
        json_path = os.path.join(self.output_folder, "test_data.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(session_dict, f, indent=2, default=str)
        
        return json_path
