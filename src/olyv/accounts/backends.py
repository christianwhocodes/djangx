from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from phonenumber_field.phonenumber import PhoneNumber
import phonenumbers


class PhoneAuthBackend(ModelBackend):
    """
    Custom authentication backend that allows users to login with phone numbers
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username:
            return None

        UserModel = get_user_model()

        # Try to parse the username as a phone number
        try:
            # Try different formats for the phone number
            phone_number = self._normalize_phone_number(username)

            if phone_number:
                # Get the user with the normalized phone number
                try:
                    # Query assuming username field contains the phone number
                    user = UserModel.objects.get(username=phone_number)

                    # Check the password and return user if valid
                    if user.check_password(password):
                        return user
                    return None

                except UserModel.DoesNotExist:
                    # Run the default password hasher to mitigate timing attacks
                    UserModel().set_password(password)
                    return None
            else:
                # Invalid phone number, but don't reveal this to prevent user enumeration
                UserModel().set_password(password)
                return None

        except Exception:
            # If there's any error in phone number parsing, return None
            # Run the default password hasher to mitigate timing attacks
            UserModel().set_password(password)
            return None

    def get_user(self, user_id):
        UserModel = get_user_model()
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None

    def _normalize_phone_number(self, phone_str):
        """
        Attempt to normalize phone number to E164 format for consistent comparison
        """
        if not phone_str:
            return None

        # Handle case where input already is a PhoneNumber object
        if isinstance(phone_str, PhoneNumber):
            return phone_str.as_e164

        try:
            # First try to parse as international format
            parsed_number = phonenumbers.parse(phone_str, None)
            if phonenumbers.is_valid_number(parsed_number):
                return phonenumbers.format_number(
                    parsed_number, phonenumbers.PhoneNumberFormat.E164
                )

            # If that fails, try with a default region (you might want to make this configurable)
            parsed_number = phonenumbers.parse(
                phone_str, "KE"
            )  # Change "KE" to your default region
            if phonenumbers.is_valid_number(parsed_number):
                return phonenumbers.format_number(
                    parsed_number, phonenumbers.PhoneNumberFormat.E164
                )

        except phonenumbers.NumberParseException:
            pass

        return None


class UsernameOrEmailAuthBackend(ModelBackend):
    """
    Custom authentication backend that allows users to login with either username or email
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()

        try:
            # Query the user model with either username or email
            user = UserModel.objects.get(
                Q(username__iexact=username) | Q(email__iexact=username)
            )

            # Check the password and return user if valid
            if user.check_password(password):
                return user
            return None

        except UserModel.DoesNotExist:
            # Run the default password hasher to mitigate timing attacks
            UserModel().set_password(password)
            return None

    def get_user(self, user_id):
        UserModel = get_user_model()
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None
