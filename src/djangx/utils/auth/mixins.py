"""Custom authentication mixins for Django class-based views (CBVs).

Plain-language overview
- A "view" is a Python class that receives a web request and returns a response.
- A "mixin" is a small helper class that you combine with a view to add behavior.
  You stack mixins from left-to-right, then put the actual view base class (like TemplateView) last:
    class MyView(SomeMixin, AnotherMixin, TemplateView): ...
- Django views use a method called "dispatch" to route the incoming request to the right handler
  based on the HTTP method (GET, POST, etc.). Mixins commonly override dispatch to add checks
  before letting the normal view logic run.

Why super() is used here
- Each mixin does a bit of work and then calls super().dispatch(...). This means:
  "I've done my part; now let the next class in the chain handle the request."
- The "chain" is determined by Python's Method Resolution Order (MRO): the order Python searches
  for methods in your multiple-inheritance class. Using super() keeps all mixins cooperative,
  so they can run in order without skipping each other.

About AccessMixin, LoginRequiredMixin, and UserPassesTestMixin
- AccessMixin provides helper methods for "what to do when access is denied" (redirect to login,
  or return a 403 Forbidden). It doesn't itself enforce rules; it just standardizes responses.
- LoginRequiredMixin ensures the user is authenticated; otherwise it triggers AccessMixin behavior.
- UserPassesTestMixin lets you define a test_func() that returns True/False. If False, it also triggers
  AccessMixin behavior (redirect or 403).

What this module provides
- AnonymousRequiredMixin: allows ONLY anonymous (not logged-in) users to visit a page (typical for login/signup pages).
  If a logged-in user hits the page, they are redirected away.
- StaffRequiredMixin: allows only authenticated staff members. Non-authenticated users are redirected to login;
  authenticated non-staff can be redirected or receive a 403, depending on settings.

Important implementation detail
- These mixins DO NOT subclass django.views.View directly. This keeps the "cooperative" super() chain predictable
  and avoids pulling View earlier into the MRO than intended. In practice, you will combine these mixins with a real
  view class (e.g., TemplateView, ListView), and that view class ultimately provides dispatch.

Type-checking note
- Some static type checkers (like Pylance/Pyright) cannot always prove that super().dispatch exists on the "next" class
  at type-check time. The code is correct at runtime when used with a real Django CBV. Where noted, we add a small
  "# pyright: ignore[reportAttributeAccessIssue]" to silence that specific false positive.
"""

from __future__ import annotations

from django.conf import settings
from django.contrib.auth.mixins import (
    AccessMixin,
    LoginRequiredMixin,
    UserPassesTestMixin,
)
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, resolve_url


class AnonymousRequiredMixin(AccessMixin):
    """Allow only anonymous (not authenticated) users to access the view.

    What it does in simple terms:
    - If the visitor is already logged in, we redirect them elsewhere (e.g., a dashboard).
    - If the visitor is not logged in, we let the normal view logic continue.

    How it works:
    - We override dispatch (the entry point for GET/POST/etc.).
    - We check request.user.is_authenticated. If True, we redirect immediately.
    - Otherwise, we call super().dispatch(...) so the rest of the view stack can handle the request.

    Where the user is redirected:
    - If you set `redirect_url` on your view, we send them there.
    - Otherwise we fall back to settings.LOGIN_REDIRECT_URL, or "/" if not set.
    - `redirect_url` can be:
        - a URL pattern name (e.g., "dashboard"),
        - a relative path ("/dashboard/"),
        - or an absolute URL ("https://example.com/").
      We use resolve_url(...) so all of these forms work.

    Example usage:
        class LoginView(AnonymousRequiredMixin, TemplateView):
            template_name = "auth/login.html"
            redirect_url = "dashboard"  # Optional override; otherwise uses LOGIN_REDIRECT_URL

    Why we inherit from AccessMixin:
    - AccessMixin provides consistent "permission denied" helpers used across Django's auth mixins.
      We don't use them directly here (we just redirect), but inheriting keeps behavior consistent and
      lets you extend this mixin similarly to Django's own mixins if needed.
    """

    # Destination for already-authenticated users.
    # If None: defaults to settings.LOGIN_REDIRECT_URL (or "/" as a final fallback).
    redirect_url: str | None = None

    def get_redirect_url(self) -> str:
        """Return the absolute URL to send already-authenticated users to.

        We compute the target as:
        - self.redirect_url if you set it on the view; otherwise
        - settings.LOGIN_REDIRECT_URL if defined; otherwise
        - "/"

        We pass that value through django.shortcuts.resolve_url so it can be a URL name,
        a relative path, or a full URL, and it will be resolved to a usable URL string.
        """
        to = self.redirect_url or getattr(settings, "LOGIN_REDIRECT_URL", "/")
        return resolve_url(to)

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Entry point for handling the request (GET/POST/etc.).

        - If the user is authenticated, immediately redirect them away using get_redirect_url().
        - Otherwise, call super().dispatch(...) to continue normal processing by the next class
          in the MRO (e.g., TemplateView/View), which will eventually route to get/post/etc.
        """
        if request.user.is_authenticated:
            return redirect(self.get_redirect_url())
        # Type checkers may not know the next class has `dispatch`, but in Django CBVs it will.
        return super().dispatch(request, *args, **kwargs)  # pyright: ignore[reportAttributeAccessIssue]


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Allow access only to authenticated users who are staff members.

    What it does in simple terms:
    - First ensures the user is logged in (LoginRequiredMixin behavior).
      If not, the user is redirected to the login page (with a ?next=... return URL).
    - Then applies a custom test (UserPassesTestMixin) that checks user.is_staff.
      If the test fails, the mixin either:
        - redirects (default AccessMixin behavior), or
        - returns a 403 Forbidden if you set `raise_exception = True` on the view.

    Customization knobs you can set on the view:
    - login_url: where to send unauthenticated users (defaults to settings.LOGIN_URL).
    - redirect_field_name: the name of the "return here after login" parameter (defaults to "next").
    - raise_exception: if True, return a 403 instead of redirecting on failure (default False).
    - permission_denied_message: message used when raising 403.

    Execution order in the MRO:
    - Your view should be declared like: class MyView(StaffRequiredMixin, TemplateView): ...
    - The MRO will ensure that LoginRequiredMixin checks authentication first.
    - Then UserPassesTestMixin will call self.test_func() (defined below).
    - If both pass, control continues to the base view (TemplateView/View) to render the page.

    Example usage:
        class StaffDashboardView(StaffRequiredMixin, TemplateView):
            template_name = "staff/dashboard.html"
            raise_exception = True  # Return 403 if not staff (instead of redirect)
            permission_denied_message = "Staff access only."
    """

    # Optional: message on permission failure (used if raise_exception=True).
    permission_denied_message = "You do not have permission to access this page."
    # If you prefer a 403 for non-staff, set this on the view class:
    # raise_exception = True

    def test_func(self) -> bool:
        """Return True if the current user passes the "staff" test.

        This method is called by UserPassesTestMixin during dispatch, after LoginRequiredMixin
        has already ensured the user is authenticated (or redirected them to login if not).

        Note:
        - On class-based views, Django sets self.request during dispatch, so by the time this
          method runs, self.request is available and contains the current HttpRequest.
        """
        user = self.request.user  # pyright: ignore[reportAttributeAccessIssue]
        return bool(user and user.is_authenticated and user.is_staff)


__all__ = ["AnonymousRequiredMixin", "StaffRequiredMixin"]
