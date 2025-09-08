from pathlib import Path


def find_project_root(start_path: str | Path | None = None) -> Path:
    """
    Find the project root by looking for manage.py.
    Returns Path object of the project root.
    """
    if start_path is None:
        start_path = Path.cwd()
    else:
        start_path = Path(start_path)  # Works with both str and Path

    markers = ["manage.py"]
    current = start_path.resolve()

    for parent in [current] + list(current.parents):
        if any((parent / marker).exists() for marker in markers):
            return parent

    return Path.cwd()


def static_url(path: str, static_url_base: str) -> str:
    """
    Generate static URL without requiring apps to be loaded.

    Args:
        path: Static file path relative to STATIC_ROOT
        static_url_base: Base static URL
    """
    return f"{static_url_base.rstrip('/')}/{path.lstrip('/')}"
