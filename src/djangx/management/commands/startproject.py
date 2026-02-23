"""Project initialization command."""

from argparse import ArgumentParser, Namespace

from christianwhocodes import ExitCode, InitAction, PostgresFilename, Text, cprint

from ... import PACKAGE
from ..enums import DatabaseEnum, PresetEnum

__all__: list[str] = ["StartprojectCommand"]


class _PresetDatabaseIncompatibilityError(Exception):
    """Raised when a preset is used with an incompatible database."""


class _BaseCommand:
    """Base class for all CLI commands.

    Subclass this and implement :attr:`prog`, :attr:`help`,
    :meth:`add_arguments`, and :meth:`handle` to define a command. Invoke the
    command by calling the instance with a list of CLI arguments.

    Example::

        class GreetCommand(_BaseCommand):
            prog = "greet"
            help = "Say hello."

            def add_arguments(self, parser: ArgumentParser) -> None:
                parser.add_argument("name", help="Name to greet.")

            def handle(self, args: Namespace) -> ExitCode:
                print(f"Hello, {args.name}!")
                return ExitCode.SUCCESS

        exit_code = GreetCommand()(["Alice"])  # prints "Hello, Alice!"

    """

    prog: str = ""
    """The program name shown in usage output. Set this on the subclass."""

    help: str = ""
    """Short description of the command, used as the parser's description. Set this on the subclass."""

    def add_arguments(self, parser: ArgumentParser) -> None:
        """Register arguments onto the parser.

        Called automatically by :meth:`create_parser`. Override this to add
        arguments via ``parser.add_argument(...)`` instead of defining them
        directly inside :meth:`create_parser`, keeping argument declaration
        and parser configuration separate.
        """

    def create_parser(self) -> ArgumentParser:
        """Construct and return the argument parser using :attr:`prog` and :attr:`help`.

        Called automatically by :meth:`__call__`. You should not need to
        override this in subclasses — define :attr:`prog`, :attr:`help`, and
        :meth:`add_arguments` instead.
        """
        parser = ArgumentParser(prog=self.prog, description=self.help)
        self.add_arguments(parser)
        return parser

    def handle(self, args: Namespace) -> ExitCode:
        """Execute the command logic with the parsed arguments.

        Receives the :class:`~argparse.Namespace` produced by parsing argv
        and should return :attr:`~ExitCode.SUCCESS` or :attr:`~ExitCode.ERROR`.

        Raises:
            NotImplementedError: If not overridden in a subclass.

        """
        raise NotImplementedError

    def __call__(self, argv: list[str]) -> ExitCode:
        """Parse ``argv`` and run the command.

        This is the primary entry point. Instantiate the command and call it
        directly with the raw argument list, typically sourced from
        ``sys.argv[1:]`` or a router that dispatches subcommands.

        Example::

            exit_code = MyCommand()(sys.argv[1:])

        """
        return self.handle(self.create_parser().parse_args(argv))


class StartprojectCommand(_BaseCommand):
    """Command to initialize a new project."""

    _actions = " | ".join(InitAction)
    prog = f"{PACKAGE.name} [{_actions}] <project_name>"
    help = f"Initialize a new {PACKAGE.display_name} project."

    def add_arguments(self, parser: ArgumentParser) -> None:
        """Register arguments onto the parser."""
        parser.add_argument("project_name", help="Name of the project to initialize.")
        parser.add_argument(
            "-p",
            "--preset",
            dest="preset",
            type=PresetEnum,
            choices=[p for p in PresetEnum],
            help="Project preset to use.",
            default=PresetEnum.DEFAULT,
        )
        parser.add_argument(
            "--db",
            type=DatabaseEnum,
            choices=[db for db in DatabaseEnum],
            help="Database backend to use.",
        )
        pg_config_group = parser.add_mutually_exclusive_group()
        pg_config_group.add_argument(
            "--pg-use-env-vars",
            action="store_true",
            help="Use environment variables for PostgreSQL configuration.",
        )
        pg_config_group.add_argument(
            "--pg-use-service-files",
            action="store_true",
            help=f"Use a `{PostgresFilename.PGSERVICE}` and `{PostgresFilename.PGPASS}` file for PostgreSQL configuration.",
        )

    def handle(self, args: Namespace) -> ExitCode:
        """Execute the command logic with the parsed arguments."""
        try:
            args = self._validate_args(args)
        except _PresetDatabaseIncompatibilityError as e:
            cprint(str(e), Text.ERROR)
            return ExitCode.ERROR
        except Exception as e:
            cprint(f"An unexpected error occurred: {e}", Text.ERROR)
            return ExitCode.ERROR
        else:
            return ExitCode.SUCCESS

    def _validate_args(self, args: Namespace) -> Namespace:
        """Validate the provided arguments."""
        match args.preset:
            case PresetEnum.VERCEL:
                if args.db == DatabaseEnum.SQLITE3:
                    raise _PresetDatabaseIncompatibilityError(
                        f"Error: The {PresetEnum.VERCEL} preset requires {DatabaseEnum.POSTGRESQL}. "
                        f"You cannot use {args.db} with this preset."
                    )
                args.db = DatabaseEnum.POSTGRESQL

            case _:
                if not args.db:
                    args.db = DatabaseEnum.SQLITE3

        if args.db == DatabaseEnum.POSTGRESQL and not (
            args.pg_use_env_vars or args.pg_use_service_files
        ):
            args.pg_use_env_vars = True

        return args
