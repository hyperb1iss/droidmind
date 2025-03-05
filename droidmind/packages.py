"""Package management utilities for DroidMind."""



def parse_package_list(output: str) -> list[dict[str, str]]:
    """Parse the output of 'pm list packages -f' command.

    Args:
        output: Raw command output from 'pm list packages -f'

    Returns:
        List of dictionaries containing package info with 'package' and 'path' keys
    """
    apps = []
    for line in output.splitlines():
        if line.startswith("package:"):
            # Format is: "package:/path/to/base.apk=com.package.name"
            path_and_pkg = line[8:]  # Strip "package:"
            if "=" in path_and_pkg:
                path, package = path_and_pkg.rsplit("=", 1)
                apps.append({"package": package.strip(), "path": path.strip()})
    return apps
