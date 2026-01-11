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
        
        # Make screenshot paths relative for the HTML report
        for page in session.pages_tested:
            for test in page.element_tests:
                if test.screenshot_path:
                    test.screenshot_path = os.path.relpath(
                        test.screenshot_path, 
                        self.output_folder
                    )
        
        html_content = template.render(session=session)
        
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
