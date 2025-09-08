from functools import wraps

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.conf import settings

from ..management.config.auth import auth_config


def auth_page_required(page_name):
    """
    View decorator to conditionally disable access to an authentication-related page.

    This is useful when certain pages like 'signin', 'signup', or others need to be
    temporarily disabled via config. It handles both standard browser requests and
    JSON/API (XHR) requests gracefully.

    Args:
        page_name (str): The key name for the page in the auth config.

    Returns:
        function: A decorator that wraps the view to block access if the page is disabled.
    """

    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not auth_config.is_enabled(page_name):
                # For API or AJAX requests
                if (
                    request.headers.get("Content-Type") == "application/json"
                    or request.headers.get("X-Requested-With") == "XMLHttpRequest"
                ):
                    return JsonResponse(
                        {"error": f"{page_name} is currently unavailable."}, status=403
                    )

                # For standard browser-based views
                messages.warning(
                    request,
                    f"{page_name.title()} is currently unavailable.",
                    extra_tags="auth_page_required",
                )
                return redirect(getattr(settings, "HOME_URL", "/"))

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


def auth_page_required_class(page_name):
    """
    Class-based view decorator to conditionally disable access to an auth-related view.

    This applies `auth_page_required(page_name)` to the `dispatch` method of a class-based view,
    ensuring that the access check is performed regardless of HTTP method (GET, POST, etc.).

    Args:
        page_name (str): The key name for the page in the auth config.

    Returns:
        function: A class decorator that restricts access if the page is disabled.
    """

    def decorator(cls):
        cls.dispatch = method_decorator(auth_page_required(page_name))(cls.dispatch)
        return cls

    return decorator


def redirect_authenticated_users(view_func):
    """
    Decorator to redirect authenticated users away from auth-only views like signin/signup.
    """

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(getattr(settings, "HOME_URL", "/"))
        return view_func(request, *args, **kwargs)

    return _wrapped_view


def redirect_authenticated_users_class(view_class):
    """
    Class-based version of redirect_authenticated_users decorator.
    Redirects authenticated users from views like SignUpView.
    """

    view_class.dispatch = method_decorator(redirect_authenticated_users)(
        view_class.dispatch
    )
    return view_class
