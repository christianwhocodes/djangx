class UniqueChoiceFormMixin:
    """
    Mixin for forms that restricts the 'name' field choices to those not
    already used in the database, ensuring uniqueness.
    """

    choices_attr = "MODEL_CHOICES"  # Default attribute name for choices

    def __init__(self, *args, **kwargs):
        """
        Initializes the form and dynamically filters available 'name' choices
        based on which ones are not already used in the database.
        """
        super().__init__(*args, **kwargs)

        if self.instance.pk or not self.choices_attr:
            return

        model_choices = getattr(self._meta.model, self.choices_attr, [])
        existing_values = self._meta.model.objects.values_list("name", flat=True)

        available_choices = [choice for choice in model_choices if choice[0] not in existing_values]

        self.fields["name"].choices = [(None, "")] + available_choices
