"""Custom authentication backends for Django."""

from typing import TYPE_CHECKING, Any, Optional

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from django.http import HttpRequest

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractBaseUser


__all__: list[str] = ["UsernameOrEmailBackend"]


class UsernameOrEmailBackend(ModelBackend):
    """Custom authentication backend that allows users to login with either username or email."""

    def authenticate(
        self,
        request: Optional[HttpRequest],
        username: Optional[str] = None,
        password: Optional[str] = None,
        **kwargs: Any,
    ) -> "Optional[AbstractBaseUser]":
        """Authenticate user with username or email."""
        if username is None or password is None:
            return None

        User = get_user_model()

        try:
            # Query the user model with either username or email
            user = User.objects.get(Q(username__iexact=username) | Q(email__iexact=username))

            # Check the password and return user if valid
            if user.check_password(password):
                return user
            return None

        except User.DoesNotExist:
            # Run the default password hasher to mitigate timing attacks
            User().set_password(User.objects.make_random_password())
            return None
