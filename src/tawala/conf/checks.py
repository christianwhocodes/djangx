class CLISetup:
    """A class to represent the state of a CLI setup process."""

    def __init__(self):
        self._is_successful: bool = False

    @classmethod
    def setsuccessful(cls):
        cls._is_successful = True

    @property
    def is_successful(self):
        return self._is_successful
