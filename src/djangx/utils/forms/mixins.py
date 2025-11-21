class UniqueChoiceMixin:
    """
    Mixin for ModelForms to filter available choices in a choice field to only
    those not yet used in existing model instances.

    This is useful for ensuring that choice values are unique across instances,
    preventing duplicates by hiding already-selected options in the form.

    Configuration:
        - choice_field: Name of the field containing choices (default: 'name')

    Requirements:
        - Form must be a ModelForm with a model that has the specified choice_field
        - The choice_field must have choices defined on the model field
        - The model must be queryable (e.g., not abstract)

    How it works:
        - In __init__: Filters the field's choices to exclude values already present
          in the database for other instances (excludes the current instance when editing)
        - Adds a blank choice at the top for new instances
        - Applies filtering for both new and existing instances

    Example (Basic usage):
        class MyForm(UniqueChoiceMixin, forms.ModelForm):
            class Meta:
                model = MyModel
                fields = '__all__'

    Example (Custom field name):
        class MyForm(UniqueChoiceMixin, forms.ModelForm):
            choice_field = 'level'

            class Meta:
                model = MyModel
                fields = '__all__'
    """

    choice_field = "name"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        choices = self._meta.model._meta.get_field(self.choice_field).choices  # type: ignore

        if not choices:
            return

        # Exclude values used by other instances (but allow the current instance's value)
        existing_values = self._meta.model.objects.exclude(  # type: ignore
            pk=self.instance.pk  # type: ignore
        ).values_list(self.choice_field, flat=True)
        available_choices = [
            choice for choice in choices if choice[0] not in existing_values
        ]

        # Add a blank choice only for new instances
        if not self.instance.pk:  # type: ignore
            self.fields[self.choice_field].choices = [(None, "")] + available_choices  # type: ignore
        else:
            self.fields[self.choice_field].choices = available_choices  # type: ignore
