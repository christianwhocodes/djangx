from django import forms
from django_ckeditor_5.widgets import CKEditor5Widget

from .models import Article, ArticleComment


class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = "__all__"
        widgets = {
            "content": CKEditor5Widget(
                attrs={"class": "django_ckeditor_5"}, config_name="extends"
            )
        }


class ArticleCommentForm(forms.ModelForm):
    class Meta:
        model = ArticleComment
        fields = ("name", "email", "website", "content")
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Feature Coming Soon",
                    "disabled": "disabled",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Feature Coming Soon",
                    "disabled": "disabled",
                }
            ),
            "website": forms.URLInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Feature Coming Soon",
                    "disabled": "disabled",
                }
            ),
            "content": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": "3",
                    "placeholder": "Feature Coming Soon",
                    "disabled": "disabled",
                }
            ),
        }
