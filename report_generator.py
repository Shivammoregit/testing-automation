"""
HTML Report Generator - creates beautiful test reports.
"""

import os
import html
import json
import re
import time
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import datetime
from urllib.parse import urlparse
from jinja2 import Template
import config
from models import TestSession, TestStatus


def _normalize_severity(raw: str) -> str:
    mapping = {
        "low": "low",
        "medium": "medium",
        "high": "risk",
        "critical": "high-risk",
    }
    if not raw:
        return "medium"
    return mapping.get(raw.lower(), "medium")


def _network_severity(status_code: int, raw: str) -> str:
    if status_code is None:
        return _normalize_severity(raw)
    if status_code >= 500:
        return "high-risk"
    if status_code in (401, 403):
        return "risk"
    if status_code in (400, 404, 405):
        return "medium"
    return _normalize_severity(raw)


def _module_seed_paths(module_name: str) -> list[str]:
    paths = []
    for seed in config.MODULES.get(module_name, []):
        parsed = urlparse(seed)
        path = parsed.path.rstrip("/")
        if path:
            paths.append(path)
    return paths


def _submodule_label(module_name: str, url: str) -> str:
    parsed = urlparse(url)
    url_path = parsed.path.rstrip("/")
    best_match = ""
    for seed_path in _module_seed_paths(module_name):
        if url_path.startswith(seed_path) and len(seed_path) > len(best_match):
            best_match = seed_path
    if not best_match:
        return "root"
    relative = url_path[len(best_match):].lstrip("/")
    if not relative:
        return "root"
    return relative.split("/")[0]


def _element_label(test) -> str:
    text = (test.element_text or "").strip()
    if not text or text in ("[No text]", "[Unknown]"):
        text = (test.element_selector or "").strip()
    if not text:
        text = test.element_type
    return text


_SEVERITY_RANK = {
    "low": 1,
    "medium": 2,
    "risk": 3,
    "high-risk": 4,
}


def _severity_rank(level: str) -> int:
    return _SEVERITY_RANK.get(level, 0)


def _max_severity(current: str, candidate: str) -> str:
    if _severity_rank(candidate) > _severity_rank(current):
        return candidate
    return current


def _status_value(status) -> str:
    return status.value if hasattr(status, "value") else str(status)


def _ensure_severities(session: TestSession) -> None:
    for page in session.pages_tested:
        for error in page.network_errors:
            error.severity = _network_severity(error.status_code, error.severity)
        for error in page.console_errors:
            error.severity = _normalize_severity(error.severity)
        for test in page.element_tests:
            test.severity = _normalize_severity(test.severity)


def _normalize_url_for_group(raw_url: str) -> str:
    if not raw_url:
        return "unknown"
    parsed = urlparse(raw_url)
    if not parsed.scheme and not parsed.netloc:
        base = raw_url.split("?")[0].rstrip("/")
        return base or raw_url
    base = f"{parsed.scheme}://{parsed.netloc}"
    path = parsed.path.rstrip("/")
    if not path:
        return base + "/"
    return base + path


def _unique_ordered(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for item in values:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def _compact_text(value: str) -> str:
    if not value:
        return ""
    return " ".join(str(value).split())


def _truncate_text(value: str, max_len: int = 160) -> str:
    text = _compact_text(value)
    if len(text) <= max_len:
        return text
    return text[:max_len - 3].rstrip() + "..."


def _format_examples(values: list[str], limit: int = 5) -> str:
    values = [v for v in _unique_ordered(values) if v]
    if not values:
        return "none"
    if len(values) <= limit:
        return ", ".join(values)
    return ", ".join(values[:limit]) + f", and {len(values) - limit} more"


def _join_examples(values: list[str], limit=None) -> str:
    values = [v for v in values if v]
    if not values:
        return "none"
    if limit is None:
        return ", ".join(values)
    return _format_examples(values, limit=limit)


def _sanitize_ascii(text: str) -> str:
    return text.encode("ascii", "replace").decode("ascii")


def _session_to_dict(session: TestSession) -> dict:
    def convert_to_dict(obj):
        if hasattr(obj, "value"):
            return obj.value
        if hasattr(obj, "__dict__"):
            return {k: convert_to_dict(v) for k, v in obj.__dict__.items()}
        if isinstance(obj, list):
            return [convert_to_dict(item) for item in obj]
        if isinstance(obj, dict):
            return {k: convert_to_dict(v) for k, v in obj.items()}
        return obj

    return convert_to_dict(session)


def _read_env_value(path: str, keys: list[str]) -> str:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            for line in handle:
                stripped = line.strip()
                if not stripped or stripped.startswith("#") or "=" not in stripped:
                    continue
                key, value = stripped.split("=", 1)
                key = key.strip()
                if key not in keys:
                    continue
                value = value.strip().strip("'").strip('"')
                if value:
                    return value
    except FileNotFoundError:
        return ""
    except Exception:
        return ""
    return ""


def _get_gemini_api_key() -> str:
    for key_name in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
        value = os.environ.get(key_name)
        if value:
            return value.strip()
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    return _read_env_value(env_path, ["GEMINI_API_KEY", "GOOGLE_API_KEY"])


def _build_human_summary_prompt(summary_json: str) -> str:
    return (
       f'''You are a senior QA engineer and software debugging expert.
You will receive a JSON-based automated testing report as input.

Your task is to:
1. Identify and classify the type of error(s) present (e.g. UI failure, network issue, API error, timeout, assertion failure, authentication issue, environment/configuration issue).
2. Determine exactly WHERE the error occurred:
   - Website or domain
   - Page or endpoint (URL/path)
   - Test step or action (if available)
3. Explain WHAT happened in simple, non-technical language first, followed by a technical explanation.
4. Summarize the sequence of events leading up to the failure.
5. Identify the most likely ROOT CAUSE(s) based on the report data.
6. Highlight WHAT ENGINEERS SHOULD CHECK FIRST to debug and fix the issue.
7. Provide clear, actionable RECOMMENDATIONS to resolve or prevent the issue in future runs.

Output your response in the following structured format:

---
### 🔍 Error Overview
- Error type:
- Severity:
- Affected system/page:

### 📍 Where It Happened
- Website:
- Page / Endpoint:
- Test step / Action:

### 🧠 What Happened (Summary)
(Brief, human-readable explanation)

### ⚙️ Technical Details
(Technical explanation referencing error codes, logs, stack traces, or failed assertions)

### 🧩 Likely Root Cause(s)
- 

### 🛠️ What to Check & Fix
- 

### ✅ Recommended Next Steps
- 
---

Rules:
- Base your analysis ONLY on the provided JSON report.
- Do not invent missing data; if something is unclear, explicitly state it.
- Be concise but thorough.
- Assume the audience includes QA engineers, developers, and product managers.
- Prioritize clarity and actionability.
The output should be in markdown format.
JSON TEST REPORT INPUT:
 {summary_json}'''
      
    )


def _markdown_to_text(markdown: str) -> str:
    lines = []
    in_code_block = False
    for raw in markdown.splitlines():
        line = raw.rstrip()
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            lines.append(line)
            continue
        line = re.sub(r"^\s*#+\s*", "", line)
        line = re.sub(r"`([^`]+)`", r"\1", line)
        lines.append(line)
    text = "\n".join(lines).strip()
    if text:
        text += "\n"
    return text


def _extract_http_error_detail(body: str) -> str:
    if not body:
        return ""
    detail = ""
    try:
        data = json.loads(body)
        detail = data.get("error", {}).get("message") or ""
        if not detail:
            detail = body
    except Exception:
        detail = body
    return _truncate_text(_compact_text(detail), 240)


def _call_gemini_api(prompt: str, api_key: str) -> tuple[str, str]:
    model = getattr(config, "GEMINI_MODEL", "gemini-2.5")
    api_version = getattr(config, "GEMINI_API_VERSION", "v1")
    timeout = getattr(config, "GEMINI_TIMEOUT_SECONDS", 30)
    url = (
        f"https://generativelanguage.googleapis.com/{api_version}/models/"
        f"{model}:generateContent?key={api_key}"
    )
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
    }
    retry_delays = [2, 5, 10, 20]
    last_error = "Unexpected error."
    for attempt in range(len(retry_delays) + 1):
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
            candidates = data.get("candidates", [])
            if not candidates:
                return "", "No candidates in response."
            parts = candidates[0].get("content", {}).get("parts", [])
            text = "".join(part.get("text", "") for part in parts)
            if not text.strip():
                return "", "Empty response text."
            return text, ""
        except urllib.error.HTTPError as exc:
            body = ""
            try:
                body = exc.read().decode("utf-8", errors="replace")
            except Exception:
                body = ""
            detail = _extract_http_error_detail(body)
            message = f"HTTP error {exc.code}."
            if detail:
                message = f"{message} {detail}"
            last_error = message
            if exc.code in (429, 503) and attempt < len(retry_delays):
                time.sleep(retry_delays[attempt])
                continue
            return "", message
        except urllib.error.URLError:
            last_error = "Network error."
            return "", last_error
        except Exception:
            last_error = "Unexpected error."
            return "", last_error
    return "", last_error


def _markdown_to_html(markdown: str) -> str:
    def _inline(text: str) -> str:
        escaped = html.escape(text)
        return re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)

    lines = markdown.splitlines()
    html_lines = []
    in_list = False

    for raw in lines:
        line = raw.rstrip()
        if not line.strip():
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            continue

        if line.startswith("### "):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<h3>{_inline(line[4:])}</h3>")
            continue
        if line.startswith("## "):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<h2>{_inline(line[3:])}</h2>")
            continue
        if line.startswith("# "):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<h1>{_inline(line[2:])}</h1>")
            continue
        if line.startswith("- "):
            if not in_list:
                html_lines.append("<ul>")
                in_list = True
            html_lines.append(f"<li>{_inline(line[2:])}</li>")
            continue

        if in_list:
            html_lines.append("</ul>")
            in_list = False
        html_lines.append(f"<p>{_inline(line)}</p>")

    if in_list:
        html_lines.append("</ul>")

    return "\n".join(html_lines)


def _build_summary_markdown(session: TestSession) -> str:
    _ensure_severities(session)

    def _is_failed(status) -> bool:
        return _status_value(status) == TestStatus.FAILED.value

    def _format_group_pages(pages: set[str], limit: int = 4) -> str:
        return _format_examples(sorted(pages), limit=limit)

    page_failures = [p for p in session.pages_tested if _is_failed(p.status)]
    page_failure_count = len(page_failures)
    network_count = sum(len(p.network_errors) for p in session.pages_tested)
    console_count = sum(len(p.console_errors) for p in session.pages_tested)
    element_failure_count = sum(
        1 for p in session.pages_tested for t in p.element_tests if _is_failed(t.status)
    )
    total_issues = page_failure_count + network_count + console_count + element_failure_count
    pages_with_issues = sum(
        1 for p in session.pages_tested if p.has_errors or _is_failed(p.status)
    )

    severity_counts = {
        "high-risk": 0,
        "risk": 0,
        "medium": 0,
        "low": 0,
        "unclassified": 0,
    }

    def _count_severity(level: str) -> None:
        key = level if level in severity_counts else "unclassified"
        severity_counts[key] += 1

    for page in session.pages_tested:
        for error in page.network_errors:
            _count_severity(error.severity)
        for error in page.console_errors:
            _count_severity(error.severity)
        for test in page.element_tests:
            if _is_failed(test.status):
                _count_severity(test.severity)
    severity_counts["unclassified"] += page_failure_count

    module_failure_counts = defaultdict(int)
    zero_load_count = 0
    empty_title_count = 0
    failure_examples = []
    for page in page_failures:
        module_failure_counts[page.module or "Uncategorized"] += 1
        if not page.title:
            empty_title_count += 1
        if not page.load_time_ms or page.load_time_ms <= 1:
            zero_load_count += 1
        failure_examples.append(_normalize_url_for_group(page.url))

    network_groups = {}
    console_groups = {}
    element_groups = {}
    status_endpoints = defaultdict(set)
    console_messages = []
    element_error_messages = []

    def _new_module_bucket():
        return {
            "pages": 0,
            "page_failures": 0,
            "network_errors": 0,
            "console_errors": 0,
            "element_failures": 0,
            "failure_urls": set(),
            "network_groups": {},
            "console_groups": {},
            "element_groups": {},
        }

    module_stats = defaultdict(_new_module_bucket)

    for page in session.pages_tested:
        module_name = page.module or "Uncategorized"
        bucket = module_stats[module_name]
        bucket["pages"] += 1
        if _is_failed(page.status):
            bucket["page_failures"] += 1
            bucket["failure_urls"].add(_normalize_url_for_group(page.url))

        for error in page.network_errors:
            url = _normalize_url_for_group(error.url)
            key = (error.method or "", url, error.status_code, error.status_text or "")
            entry = network_groups.get(key)
            if not entry:
                entry = {
                    "count": 0,
                    "method": error.method or "",
                    "url": url,
                    "status_code": error.status_code,
                    "status_text": error.status_text or "",
                    "severity": error.severity,
                    "pages": set(),
                }
                network_groups[key] = entry
            entry["count"] += 1
            entry["pages"].add(page.url)
            entry["severity"] = _max_severity(entry["severity"], error.severity)

            if error.status_code is not None:
                status_endpoints[error.status_code].add(url)

            bucket["network_errors"] += 1
            mod_entry = bucket["network_groups"].get(key)
            if not mod_entry:
                mod_entry = {
                    "count": 0,
                    "method": error.method or "",
                    "url": url,
                    "status_code": error.status_code,
                    "status_text": error.status_text or "",
                    "severity": error.severity,
                    "pages": set(),
                }
                bucket["network_groups"][key] = mod_entry
            mod_entry["count"] += 1
            mod_entry["pages"].add(page.url)
            mod_entry["severity"] = _max_severity(mod_entry["severity"], error.severity)

        for error in page.console_errors:
            key = (error.message or "", error.source or "", error.line_number or 0)
            entry = console_groups.get(key)
            if not entry:
                entry = {
                    "count": 0,
                    "message": error.message or "",
                    "source": error.source or "unknown",
                    "line_number": error.line_number or 0,
                    "severity": error.severity,
                    "pages": set(),
                }
                console_groups[key] = entry
            entry["count"] += 1
            entry["pages"].add(page.url)
            entry["severity"] = _max_severity(entry["severity"], error.severity)
            console_messages.append(error.message or "")

            bucket["console_errors"] += 1
            mod_entry = bucket["console_groups"].get(key)
            if not mod_entry:
                mod_entry = {
                    "count": 0,
                    "message": error.message or "",
                    "source": error.source or "unknown",
                    "line_number": error.line_number or 0,
                    "severity": error.severity,
                    "pages": set(),
                }
                bucket["console_groups"][key] = mod_entry
            mod_entry["count"] += 1
            mod_entry["pages"].add(page.url)
            mod_entry["severity"] = _max_severity(mod_entry["severity"], error.severity)

        for test in page.element_tests:
            if not _is_failed(test.status):
                continue
            label = _element_label(test)
            key = (test.element_type or "", test.action or "", label, test.error_message or "")
            entry = element_groups.get(key)
            if not entry:
                entry = {
                    "count": 0,
                    "element_type": test.element_type or "element",
                    "action": test.action or "action",
                    "label": label,
                    "error_message": test.error_message or "",
                    "severity": test.severity,
                    "pages": set(),
                }
                element_groups[key] = entry
            entry["count"] += 1
            entry["pages"].add(page.url)
            entry["severity"] = _max_severity(entry["severity"], test.severity)
            element_error_messages.append(test.error_message or "")

            bucket["element_failures"] += 1
            mod_entry = bucket["element_groups"].get(key)
            if not mod_entry:
                mod_entry = {
                    "count": 0,
                    "element_type": test.element_type or "element",
                    "action": test.action or "action",
                    "label": label,
                    "error_message": test.error_message or "",
                    "severity": test.severity,
                    "pages": set(),
                }
                bucket["element_groups"][key] = mod_entry
            mod_entry["count"] += 1
            mod_entry["pages"].add(page.url)
            mod_entry["severity"] = _max_severity(mod_entry["severity"], test.severity)

    def _sort_groups(groups: dict) -> list[dict]:
        return sorted(
            groups.values(),
            key=lambda g: (-g["count"], -_severity_rank(g["severity"]))
        )

    def _summarize_network_groups(groups: dict, limit: int = 3) -> str:
        if not groups:
            return "none"
        entries = _sort_groups(groups)
        if limit is not None:
            entries = entries[:limit]
        items = []
        for entry in entries:
            method = entry["method"] or "REQUEST"
            status_code = entry["status_code"] if entry["status_code"] is not None else "n/a"
            status_text = _truncate_text(entry["status_text"], 40)
            label = f"{method} {entry['url']} -> {status_code}"
            if status_text:
                label = f"{label} {status_text}"
            items.append(f"{label} ({entry['count']}x)")
        return _join_examples(items, limit=limit)

    def _summarize_console_groups(groups: dict, limit: int = 3) -> str:
        if not groups:
            return "none"
        entries = _sort_groups(groups)
        if limit is not None:
            entries = entries[:limit]
        items = []
        for entry in entries:
            message = _truncate_text(entry["message"], 80)
            source = _truncate_text(entry["source"], 40)
            location = source
            if entry["line_number"]:
                location = f"{location}:{entry['line_number']}" if location else str(entry["line_number"])
            label = message
            if location:
                label = f"{label} ({location})"
            items.append(f"{label} ({entry['count']}x)")
        return _join_examples(items, limit=limit)

    def _summarize_element_groups(groups: dict, limit: int = 3) -> str:
        if not groups:
            return "none"
        entries = _sort_groups(groups)
        if limit is not None:
            entries = entries[:limit]
        items = []
        for entry in entries:
            label = _truncate_text(entry["label"].replace('"', "'"), 60)
            error_message = _truncate_text(entry["error_message"], 60)
            action = entry["action"]
            element_type = entry["element_type"]
            detail = f"{element_type} {action} \"{label}\""
            if error_message:
                detail = f"{detail} -> {error_message}"
            items.append(f"{detail} ({entry['count']}x)")
        return _join_examples(items, limit=limit)

    lines = []
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    run_end = session.end_time or "n/a"
    lines.append("# Test Summary Report")
    lines.append(f"Generated: {generated_at}")
    lines.append(f"Target: {session.website_url}")
    lines.append(f"Run window: {session.start_time} - {run_end}")
    lines.append(f"Duration: {session.duration_seconds:.1f}s")
    lines.append(f"Pages tested: {session.total_pages}")
    lines.append(f"Pages with issues: {pages_with_issues}")
    lines.append("")
    lines.append("## Overall Issue Summary")
    lines.append(f"- Total issues: {total_issues}")
    lines.append(
        "- Severity counts: "
        f"high-risk={severity_counts['high-risk']}, "
        f"risk={severity_counts['risk']}, "
        f"medium={severity_counts['medium']}, "
        f"low={severity_counts['low']}, "
        f"unclassified={severity_counts['unclassified']}"
    )
    lines.append(
        "- Issue types: "
        f"page_load_failures={page_failure_count}, "
        f"network_errors={network_count}, "
        f"console_errors={console_count}, "
        f"element_failures={element_failure_count}"
    )
    lines.append("")
    lines.append("## Module-wise Errors")
    module_entries = []
    for name, data in module_stats.items():
        total = (
            data["page_failures"]
            + data["network_errors"]
            + data["console_errors"]
            + data["element_failures"]
        )
        if total == 0:
            continue
        module_entries.append((name, data, total))
    module_entries.sort(key=lambda item: (-item[2], item[0].lower()))

    if not module_entries:
        lines.append("- No module-specific errors detected.")
    else:
        lines.append("- Modules without issues are omitted.")
        for name, data, total in module_entries:
            lines.append(f"### {name}")
            lines.append(
                f"- Totals: pages_tested={data['pages']}, "
                f"issues={total}, "
                f"page_load_failures={data['page_failures']}, "
                f"network_errors={data['network_errors']}, "
                f"console_errors={data['console_errors']}, "
                f"element_failures={data['element_failures']}"
            )
            if data["page_failures"]:
                examples = _format_examples(sorted(data["failure_urls"]), limit=3)
                lines.append(f"- Example failed pages: {examples}.")
            if data["network_errors"]:
                lines.append(
                    f"- Network issues: {_summarize_network_groups(data['network_groups'], limit=None)}."
                )
            if data["console_errors"]:
                lines.append(
                    f"- Console issues: {_summarize_console_groups(data['console_groups'], limit=None)}."
                )
            if data["element_failures"]:
                lines.append(
                    f"- Element failures: {_summarize_element_groups(data['element_groups'], limit=None)}."
                )
    lines.append("")
    lines.append("## Grouped Issues")
    lines.append(f"### Page Load Failures ({page_failure_count})")
    if page_failure_count == 0:
        lines.append("- None")
    else:
        module_items = [
            f"{name} ({count})"
            for name, count in sorted(
                module_failure_counts.items(),
                key=lambda item: (-item[1], item[0].lower())
            )
        ]
        lines.append(
            f"- Common signals: empty_title={empty_title_count}, "
            f"zero_load_time={zero_load_count}."
        )
        lines.append(f"- Modules affected: {_format_examples(module_items, limit=5)}.")
        lines.append(f"- Example URLs: {_format_examples(failure_examples, limit=5)}.")

    lines.append(f"### Network Errors ({network_count})")
    if network_count == 0:
        lines.append("- None")
    else:
        for entry in _sort_groups(network_groups):
            method = entry["method"] or "REQUEST"
            status_code = entry["status_code"] if entry["status_code"] is not None else "n/a"
            status_text = _truncate_text(entry["status_text"], 60)
            sev = entry["severity"] or "unclassified"
            pages = _format_group_pages(entry["pages"])
            lines.append(
                f"- {entry['count']}x {method} {entry['url']} -> "
                f"{status_code} {status_text} [severity: {sev}]. "
                f"Affected pages: {len(entry['pages'])} (examples: {pages})."
            )

    lines.append(f"### Console Errors ({console_count})")
    if console_count == 0:
        lines.append("- None")
    else:
        for entry in _sort_groups(console_groups):
            message = _truncate_text(entry["message"], 120)
            source = _truncate_text(entry["source"], 60)
            sev = entry["severity"] or "unclassified"
            pages = _format_group_pages(entry["pages"])
            lines.append(
                f"- {entry['count']}x {message} ({source}:{entry['line_number']}) "
                f"[severity: {sev}]. Affected pages: {len(entry['pages'])} "
                f"(examples: {pages})."
            )

    lines.append(f"### Element Failures ({element_failure_count})")
    if element_failure_count == 0:
        lines.append("- None")
    else:
        for entry in _sort_groups(element_groups):
            label = _truncate_text(entry["label"].replace('"', "'"), 80)
            error_message = _truncate_text(entry["error_message"], 120)
            sev = entry["severity"] or "unclassified"
            pages = _format_group_pages(entry["pages"])
            lines.append(
                f"- {entry['count']}x {entry['element_type']} {entry['action']} "
                f"\"{label}\" -> {error_message} [severity: {sev}]. "
                f"Affected pages: {len(entry['pages'])} (examples: {pages})."
            )

    lines.append("")
    lines.append("## Areas to Review")
    review_notes = []

    def _add_note(text: str) -> None:
        if text and text not in review_notes:
            review_notes.append(text)

    if page_failure_count:
        signal_parts = []
        if empty_title_count:
            signal_parts.append(f"empty title on {empty_title_count} page(s)")
        if zero_load_count:
            signal_parts.append(f"zero load time on {zero_load_count} page(s)")
        signal_text = ", ".join(signal_parts)
        note = "Page navigation failures observed"
        if signal_text:
            note += f" ({signal_text})"
        note += ". Check route availability, redirects, and login/session state."
        _add_note(note)

        module_items = [
            f"{name} ({count})"
            for name, count in sorted(
                module_failure_counts.items(),
                key=lambda item: (-item[1], item[0].lower())
            )
        ]
        if module_items:
            _add_note(
                "Module routing or backend availability may need attention in: "
                f"{_format_examples(module_items, limit=4)}."
            )

    status_codes = list(status_endpoints.keys())
    if any(code >= 500 for code in status_codes):
        endpoints = []
        for code in sorted(status_codes):
            if code >= 500:
                endpoints.extend(sorted(status_endpoints[code]))
        _add_note(
            "Server errors (5xx) detected. Review backend logs for: "
            f"{_format_examples(endpoints, limit=4)}."
        )
    if any(code in (401, 403) for code in status_codes):
        endpoints = []
        for code in sorted(status_codes):
            if code in (401, 403):
                endpoints.extend(sorted(status_endpoints[code]))
        _add_note(
            "Auth/permission errors (401/403). Verify access control for: "
            f"{_format_examples(endpoints, limit=4)}."
        )
    if 404 in status_endpoints:
        _add_note(
            "Missing routes/resources (404). Check URL routing or resource paths for: "
            f"{_format_examples(sorted(status_endpoints[404]), limit=4)}."
        )
    if 400 in status_endpoints:
        _add_note(
            "Request validation errors (400). Verify request payloads for: "
            f"{_format_examples(sorted(status_endpoints[400]), limit=4)}."
        )

    console_text = " ".join(msg.lower() for msg in console_messages if msg)
    if "geolocation" in console_text or "location" in console_text:
        _add_note(
            "Geolocation permission handling: guard against denied access and avoid logging errors when permission is blocked."
        )
    if "typeerror" in console_text or "referenceerror" in console_text:
        _add_note(
            "JavaScript runtime errors: inspect console stack traces for the listed source files."
        )
    if "cors" in console_text:
        _add_note(
            "CORS warnings/errors: check API allowlists and preflight handling."
        )

    element_text = " ".join(msg.lower() for msg in element_error_messages if msg)
    if element_failure_count and (
        "timeout" in element_text or "not found" in element_text or "detached" in element_text
    ):
        _add_note(
            "Element interaction failures indicate selector or timing issues. Review locators and waits."
        )

    if not review_notes:
        review_notes.append("No dominant patterns detected. Review grouped issues for context.")

    for note in review_notes[:6]:
        lines.append(f"- {note}")

    return "\n".join(lines).rstrip() + "\n"


def _build_human_summary_text(
    session: TestSession,
    summary_markdown: str,
    summary_json: str = "",
) -> tuple[str, str]:
    api_key = _get_gemini_api_key()
    if not api_key:
        return "", "Missing GEMINI_API_KEY."
    if summary_json:
        prompt = _build_human_summary_prompt(summary_json)
    else:
        session_dict = _session_to_dict(session)
        prompt = _build_human_summary_prompt(
            json.dumps(session_dict, ensure_ascii=True, default=str)
        )
    text, error = _call_gemini_api(prompt, api_key)
    if error:
        return "", error
    text = _sanitize_ascii(text).strip()
    if not text:
        return "", "Empty response."
    text = _markdown_to_text(text)
    if not text:
        return "", "Empty response."
    return text, ""


def _build_human_summary_fallback(session: TestSession, summary_markdown: str, reason: str) -> str:
    note = _sanitize_ascii(reason or "Unknown error.")
    page_failures = len(
        [p for p in session.pages_tested if _status_value(p.status) == TestStatus.FAILED.value]
    )
    network_count = sum(len(p.network_errors) for p in session.pages_tested)
    console_count = sum(len(p.console_errors) for p in session.pages_tested)
    element_failures = sum(
        1 for p in session.pages_tested for t in p.element_tests
        if _status_value(t.status) == TestStatus.FAILED.value
    )
    total_issues = page_failures + network_count + console_count + element_failures
    pages_with_issues = sum(
        1 for p in session.pages_tested
        if p.has_errors or _status_value(p.status) == TestStatus.FAILED.value
    )
    structured_text = _markdown_to_text(summary_markdown)
    fallback = (
        "Human Summary\n"
        f"Note: LLM summary could not be generated or was incomplete ({note}).\n"
        f"This run tested {session.total_pages} pages on {session.website_url}. "
        f"Pages with issues: {pages_with_issues}. "
        f"Total issues found: {total_issues} "
        f"(page_load_failures={page_failures}, "
        f"network_errors={network_count}, "
        f"console_errors={console_count}, "
        f"element_failures={element_failures}).\n\n"
        "Detailed issue list (structured summary converted to text):\n\n"
    )
    fallback += structured_text
    if not fallback.endswith("\n"):
        fallback += "\n"
    return fallback


class ReportGenerator:
    """Generates HTML test reports."""
    
    def __init__(self, output_folder: str):
        self.output_folder = output_folder
        os.makedirs(output_folder, exist_ok=True)
    
    def _get_template(self) -> str:
        return open(os.path.join(os.path.dirname(__file__), "report_template.html"), "r", encoding="utf-8").read()
    
    def generate_report(self, session: TestSession, json_path: str = "") -> tuple[str, str, str]:
        """Generate HTML, summary markdown, and human summary text for the test session."""
        template = Template(self._get_template())
        _ensure_severities(session)

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
                    "verification": error.verification,
                    "screenshot_path": error.screenshot_path,
                    "request_headers": error.request_headers,
                    "response_headers": error.response_headers,
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
                    "verification": error.verification,
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
                    "verification": test.verification,
                    "screenshot_path": test.screenshot_path,
                    "console_logs": console_logs,
                })

        module_flow_tree = {}
        for page in session.pages_tested:
            module_name = page.module or "Uncategorized"
            submodule = _submodule_label(module_name, page.url)
            module_flow_tree.setdefault(module_name, {})
            module_flow_tree[module_name].setdefault(submodule, [])
            elements = []
            for test in page.element_tests:
                label = _element_label(test)
                if label not in elements:
                    elements.append(label)
            module_flow_tree[module_name][submodule].append({
                "url": page.url,
                "title": page.title,
                "status": page.status,
                "elements": elements,
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

        module_crawl_path = {}
        for step in session.crawl_path:
            module_name = step.module or "Uncategorized"
            module_crawl_path.setdefault(module_name, []).append(step)

        summary_markdown = _build_summary_markdown(session)
        summary_html = _markdown_to_html(summary_markdown)
        summary_markdown_escaped = html.escape(summary_markdown)
        summary_path = os.path.join(self.output_folder, "summary_report.md")
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write(summary_markdown)

        summary_json = ""
        if json_path:
            try:
                with open(json_path, "r", encoding="utf-8") as handle:
                    summary_json = handle.read()
            except Exception:
                summary_json = ""
        human_summary_text, human_error = _build_human_summary_text(
            session,
            summary_markdown,
            summary_json,
        )
        if not human_summary_text:
            human_summary_text = _build_human_summary_fallback(session, summary_markdown, human_error)
        human_summary_text = _sanitize_ascii(human_summary_text)
        human_summary_text_escaped = html.escape(human_summary_text)
        human_summary_path = os.path.join(self.output_folder, "human_summary.txt")
        with open(human_summary_path, "w", encoding="utf-8") as f:
            f.write(human_summary_text)
        human_summary_md_path = os.path.join(self.output_folder, "humansummary.md")
        with open(human_summary_md_path, "w", encoding="utf-8") as f:
            f.write(human_summary_text)

        html_content = template.render(
            session=session,
            module_summary=module_summary,
            module_errors=module_errors,
            module_crawl_path=module_crawl_path,
            module_flow_tree=module_flow_tree,
            summary_html=summary_html,
            summary_markdown_escaped=summary_markdown_escaped,
            human_summary_text_escaped=human_summary_text_escaped
        )
        
        report_path = os.path.join(self.output_folder, "test_report.html")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        return report_path, summary_path, human_summary_path

    def generate_summary_report(self, session: TestSession) -> str:
        """Generate a grouped Markdown summary report."""
        summary_markdown = _build_summary_markdown(session)
        summary_path = os.path.join(self.output_folder, "summary_report.md")
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write(summary_markdown)

        return summary_path
    
    def save_session_data(self, session: TestSession) -> str:
        """Save session data as JSON for later analysis."""
        session_dict = _session_to_dict(session)
        
        json_path = os.path.join(self.output_folder, "test_data.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(session_dict, f, indent=2, default=str)
        
        return json_path
