from django.contrib import admin

from .forms import SchoolLevelForm, SchoolTermForm
from .models import SchoolLevel, SchoolTerm, TermFee


@admin.register(SchoolLevel)
class SchoolLevelAdmin(admin.ModelAdmin):
    form = SchoolLevelForm
    list_display = ("name", "alt_name", "category")
    list_filter = ("category",)


@admin.register(SchoolTerm)
class SchoolTermAdmin(admin.ModelAdmin):
    form = SchoolTermForm
    list_display = ("name",)


@admin.register(TermFee)
class TermFeeAdmin(admin.ModelAdmin):
    list_display = ("school_level_term", "amount")
    list_filter = ("term", "school_level")

    def school_level_term(self, obj):
        return f"{obj.school_level} - {obj.term}"

    school_level_term.short_description = "School Level - Term"  # type: ignore
