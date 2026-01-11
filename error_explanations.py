"""
Error explanations and suggestions module.
Provides human-readable explanations for common errors.
"""


def get_network_error_explanation(status_code: int, url: str) -> dict:
    """Get explanation and suggestion for network errors."""
    explanations = {
        400: {
            "title": "Bad Request",
            "explanation": "The server could not understand the request due to invalid syntax. This usually means the request was malformed or missing required parameters.",
            "suggestion": "Check if the API endpoint expects specific parameters or headers. Verify the request format matches the API specification.",
            "severity": "medium"
        },
        401: {
            "title": "Unauthorized",
            "explanation": "Authentication is required to access this resource. The request lacks valid authentication credentials.",
            "suggestion": "Ensure the user is logged in before accessing this page. Check if the authentication token is being sent correctly.",
            "severity": "high"
        },
        403: {
            "title": "Forbidden",
            "explanation": "The server understood the request but refuses to authorize it. The user may not have permission to access this resource.",
            "suggestion": "Verify user permissions and roles. Check if the resource requires specific access rights.",
            "severity": "high"
        },
        404: {
            "title": "Not Found",
            "explanation": "The requested resource could not be found on the server. This could be a broken link, deleted resource, or incorrect URL.",
            "suggestion": "Verify the URL is correct. Check if the resource was moved or deleted. Update any hardcoded links.",
            "severity": "medium"
        },
        405: {
            "title": "Method Not Allowed",
            "explanation": "The HTTP method used is not supported for this resource. For example, using POST when only GET is allowed.",
            "suggestion": "Check the API documentation for supported HTTP methods. Ensure forms use the correct method.",
            "severity": "medium"
        },
        500: {
            "title": "Internal Server Error",
            "explanation": "The server encountered an unexpected condition that prevented it from fulfilling the request. This is a server-side issue.",
            "suggestion": "Check server logs for detailed error messages. This requires backend investigation.",
            "severity": "critical"
        },
        502: {
            "title": "Bad Gateway",
            "explanation": "The server acting as a gateway received an invalid response from the upstream server.",
            "suggestion": "Check if backend services are running. Verify load balancer and proxy configurations.",
            "severity": "critical"
        },
        503: {
            "title": "Service Unavailable",
            "explanation": "The server is temporarily unable to handle the request, possibly due to maintenance or overload.",
            "suggestion": "Wait and retry. Check server status and resource utilization. Consider scaling if under heavy load.",
            "severity": "critical"
        },
        504: {
            "title": "Gateway Timeout",
            "explanation": "The server acting as a gateway did not receive a timely response from the upstream server.",
            "suggestion": "Check backend service response times. Consider increasing timeout values or optimizing slow operations.",
            "severity": "high"
        }
    }
    
    default = {
        "title": f"HTTP Error {status_code}",
        "explanation": f"The server returned status code {status_code}.",
        "suggestion": "Investigate the server logs for more details.",
        "severity": "medium"
    }
    
    return explanations.get(status_code, default)


def get_console_error_explanation(message: str, error_type: str) -> dict:
    """Get explanation and suggestion for console errors."""
    message_lower = message.lower()
    
    # Common error patterns
    if "undefined" in message_lower or "is not defined" in message_lower:
        return {
            "title": "Undefined Variable/Function",
            "explanation": "A variable or function is being used before it's defined, or there's a typo in the name.",
            "suggestion": "Check for typos in variable names. Ensure scripts are loaded in the correct order. Verify imports are correct.",
            "severity": "high"
        }
    
    if "cannot read property" in message_lower or "cannot read properties" in message_lower:
        return {
            "title": "Null Reference Error",
            "explanation": "Attempting to access a property of null or undefined. The expected object doesn't exist.",
            "suggestion": "Add null checks before accessing properties. Verify the data is loaded before using it. Use optional chaining (?.).",
            "severity": "high"
        }
    
    if "cors" in message_lower or "cross-origin" in message_lower:
        return {
            "title": "CORS Policy Error",
            "explanation": "Cross-Origin Resource Sharing policy is blocking the request. The server doesn't allow requests from this origin.",
            "suggestion": "Configure CORS headers on the server. Add the origin to allowed origins list. Use a proxy for development.",
            "severity": "high"
        }
    
    if "failed to fetch" in message_lower or "network error" in message_lower:
        return {
            "title": "Network/Fetch Error",
            "explanation": "A network request failed. This could be due to connectivity issues, server being down, or CORS.",
            "suggestion": "Check network connectivity. Verify the API endpoint is accessible. Check for CORS issues.",
            "severity": "high"
        }
    
    if "syntax error" in message_lower:
        return {
            "title": "JavaScript Syntax Error",
            "explanation": "There's a syntax error in the JavaScript code that prevents it from executing.",
            "suggestion": "Check for missing brackets, quotes, or semicolons. Use a linter to catch syntax errors.",
            "severity": "critical"
        }
    
    if "type error" in message_lower or "typeerror" in message_lower:
        return {
            "title": "Type Error",
            "explanation": "An operation was performed on an incompatible type, like calling a non-function or accessing properties of null.",
            "suggestion": "Add type checking. Verify function arguments. Ensure data structures match expected types.",
            "severity": "high"
        }
    
    if "deprecated" in message_lower:
        return {
            "title": "Deprecation Warning",
            "explanation": "A deprecated feature or API is being used. It may be removed in future versions.",
            "suggestion": "Update to use the recommended alternative. Check documentation for migration guides.",
            "severity": "low"
        }
    
    if "mixed content" in message_lower:
        return {
            "title": "Mixed Content Warning",
            "explanation": "HTTP content is being loaded on an HTTPS page, which is a security risk.",
            "suggestion": "Update all resource URLs to use HTTPS. Configure server to redirect HTTP to HTTPS.",
            "severity": "medium"
        }
    
    if "cookie" in message_lower and ("samesite" in message_lower or "secure" in message_lower):
        return {
            "title": "Cookie Security Warning",
            "explanation": "Cookies are being set without proper security attributes (SameSite, Secure).",
            "suggestion": "Add SameSite and Secure attributes to cookies. Update cookie configuration on the server.",
            "severity": "medium"
        }
    
    # Default explanation based on error type
    if error_type == "error":
        return {
            "title": "JavaScript Error",
            "explanation": "An error occurred during JavaScript execution.",
            "suggestion": "Check the browser console for stack trace. Debug the error at the specified location.",
            "severity": "high"
        }
    
    if error_type == "warning":
        return {
            "title": "Console Warning",
            "explanation": "A warning was logged, indicating a potential issue that doesn't break functionality.",
            "suggestion": "Review the warning message and address if necessary. Warnings may become errors in future versions.",
            "severity": "low"
        }
    
    return {
        "title": "Console Message",
        "explanation": "A message was logged to the console.",
        "suggestion": "Review the message content for any issues.",
        "severity": "low"
    }


def get_element_error_explanation(error_message: str, element_type: str) -> dict:
    """Get explanation and suggestion for element interaction errors."""
    message_lower = error_message.lower()
    
    if "timeout" in message_lower:
        return {
            "title": "Interaction Timeout",
            "explanation": f"The {element_type} took too long to respond or become interactive.",
            "suggestion": "Check if the element is properly loaded. Verify no overlays are blocking it. Consider increasing timeout.",
            "severity": "medium"
        }
    
    if "not visible" in message_lower or "hidden" in message_lower:
        return {
            "title": "Element Not Visible",
            "explanation": f"The {element_type} exists in the DOM but is not visible on the page.",
            "suggestion": "Check CSS display/visibility properties. Ensure the element is not hidden behind other elements.",
            "severity": "medium"
        }
    
    if "detached" in message_lower:
        return {
            "title": "Element Detached",
            "explanation": f"The {element_type} was removed from the DOM during the interaction.",
            "suggestion": "The page may have reloaded or the element was dynamically removed. Add wait for element stability.",
            "severity": "high"
        }
    
    if "intercept" in message_lower or "click" in message_lower:
        return {
            "title": "Click Intercepted",
            "explanation": f"Another element is covering the {element_type} and intercepting the click.",
            "suggestion": "Check for modals, overlays, or fixed elements blocking the target. Close any open dialogs first.",
            "severity": "medium"
        }
    
    return {
        "title": "Element Interaction Error",
        "explanation": f"An error occurred while interacting with the {element_type}.",
        "suggestion": "Check the element's state and ensure it's interactive. Review the full error message.",
        "severity": "medium"
    }


def get_page_error_explanation(error_message: str) -> dict:
    """Get explanation for page-level errors."""
    message_lower = error_message.lower()
    
    if "timeout" in message_lower:
        return {
            "title": "Page Load Timeout",
            "explanation": "The page took too long to load completely.",
            "suggestion": "Check server response time. Optimize page assets. Consider lazy loading for large resources.",
            "severity": "high"
        }
    
    if "navigation" in message_lower:
        return {
            "title": "Navigation Error",
            "explanation": "Failed to navigate to the page.",
            "suggestion": "Verify the URL is correct and accessible. Check for redirects or authentication requirements.",
            "severity": "high"
        }
    
    return {
        "title": "Page Error",
        "explanation": "An error occurred while loading or interacting with the page.",
        "suggestion": "Review the full error message for specific details.",
        "severity": "medium"
    }
