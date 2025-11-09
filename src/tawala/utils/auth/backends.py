from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from django.http import HttpRequest

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractBaseUser


class UsernameOrEmailBackend(ModelBackend):
    """
    Custom authentication backend that allows users to login with either username or email.

    Usage:
        Add to settings.py:

        AUTHENTICATION_BACKENDS = [
            'tawala.utils.auth.backends.UsernameOrEmailBackend',
            'django.contrib.auth.backends.ModelBackend',  # default
        ]
    """

    def authenticate(
        self,
        request: HttpRequest | None,
        username: str | None = None,
        password: str | None = None,
        **kwargs,
    ) -> "AbstractBaseUser | None":
        if username is None or password is None:
            return None

        User = get_user_model()

        try:
            # Query the user model with either username or email
            user = User.objects.get(
                Q(username__iexact=username) | Q(email__iexact=username)
            )

            # Check the password and return user if valid
            if user.check_password(password):
                return user
            return None

        except User.DoesNotExist:
            # Run the default password hasher to mitigate timing attacks
            User().set_password(User.objects.make_random_password())
            return None
