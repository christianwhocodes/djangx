import subprocess
import sys
from pathlib import Path


def utilitycommands() -> list[str]:
    commands_dir = Path(__file__).resolve().parent / "utils" / "management" / "commands"
    return [f.stem for f in commands_dir.glob("*.py") if f.stem != "__init__"]


def main() -> None:
    if len(sys.argv) < 2:
        print("No command provided.")
        sys.exit(1)

    scripts_dir = Path(__file__).resolve().parent / "scripts"
    utils_commands = utilitycommands()

    try:
        match sys.argv[1]:
            case command if command in utils_commands:
                result = subprocess.run(
                    [sys.executable, str(scripts_dir / "execute_from_tawala_dir.py")]
                    + sys.argv[1:]
                )
                sys.exit(result.returncode)
            case _:
                result = subprocess.run(
                    [
                        sys.executable,
                        str(scripts_dir / "execute_from_user_project_dir.py"),
                    ]
                    + sys.argv[1:]
                )
                sys.exit(result.returncode)
    except KeyboardInterrupt:
        sys.exit(1)


if __name__ == "__main__":
    main()
