"""
Route seed extraction from a React Router routes file.
"""

from __future__ import annotations

import os
import re
from itertools import product
from typing import Dict, Iterable, List, Optional, Tuple
from urllib.parse import urljoin, urlparse


_PATH_PATTERN = re.compile(
    r"path\s*=\s*(?:\{)?\s*['\"]([^'\"]+)['\"]\s*(?:\})?",
    re.MULTILINE
)


def _origin_from_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme and parsed.netloc:
        return f"{parsed.scheme}://{parsed.netloc}"
    return url.rstrip("/")


def _extract_paths(content: str) -> List[str]:
    raw_paths = _PATH_PATTERN.findall(content)
    seen = set()
    paths: List[str] = []
    for raw in raw_paths:
        path = raw.strip()
        if not path or path == "*" or "*" in path:
            continue
        if not path.startswith("/"):
            path = f"/{path}"
        if path not in seen:
            seen.add(path)
            paths.append(path)
    return paths


def _normalize_param_values(param_values: Dict[str, Iterable]) -> Dict[str, List[str]]:
    normalized: Dict[str, List[str]] = {}
    for key, values in (param_values or {}).items():
        if values is None:
            continue
        if isinstance(values, (str, int, float)):
            values = [values]
        cleaned: List[str] = []
        for value in values:
            if value is None:
                continue
            text = str(value).strip()
            if text.lower() in ("undefined", "null", "none", "nan"):
                continue
            if text:
                cleaned.append(text)
        if cleaned:
            normalized[str(key)] = cleaned
    return normalized


def normalize_param_values(param_values: Dict[str, Iterable]) -> Dict[str, List[str]]:
    return _normalize_param_values(param_values)


def load_route_paths(routes_file: str) -> Tuple[List[str], Dict[str, int]]:
    stats = {
        "total_paths": 0,
        "missing_file": 0,
    }
    if not routes_file or not os.path.exists(routes_file):
        stats["missing_file"] = 1
        return [], stats

    with open(routes_file, "r", encoding="utf-8") as handle:
        content = handle.read()

    paths = _extract_paths(content)
    stats["total_paths"] = len(paths)
    return paths, stats


def _compile_dynamic_matcher(path: str) -> Optional[Tuple[re.Pattern, List[str]]]:
    params = re.findall(r":(\w+)", path)
    if not params:
        return None
    if path == "/":
        return None

    segments = path.strip("/").split("/")
    regex_parts = []
    for segment in segments:
        if segment.startswith(":"):
            regex_parts.append(r"([^/]+)")
        else:
            regex_parts.append(re.escape(segment))
    pattern = "^/" + "/".join(regex_parts) + "$"
    return re.compile(pattern), params


def build_route_matchers(paths: List[str]) -> List[Tuple[re.Pattern, List[str]]]:
    matchers: List[Tuple[re.Pattern, List[str]]] = []
    for path in paths:
        compiled = _compile_dynamic_matcher(path)
        if compiled:
            matchers.append(compiled)
    return matchers


def extract_param_values_from_urls(
    route_matchers: List[Tuple[re.Pattern, List[str]]],
    urls: Iterable[str]
) -> Dict[str, List[str]]:
    collected: Dict[str, set] = {}
    for url in urls or []:
        try:
            path = urlparse(url).path
        except Exception:
            continue
        if not path:
            continue
        for pattern, params in route_matchers:
            match = pattern.match(path)
            if not match:
                continue
            groups = match.groups()
            for name, value in zip(params, groups):
                if not value:
                    continue
                if value.lower() in ("undefined", "null", "none", "nan"):
                    continue
                collected.setdefault(name, set()).add(value)
    return {key: sorted(values) for key, values in collected.items()}


def _expand_dynamic_paths(
    paths: List[str],
    param_values: Dict[str, List[str]],
    include_dynamic: bool,
    skip_missing: bool
) -> Tuple[List[str], List[str], List[str]]:
    static_paths: List[str] = []
    dynamic_paths: List[str] = []
    expanded_paths: List[str] = []

    for path in paths:
        params = re.findall(r":(\w+)", path)
        if not params:
            static_paths.append(path)
            continue

        dynamic_paths.append(path)
        if not include_dynamic:
            continue

        value_lists: List[List[str]] = []
        missing = False
        for param in params:
            values = param_values.get(param)
            if not values:
                missing = True
                break
            value_lists.append(values)

        if missing:
            if skip_missing:
                continue
            continue

        for combo in product(*value_lists):
            expanded = path
            for param, value in zip(params, combo):
                expanded = expanded.replace(f":{param}", value)
            expanded_paths.append(expanded)

    return static_paths, dynamic_paths, expanded_paths


def expand_route_paths(
    paths: List[str],
    base_url: str,
    include_dynamic: bool,
    param_values: Dict[str, Iterable],
    skip_missing: bool = True
) -> Tuple[List[str], Dict[str, int]]:
    stats = {
        "total_paths": len(paths),
        "static_paths": 0,
        "dynamic_paths": 0,
        "dynamic_expanded": 0,
    }

    normalized_params = _normalize_param_values(param_values or {})
    static_paths, dynamic_paths, expanded_paths = _expand_dynamic_paths(
        paths,
        normalized_params,
        include_dynamic=include_dynamic,
        skip_missing=skip_missing
    )

    stats["static_paths"] = len(static_paths)
    stats["dynamic_paths"] = len(dynamic_paths)
    stats["dynamic_expanded"] = len(expanded_paths)

    base_origin = _origin_from_url(base_url)
    urls: List[str] = []
    seen = set()
    for path in static_paths + expanded_paths:
        url = urljoin(base_origin, path)
        if url not in seen:
            seen.add(url)
            urls.append(url)

    return urls, stats


def get_route_seed_urls(
    routes_file: str,
    base_url: str,
    include_dynamic: bool,
    param_values: Dict[str, Iterable],
    skip_missing: bool = True
) -> Tuple[List[str], Dict[str, int]]:
    paths, load_stats = load_route_paths(routes_file)
    if load_stats.get("missing_file"):
        return [], load_stats

    urls, expand_stats = expand_route_paths(
        paths,
        base_url,
        include_dynamic=include_dynamic,
        param_values=param_values,
        skip_missing=skip_missing
    )
    stats = {
        "missing_file": load_stats.get("missing_file", 0),
        **expand_stats,
    }
    return urls, stats
