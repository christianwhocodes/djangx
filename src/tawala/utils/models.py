from django.core.exceptions import ValidationError


class OrderedChoiceMixin:
    """
    Mixin to automatically set an 'order' field based on the position of a choice
    field in its choices, in a 1-indexed way.

    Configuration:
        - choice_field: Name of the field containing choices (default: 'name')
        - order_field: Name of the field to store order (default: 'order')

    Requirements:
        - Model must have both the choice_field and order_field defined
        - The order_field should be a PositiveIntegerField with editable=False

    How it works:
        - Automatically sets the order based on the position in choices (1-indexed)
        - If choice value is not found in choices, sets order to 0
        - Order is updated every time the model is saved

    Example (Default field names):
        class MyModel(OrderedChoiceMixin, models.Model):
            class Choices(models.TextChoices):
                A = "A", "Apple"
                B = "B", "Banana"
                C = "C", "Cherry"

            name = models.CharField(choices=Choices.choices)
            order = models.PositiveIntegerField(editable=False, default=0)

            class Meta:
                ordering = ["order"]

        # When saved:
        # MyModel(name="A").save() -> order = 1
        # MyModel(name="B").save() -> order = 2
        # MyModel(name="C").save() -> order = 3

    Example (Custom field names):
        class CustomModel(OrderedChoiceMixin, models.Model):
            choice_field = 'level'
            order_field = 'position'

            class Choices(models.TextChoices):
                BEGINNER = "BEGINNER", "Beginner"
                INTERMEDIATE = "INTERMEDIATE", "Intermediate"

            level = models.CharField(choices=Choices.choices)
            position = models.PositiveIntegerField(editable=False, default=0)

            class Meta:
                ordering = ["position"]
    """

    choice_field = "name"
    order_field = "order"

    def save(self, *args, **kwargs):
        choice_value = getattr(self, self.choice_field, None)
        order_attr = getattr(self, self.order_field, None)

        if choice_value is not None and order_attr is not None:
            choices = self.get_choices()
            if choices:
                choices_values = [choice[0] for choice in choices]
                if choice_value in choices_values:
                    # Set order based on position in choices (1-indexed)
                    setattr(
                        self, self.order_field, choices_values.index(choice_value) + 1
                    )
                else:
                    # Choice not found, set order to 0
                    setattr(self, self.order_field, 0)

        super().save(*args, **kwargs)  # type: ignore

    def get_choices(self):
        """
        Retrieve the choices defined in the model's choice field.
        Override this method if the choices are defined differently.

        Returns:
            List of tuples: [(value, label), ...]
        """
        return self._meta.get_field(self.choice_field).choices  # type: ignore


class CategoryAssignmentMixin:
    """
    Mixin to automatically set a 'category' field based on a mapping from a
    choice field. Also validates that the category matches the expected value
    during model cleaning.

    Configuration:
        - choice_field: Name of the field containing choices (default: 'name')
        - category_field: Name of the field to store category (default: 'category')
        - category_mapping: Dict mapping choice values to category values (required)

    Requirements:
        - Model must have both the choice_field and category_field defined
        - The category_field should have editable=False
        - Must define category_mapping as a class attribute
        - IMPORTANT: Override save() to call self.full_clean() if you want
          validation to run automatically (Django doesn't call clean() on save by default)

    How it works:
        - In save(): Automatically sets category based on category_mapping
        - In clean(): Validates that category matches the expected value from mapping
        - If validation fails, raises ValidationError

    Important Notes:
        - If you override clean() in your model, you MUST call super().clean()
          to ensure this mixin's validation runs
        - To enable automatic validation on save, override save() to call
          self.full_clean() before super().save()
        - Django forms and admin automatically call full_clean(), but programmatic
          saves do not

    Example (Basic usage):
        class MyModel(CategoryAssignmentMixin, models.Model):
            class Choices(models.TextChoices):
                APPLE = "APPLE", "Apple"
                BANANA = "BANANA", "Banana"
                CARROT = "CARROT", "Carrot"

            class Categories(models.TextChoices):
                FRUIT = "FRUIT", "Fruit"
                VEGETABLE = "VEGETABLE", "Vegetable"

            name = models.CharField(choices=Choices.choices)
            category = models.CharField(choices=Categories.choices, editable=False)

            # Define the mapping as a class attribute
            category_mapping = {
                Choices.APPLE: Categories.FRUIT,
                Choices.BANANA: Categories.FRUIT,
                Choices.CARROT: Categories.VEGETABLE,
            }

            def save(self, *args, **kwargs):
                # Call full_clean to validate before saving
                self.full_clean()
                super().save(*args, **kwargs)

    Example (With custom clean method):
        class MyModel(CategoryAssignmentMixin, models.Model):
            # ... fields and mapping ...

            def clean(self):
                # Custom validation
                if self.name == "APPLE" and some_condition:
                    raise ValidationError("Custom error for Apple")

                # MUST call super().clean() to run CategoryAssignmentMixin validation
                super().clean()

            def save(self, *args, **kwargs):
                self.full_clean()
                super().save(*args, **kwargs)

    Example (With custom field names):
        class CustomModel(CategoryAssignmentMixin, models.Model):
            choice_field = 'level'
            category_field = 'tier'

            class Levels(models.TextChoices):
                JUNIOR = "JUNIOR", "Junior"
                SENIOR = "SENIOR", "Senior"

            class Tiers(models.TextChoices):
                ENTRY = "ENTRY", "Entry Level"
                ADVANCED = "ADVANCED", "Advanced"

            level = models.CharField(choices=Levels.choices)
            tier = models.CharField(choices=Tiers.choices, editable=False)

            category_mapping = {
                Levels.JUNIOR: Tiers.ENTRY,
                Levels.SENIOR: Tiers.ADVANCED,
            }

            def save(self, *args, **kwargs):
                self.full_clean()
                super().save(*args, **kwargs)
    """

    choice_field = "name"
    category_field = "category"
    category_mapping = {}  # Must be overridden in subclass

    def clean(self):
        """
        Validates that the category field matches the expected value from the
        category_mapping based on the choice field value.

        Raises:
            ValidationError: If category doesn't match the expected value
        """
        choice_value = getattr(self, self.choice_field, None)

        if (
            choice_value is not None
            and self.category_mapping
            and choice_value in self.category_mapping
        ):
            expected_category = self.category_mapping[choice_value]
            current_category = getattr(self, self.category_field, None)

            if current_category != expected_category:
                raise ValidationError(
                    f"The {self.category_field} for '{choice_value}' must be "
                    f"'{expected_category}', but '{current_category}' was provided."
                )

        super().clean()  # type: ignore

    def save(self, *args, **kwargs):
        """
        Automatically sets the category field based on the category_mapping
        before saving the model.
        """
        choice_value = getattr(self, self.choice_field, None)

        if choice_value is not None and self.category_mapping:
            if choice_value in self.category_mapping:
                setattr(self, self.category_field, self.category_mapping[choice_value])

        super().save(*args, **kwargs)  # type: ignore
