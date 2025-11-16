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

    # Remove the command from sys.argv so scripts can parse remaining args
    sys.argv = [sys.argv[0]] + sys.argv[2:]

    match command:
        case "help" | "--help" | "-h":
            print_help()
            sys.exit(0)
        case _:
            script_path = Path(__file__).parent / "scripts" / f"{command}.py"

            if script_path.exists():
                result = subprocess.run(
                    # *: sys.argv[1:] now starts from the original sys.argv[2] since command was removed
                    [sys.executable, str(script_path), command] + sys.argv[1:]
                )
                sys.exit(result.returncode)
            else:
                print(colored(f"❌ Script not found for command: {command}\n", "red"))
                sys.exit(1)


def print_help() -> None:
    """Print available commands."""
    print(colored("Tawala CLI", "cyan", attrs=["bold"]))
    print("\nAvailable commands:")
    # Create Project Command
    print("\n" + colored("init [project-name]", "cyan", attrs=["bold"]))
    print("  Usage: uvx tawala init my-project")
    print("  Create / Initialize a new Tawala project")
    # Get Random Secret Key Command
    print("\n" + colored("generaterandom", "cyan", attrs=["bold"]))
    print("  Usage: uvx tawala generaterandom")
    print("  Generate a random string (suitable for Django SECRET_KEY)")


if __name__ == "__main__":
    main()
