import subprocess
import sys
from pathlib import Path

from termcolor import colored


def main() -> None:
    """Main CLI entry point for tawala commands."""
    if len(sys.argv) < 2:
        print_help()
        sys.exit(1)

    command = sys.argv[1]
    scripts_dir = Path(__file__).parent / "scripts"

    # Remove the command from sys.argv so scripts can parse remaining args
    sys.argv = [sys.argv[0]] + sys.argv[2:]

    script_path = None
    match command:
        case "init" | "create" | "new":
            script_path = scripts_dir / "create_project.py"
            if not script_path.exists():
                print(
                    colored(
                        "❌ Script for creating a Tawala project not found.\n", "red"
                    )
                )
                sys.exit(1)

        case _:
            print(colored(f"❌ Unknown command: {command}\n", "red"))
            print_help()
            sys.exit(1)

    if script_path:
        result = subprocess.run(
            # Note: sys.argv[1:] now starts from the original sys.argv[2] since command was removed
            [sys.executable, str(script_path), command] + sys.argv[1:]
        )
        sys.exit(result.returncode)


def print_help() -> None:
    """Print available commands."""
    print(colored("Tawala CLI", "cyan", attrs=["bold"]))
    print("\nAvailable commands:")
    print(" init|create|new [project-name]  Create a new Tawala project")
    print("\nUsage:")
    print("  uvx tawala init my-project")
    print("  uvx tawala create my-project")
    print("  uvx tawala new .")


if __name__ == "__main__":
    main()
