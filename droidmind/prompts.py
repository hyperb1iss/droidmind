"""
DroidMind Prompts - Prompt implementations for the DroidMind MCP server.

This module provides all the prompt templates for the DroidMind MCP server,
allowing AI assistants to have pre-defined interaction patterns.
"""

from droidmind.context import mcp


@mcp.prompt()
def debug_app_crash(app_package: str) -> str:
    """
    Generate a prompt to debug an app crash.

    Args:
        app_package: The package name of the crashed app
    """
    return f"""I need help debugging a crash in my Android app with package name '{app_package}'.

Can you help me:
1. Capture the relevant logcat output for this app
2. Analyze the stack trace and error messages
3. Identify the root cause of the crash
4. Suggest potential fixes

Please include specific code or configuration changes that might solve the issue.
"""


@mcp.prompt()
def analyze_battery_usage() -> str:
    """
    Generate a prompt to analyze battery usage.
    """
    return """My Android device's battery is draining too quickly.

Can you help me:
1. Analyze the battery usage statistics
2. Identify apps or services consuming excessive power
3. Check for wake locks or background processes
4. Suggest ways to optimize battery life

Please provide specific recommendations to extend battery life.
"""


@mcp.prompt()
def analyze_device_performance() -> str:
    """
    Generate a prompt to analyze overall device performance.
    """
    return """I need a comprehensive performance analysis of my connected Android device.

Can you:
1. Check CPU and memory usage statistics
2. Identify any resource-intensive processes
3. Analyze device temperature and thermal throttling
4. Evaluate current performance bottlenecks
5. Suggest optimizations to improve device responsiveness

Please include specific metrics and recommendations for improving overall system performance.
"""


@mcp.prompt()
def analyze_network_issues() -> str:
    """
    Generate a prompt to diagnose network connectivity problems.
    """
    return """I'm experiencing network connectivity issues on my Android device.

Please help me:
1. Check current network status and connection type
2. Run network diagnostics (ping, DNS resolution tests)
3. Analyze recent network-related log entries
4. Identify possible causes for poor connectivity
5. Suggest troubleshooting steps to resolve the issues

Please focus on both hardware and software potential causes.
"""


@mcp.prompt()
def optimize_app_startup(app_package: str) -> str:
    """
    Generate a prompt to analyze and optimize app startup time.

    Args:
        app_package: The package name of the app to optimize
    """
    return f"""I want to optimize the startup performance of my app '{app_package}'.

Can you help me:
1. Measure the current cold and warm start times
2. Analyze the startup process and identify bottlenecks
3. Check for excessive resource loading or initialization
4. Compare against similar apps in the same category
5. Suggest specific optimizations to improve startup speed

Please provide actionable recommendations with potential performance impacts.
"""


@mcp.prompt()
def analyze_app_permissions(app_package: str) -> str:
    """
    Generate a prompt to analyze an app's permission usage.

    Args:
        app_package: The package name of the app to analyze
    """
    return f"""I'd like to review the permissions used by '{app_package}' on my device.

Please:
1. List all permissions requested by the app
2. Identify any potentially concerning or excessive permissions
3. Check actual permission usage through recent access logs
4. Compare against similar apps in this category
5. Suggest which permissions could be safely denied

Focus on privacy implications and potential security concerns.
"""


@mcp.prompt()
def create_ui_test_script(app_package: str) -> str:
    """
    Generate a prompt to create a UI test script for an app.

    Args:
        app_package: The package name of the app to test
    """
    return f"""I need to create a UI test script for my app '{app_package}'.

Please help me:
1. Launch the app and take screenshots of key screens
2. Create a sequence of UI interactions to test core functionality
3. Include taps, swipes, text inputs, and navigation gestures
4. Define expected outcomes for each interaction
5. Generate a structured test plan that can be reused

The test should cover the main user flows and common edge cases.
"""


@mcp.prompt()
def analyze_ui_accessibility(app_package: str) -> str:
    """
    Generate a prompt to evaluate app accessibility.

    Args:
        app_package: The package name of the app to evaluate
    """
    return f"""I want to evaluate the accessibility of my app '{app_package}' for users with disabilities.

Please:
1. Check content labeling for screen readers
2. Evaluate contrast ratios and text sizing
3. Test navigation with keyboard/d-pad only
4. Analyze touch target sizes and spacing
5. Identify potential accessibility barriers

Provide specific recommendations to improve the app's accessibility compliance.
"""


@mcp.prompt()
def system_cleanup() -> str:
    """
    Generate a prompt for system cleanup and optimization.
    """
    return """My Android device is running low on storage and feeling sluggish.

Can you help me:
1. Identify large files and apps consuming storage space
2. Find cached data that can be safely cleared
3. Check for memory leaks or excessive battery consumption
4. Suggest apps or files to remove or archive
5. Recommend system settings to optimize for better performance

Please provide a step-by-step cleanup plan with projected space savings.
"""


@mcp.prompt()
def security_audit() -> str:
    """
    Generate a prompt for performing a device security audit.
    """
    return """I'd like to perform a security audit on my Android device.

Please help me:
1. Check current security patch level and system vulnerabilities
2. Identify apps with potentially risky permissions or behaviors
3. Analyze system settings for security weaknesses
4. Check for signs of compromise or suspicious activity
5. Recommend steps to strengthen device security

Please prioritize findings by risk level and provide actionable remediation steps.
"""
