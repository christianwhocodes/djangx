from django.core.exceptions import ValidationError
from django.db import models
from djangx.utils.models.fields import calculate_max_length_from_choices
from djangx.utils.models.mixins import CategoryAssignmentMixin, OrderedChoiceMixin


class SchoolLevel(OrderedChoiceMixin, CategoryAssignmentMixin, models.Model):
    """
    Model representing different school levels.
    """

    class Levels(models.TextChoices):
        """Available school levels in order"""

        BEGINNER = "BEGINNER", "Beginner"
        PP1 = "PP1", "Pre-Primary 1"
        PP2 = "PP2", "Pre-Primary 2"
        GRADE_1 = "GRADE_1", "Grade 1"
        GRADE_2 = "GRADE_2", "Grade 2"
        GRADE_3 = "GRADE_3", "Grade 3"
        GRADE_4 = "GRADE_4", "Grade 4"
        GRADE_5 = "GRADE_5", "Grade 5"
        GRADE_6 = "GRADE_6", "Grade 6"
        GRADE_7 = "GRADE_7", "Grade 7"
        GRADE_8 = "GRADE_8", "Grade 8"
        GRADE_9 = "GRADE_9", "Grade 9"
        GRADE_10 = "GRADE_10", "Grade 10"
        GRADE_11 = "GRADE_11", "Grade 11"
        GRADE_12 = "GRADE_12", "Grade 12"

    class Categories(models.TextChoices):
        """Education level categories"""

        PRE_SCHOOL = "PRE_SCHOOL", "Pre-School"
        PRE_PRIMARY = "PRE_PRIMARY", "Pre-Primary"
        PRIMARY = "PRIMARY", "Primary"
        JUNIOR_SECONDARY_SCHOOL = "JUNIOR_SECONDARY_SCHOOL", "Junior Secondary School"
        SENIOR_SECONDARY_SCHOOL = "SENIOR_SECONDARY_SCHOOL", "Senior Secondary School"

    # Fields
    name = models.CharField(
        max_length=calculate_max_length_from_choices(Levels.choices),
        unique=True,
        choices=Levels.choices,
        help_text="The school level name",
    )
    alt_name = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Alternative Name",
        help_text="Alternative name for the school level (optional)",
    )
    description = models.TextField(
        blank=True, help_text="Optional description of this school level"
    )
    category = models.CharField(
        max_length=calculate_max_length_from_choices(Categories.choices),
        choices=Categories.choices,
        editable=False,
        help_text="Education category (automatically assigned)",
    )
    order = models.PositiveIntegerField(
        editable=False,
        default=0,
        help_text="Display order (automatically assigned based on position in choices)",
    )

    # Category mapping configuration for CategoryAssignmentMixin
    category_mapping = {
        Levels.BEGINNER: Categories.PRE_SCHOOL,
        Levels.PP1: Categories.PRE_PRIMARY,
        Levels.PP2: Categories.PRE_PRIMARY,
        Levels.GRADE_1: Categories.PRIMARY,
        Levels.GRADE_2: Categories.PRIMARY,
        Levels.GRADE_3: Categories.PRIMARY,
        Levels.GRADE_4: Categories.PRIMARY,
        Levels.GRADE_5: Categories.PRIMARY,
        Levels.GRADE_6: Categories.PRIMARY,
        Levels.GRADE_7: Categories.JUNIOR_SECONDARY_SCHOOL,
        Levels.GRADE_8: Categories.JUNIOR_SECONDARY_SCHOOL,
        Levels.GRADE_9: Categories.JUNIOR_SECONDARY_SCHOOL,
        Levels.GRADE_10: Categories.SENIOR_SECONDARY_SCHOOL,
        Levels.GRADE_11: Categories.SENIOR_SECONDARY_SCHOOL,
        Levels.GRADE_12: Categories.SENIOR_SECONDARY_SCHOOL,
    }

    class Meta:
        ordering = ["order"]
        unique_together = ["name", "category"]

    def get_term_fee(self, term):
        """
        Returns the fee amount for the given term, or None if not found.

        Args:
            term: A SchoolTerm instance (e.g., SchoolTerm.objects.get(name=SchoolTerm.Terms.TERM_1))

        Returns:
            Decimal or None: The fee amount for the term, or None if no fee exists.
        """
        try:
            return self.term_fees.get(term=term).amount  # type: ignore
        except TermFee.DoesNotExist:
            return None

    def __str__(self):
        return self.get_name_display()  # type: ignore


class SchoolTerm(OrderedChoiceMixin, models.Model):
    """
    Model representing academic terms.
    """

    class Terms(models.TextChoices):
        """Available academic terms in order"""

        TERM_1 = "TERM_1", "Term 1"
        TERM_2 = "TERM_2", "Term 2"
        TERM_3 = "TERM_3", "Term 3"

    # Fields
    name = models.CharField(
        max_length=calculate_max_length_from_choices(Terms.choices),
        unique=True,
        choices=Terms.choices,
        help_text="The academic term name",
    )
    order = models.PositiveIntegerField(
        editable=False,
        default=0,
        help_text="Display order (automatically assigned based on position in choices)",
    )

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.get_name_display()  # type: ignore


class TermFee(models.Model):
    """
    Model representing the fee structure for each school level per term.

    Example Usage:
        # Create fees for a school level
        level = SchoolLevel.objects.get(name=SchoolLevel.Levels.BEGINNER)
        term1 = SchoolTerm.objects.get(name=SchoolTerm.Terms.TERM_1)

        TermFee.objects.create(
            school_level=level,
            term=term1,
            amount=11500
        )

        # Query fees for a level
        beginner_fees = TermFee.objects.filter(school_level=level)

        # Get specific term fee
        term1_fee = TermFee.objects.get(
            school_level=level,
            term=term1
        )
    """

    school_level = models.ForeignKey(
        SchoolLevel,
        on_delete=models.CASCADE,
        related_name="term_fees",
        help_text="The school level this fee applies to",
    )
    term = models.ForeignKey(
        SchoolTerm,
        on_delete=models.CASCADE,
        help_text="Academic term",
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Fee amount in KES",
    )

    class Meta:
        ordering = ["school_level__order", "term__order"]
        unique_together = ["school_level", "term"]

    def clean(self):
        """Validate that the fee amount is positive."""
        super().clean()
        if self.amount is not None and self.amount <= 0:
            raise ValidationError({"amount": "Fee amount must be greater than zero."})

    def save(self, *args, **kwargs):
        """Override save to call full_clean() before saving."""
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.school_level} - {self.term}: KES {self.amount}"  # type: ignore


class LearnerProfile(models.Model):
    """
    Model representing a learner enrolled in a specific school level.

    Example Usage:
        level = SchoolLevel.objects.get(name=SchoolLevel.Levels.GRADE1)
        learner = LearnerProfile.objects.create(
            school_level=level,
            first_name="John",
            last_name="Doe"
        )
    """

    school_level = models.ForeignKey(
        SchoolLevel,
        on_delete=models.CASCADE,
        related_name="learners",
        help_text="The school level this learner is enrolled in",
    )
    first_name = models.CharField(max_length=30, help_text="Learner's first name")
    last_name = models.CharField(max_length=30, help_text="Learner's last name")
    other_names = models.CharField(
        max_length=50,
        blank=True,
        help_text="Learner's other names (optional)",
    )

    @property
    def full_name(self):
        """Returns the learner's full name."""
        names = [self.first_name]
        if self.other_names:
            names.append(self.other_names)
        names.append(self.last_name)
        return " ".join(names)

    date_of_birth = models.DateField(
        null=True,
        blank=True,
        help_text="Learner's date of birth (optional)",
    )
    enrollment_date = models.DateField(
        auto_now_add=True,
        help_text="Date when the learner was enrolled",
    )

    def __str__(self):
        return f"{self.full_name} - {self.school_level.get_name_display()}"  # type: ignore
