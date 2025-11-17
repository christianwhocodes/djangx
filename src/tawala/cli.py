"""
Command-line interface for Tawala.
Handles routing commands to appropriate scripts based on context.
"""

import subprocess
import sys
from pathlib import Path


def is_executed_from_tawala_package_dir() -> bool:
    """
    Check if the directory structure matches that of the Tawala package
    Confirm by checking for the absence of user project indicators (e.g., config/settings.py)
    """
    current_dir = Path.cwd()
    return not (current_dir / "config" / "settings.py").exists()


def tawalacommands() -> list[str]:
    """
    Get the list of available Tawala-specific commands.
    Includes 'help' if executed from the Tawala package directory.
    """
    commands_dir = Path(__file__).resolve().parent / "utils" / "management" / "commands"
    commands = [f.stem for f in commands_dir.glob("*.py") if f.stem != "__init__"]
    if is_executed_from_tawala_package_dir():
        commands.append("help")
    return commands


def main() -> None:
    """
    Main entry point for the Tawala CLI.
    Parses command-line arguments and executes the appropriate script.
    """
    if len(sys.argv) < 2:
        print("No command provided.")
        sys.exit(1)

    scripts_dir = Path(__file__).resolve().parent / "scripts"

    try:
        match sys.argv[1]:
            case command if command in tawalacommands():
                # Execute Tawala-specific commands from the package directory
                result = subprocess.run(
                    [
                        sys.executable,
                        str(scripts_dir / "execute_from_tawala_package_dir.py"),
                        command,
                    ]
                    + sys.argv[2:]
                )
                sys.exit(result.returncode)

            case _:
                if not is_executed_from_tawala_package_dir():
                    # Execute Django commands from the user project directory
                    result = subprocess.run(
                        [
                            sys.executable,
                            str(scripts_dir / "execute_from_user_project_dir.py"),
                        ]
                        + sys.argv[1:]
                    )
                    sys.exit(result.returncode)
                else:
                    print(
                        f"Unknown command: '{sys.argv[1]}'\nType 'tawala help' for usage."
                    )
                    sys.exit(1)

    except KeyboardInterrupt:
        sys.exit(1)


if __name__ == "__main__":
    main()
