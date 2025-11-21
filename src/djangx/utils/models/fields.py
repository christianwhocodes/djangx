from typing import Any, Iterable, Tuple


def calculate_max_length_from_choices(choices: Iterable[Tuple[str, Any]]) -> int:
    """
    Utility function to get the max_length for a CharField based on the longest choice value.

    Args:
        choices: A tuple of choices

    Example:
        class MyModel(models.Model):
            class Choices(models.TextChoices):
                SHORT = "SHORT", "Short Option"
                VERY_LONG_OPTION = "VERY_LONG_OPTION", "Very Long Option"

            field = models.CharField(
                max_length=calculate_max_length_from_choices(Choices.choices),
                choices=Choices.choices
            )

    Returns:
        int: The length of the longest choice value.
    """
    return max(len(choice[0]) for choice in choices)
