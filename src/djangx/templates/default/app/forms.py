from django import forms
from djangx.utils.forms.mixins import UniqueChoiceMixin

from .models import SchoolLevel, SchoolTerm


class SchoolLevelForm(UniqueChoiceMixin, forms.ModelForm):
    class Meta:
        model = SchoolLevel
        fields = "__all__"


class SchoolTermForm(UniqueChoiceMixin, forms.ModelForm):
    class Meta:
        model = SchoolTerm
        fields = "__all__"
