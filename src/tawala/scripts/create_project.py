import shutil
import subprocess
import sys
from pathlib import Path

from termcolor import colored


def get_project_config(command: str) -> tuple[str, Path, str | None]:
    """Determine project name and target directory from command line args."""
    if len(sys.argv) < 3:  # sys.argv[0] is script, [1] is command, [2] is first arg
        if command in ["new", "init"]:
            return "my-app", Path.cwd() / "my-app", None
        elif command == "create":
            return Path.cwd().name, Path.cwd(), "."

    arg = sys.argv[2]  # First actual arg after command
    if arg == ".":
        target_dir = Path.cwd()
        return target_dir.name, target_dir, arg
    else:
        return arg, Path.cwd() / arg, arg


def check_directory_empty(target_dir: Path) -> None:
    """Check if directory is empty and exit if not."""
    contents = list(target_dir.iterdir())

    if not contents:
        return

    print(colored("⚠️  Current directory is not empty!", "yellow", attrs=["bold"]))
    print(colored("Contents:", "cyan"))

    for item in contents[:10]:
        print(f"  - {item.name}")

    if len(contents) > 10:
        print(f"  ... and {len(contents) - 10} more items")

    print(colored("\nPlease use an empty directory.", "red"))
    sys.exit(1)


def check_directory_exists(target_dir: Path, project_name: str) -> None:
    """Check if target directory exists and exit with helpful message."""
    if not target_dir.exists():
        return

    print(
        colored(
            f"⚠️  A folder named '{target_dir.name}' already exists!",
            "yellow",
            attrs=["bold"],
        )
    )
    print(colored("Please use a different name, e.g.:", "cyan"))
    print(f"  uvx create-olyv-app {project_name}-new")
    print(colored("\n❌ Aborted.", "red"))
    sys.exit(1)


def should_skip_file(item: Path) -> bool:
    """Check if file or directory should be skipped during copy."""
    # Skip __pycache__ directories
    if "__pycache__" in item.parts:
        return True

    return False


def copy_template_files(
    template_dir: Path, target_dir: Path, project_name: str
) -> None:
    """Copy all template files to target directory."""
    target_dir.mkdir(parents=True, exist_ok=True)

    for item in template_dir.rglob("*"):
        if not item.is_file():
            continue

        # Skip unwanted files
        if should_skip_file(item):
            continue

        relative_path = item.relative_to(template_dir)
        dest_path = target_dir / relative_path
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, dest_path)

        # Update pyproject.toml with the actual project name
        if dest_path.name == "pyproject.toml":
            update_project_name(dest_path, project_name)


def update_project_name(pyproject_path: Path, project_name: str) -> None:
    """Replace default project name in pyproject.toml."""
    content = pyproject_path.read_text()
    content = content.replace('name = "default"', f'name = "{project_name}"')
    pyproject_path.write_text(content)


def run_uv_sync(target_dir: Path) -> None:
    """Run uv sync in the target directory."""
    print(colored("\n📦 Installing dependencies...", "cyan", attrs=["bold"]))
    subprocess.run(["uv", "sync"], cwd=target_dir, check=True)


def print_success_message(project_name: str, arg: str | None) -> None:
    """Print success message with next steps."""
    print(colored(f"\n✅ Project '{project_name}' created successfully!", "green"))
    print(colored("\nNext steps:", "cyan", attrs=["bold"]))

    if arg != ".":
        print(f"  cd {project_name}")

    print("  uv run python manage.py migrate")
    print("  uv run python manage.py setup_groups")
    print("  uv run python manage.py runserver")


def main() -> None:
    """Main entry point for create-olyv-app CLI."""
    if len(sys.argv) < 2:
        print("Error: Command not provided.")
        sys.exit(1)
    command = sys.argv[1]
    project_name, target_dir, arg = get_project_config(command)

    # Validate directory state
    if arg == ".":
        check_directory_empty(target_dir)
    else:
        check_directory_exists(target_dir, project_name)

    # Create project
    print(colored(f"✨ Creating project: {project_name}", "green", attrs=["bold"]))

    template_dir = Path(__file__).parent / "templates" / "default"
    copy_template_files(template_dir, target_dir, project_name)

    # Install dependencies
    run_uv_sync(target_dir)

    # Show success message
    print_success_message(project_name, arg)


if __name__ == "__main__":
    main()
