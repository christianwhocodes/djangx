import sys

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
        case "new":
            from tawala.scripts.new import main as new

            new()

        case _:
            print(colored(f"❌ Unknown command: {command}\n", "red"))
            print_help()
            sys.exit(1)


def print_help() -> None:
    """Print available commands."""
    print(colored("Tawala CLI", "cyan", attrs=["bold"]))
    print("\nAvailable commands:")
    print("  new [project-name]  Create a new Tawala project")
    print("\nUsage:")
    print("  uvx tawala new my-app")
    print("  uvx tawala new .")


if __name__ == "__main__":
    main()
