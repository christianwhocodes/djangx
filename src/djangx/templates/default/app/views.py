from django.views.generic import TemplateView


class HomePage(TemplateView):
    template_name = "app/home.html"
    extra_context = {
        "page_title": "The Spark Playhouse",
    }
