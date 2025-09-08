from django.contrib import messages
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.shortcuts import get_object_or_404, render

from olyv.base.forms import SearchForm

from .forms import ArticleCommentForm
from .models import Article, ArticleCategory, ArticleTag


def blog(request):
    articles = Article.objects.order_by("-date_created")
    categories = ArticleCategory.objects

    category = request.GET.get("category")
    tag = request.GET.get("tag")
    text = request.GET.get("text")

    # Check if the text matches a tag or category
    tag_exists = ArticleTag.objects.filter(name=text).exists()
    category_exists = categories.filter(name=text).exists()

    if text:
        if tag_exists:
            tag = text
        elif category_exists:
            category = text

    if category:
        articles = articles.filter(category__name=category)
    if tag:
        articles = articles.filter(tags__name=tag)

    paginator = Paginator(articles, 4)
    page_number = request.GET.get("page")

    try:
        blog_articles = paginator.page(page_number)
    except PageNotAnInteger:
        blog_articles = paginator.page(1)
    except EmptyPage:
        blog_articles = paginator.page(paginator.num_pages)

    context = {
        "has_header": True,
        "has_footer": True,
        "page_title": "Blog",
        "blog_active": "active",
        "articles": articles,
        "blog_articles": blog_articles,
        "categories": categories,
        "searchform": SearchForm(),
    }

    if category:
        context["filtered_category"] = category
    if tag:
        context["filtered_tag"] = tag

    return render(request, "blog/blogpage.html", context)


def details(request, pk):
    article = get_object_or_404(Article, id=pk)
    articles = Article.objects.order_by("-date_created")
    categories = ArticleCategory.objects
    tags = article.tags
    comments = article.comment_set.all()

    context = {
        "has_header": True,
        "has_footer": True,
        "page_title": article.title,
        "single_article": article,
        "articles": articles,
        "categories": categories,
        "tags": tags,
        "searchform": SearchForm(),
        "comments": comments,
    }

    category = request.GET.get("category")

    if category:
        articles = articles.filter(category__name=category)
        context["filtered_category"] = category

    if request.method == "POST":
        filled_form = ArticleCommentForm(request.POST)
        if filled_form.is_valid():
            new_comment = filled_form.save(commit=False)
            new_comment.article = article  # Set the article for the comment
            new_comment.save()
            messages.success(request, "Comment submitted successfully!")
            context["replyform"] = ArticleCommentForm()
        else:
            messages.error(request, "There was an error posting your comment")
            context["replyform"] = ArticleCommentForm(request.POST)
            print(filled_form.errors)
    else:
        context["replyform"] = ArticleCommentForm()

    return render(request, "blog/blogpage.html", context)
