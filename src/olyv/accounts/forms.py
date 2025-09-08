from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.models import Group


class UserForm(UserChangeForm):
    class Meta:
        model = get_user_model()
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        self._current_user = kwargs.pop("current_user", None)
        super().__init__(*args, **kwargs)

        # Only modify username field if it exists
        if "username" in self.fields:
            auth_username = getattr(settings, "AUTH_USERNAME", {})
            self.fields["username"].label = auth_username.get("label", "Username")
            self.fields["username"].widget.attrs["placeholder"] = auth_username.get(
                "placeholder", "Enter your username"
            )

        # Filter groups field to hide "superuser" group for non-superusers
        if (
            "groups" in self.fields
            and self._current_user
            and not self._current_user.is_superuser
        ):
            self.fields["groups"].queryset = Group.objects.exclude(name="superuser")
            # You'll need to pass the request user to the form (see admin class modification below)
            current_user = getattr(self, "_current_user", None)

            if current_user and not current_user.is_superuser:
                # Exclude the "superuser" group from the queryset
                self.fields["groups"].queryset = Group.objects.exclude(name="superuser")
