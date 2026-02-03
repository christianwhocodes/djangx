# ==============================================================================
# Email Configuration
# https://docs.djangoproject.com/en/stable/topics/email/
# ==============================================================================
from ... import Conf, ConfField


class ContactInfoAddressConf(Conf):
    """ContactInfo Address configuration settings."""

    country = ConfField(
        type=str,
        env="CONTACTINFO_ADDRESS_COUNTRY",
        toml="contactinfo.address.country",
        default="",
    )
    state = ConfField(
        type=str,
        env="CONTACTINFO_ADDRESS_STATE",
        toml="contactinfo.address.state",
        default="",
    )
    city = ConfField(
        type=str,
        env="CONTACTINFO_ADDRESS_CITY",
        toml="contactinfo.address.city",
        default="",
    )
    street = ConfField(
        type=str,
        env="CONTACTINFO_ADDRESS_STREET",
        toml="contactinfo.address.street",
        default="",
    )


class ContactInfoEmailConf(Conf):
    """ContactInfo Email configuration settings."""

    primary = ConfField(
        type=str,
        env="CONTACTINFO_EMAIL_PRIMARY",
        toml="contactinfo.email.primary",
        default="",
    )
    additional = ConfField(
        type=list,
        env="CONTACTINFO_EMAIL_ADDITIONAL",
        toml="contactinfo.email.additional",
        default=[],
    )


class ContactInfoPhoneConf(Conf):
    """ContactInfo Phone Number configuration settings."""

    primary = ConfField(
        type=str,
        env="CONTACTINFO_NUMBER_PRIMARY",
        toml="contactinfo.number.primary",
        default="",
    )
    additional = ConfField(
        type=list,
        env="CONTACTINFO_NUMBER_ADDITIONAL",
        toml="contactinfo.number.additional",
        default=[],
    )


CONTACTINFO_ADDRESS = ContactInfoAddressConf()
CONTACTINFO_EMAIL = ContactInfoEmailConf()
CONTACTINFO_PHONE = ContactInfoPhoneConf()


class EmailConf(Conf):
    """Email configuration settings."""

    backend = ConfField(
        type=str,
        env="EMAIL_BACKEND",
        toml="email.backend",
        default="django.core.mail.backends.smtp.EmailBackend",
    )
    host = ConfField(
        type=str,
        env="EMAIL_HOST",
        toml="email.host",
        default="",
    )
    use_tls = ConfField(
        type=bool,
        env="EMAIL_USE_TLS",
        toml="email.use-tls",
        default=False,
    )
    use_ssl = ConfField(
        type=bool,
        env="EMAIL_USE_SSL",
        toml="email.use-ssl",
        default=False,
    )
    port = ConfField(
        type=str,
        env="EMAIL_PORT",
        toml="email.port",
        default="",
    )
    host_user = ConfField(
        type=str,
        env="EMAIL_HOST_USER",
        toml="email.host-user",
        default="",
    )
    host_password = ConfField(
        type=str,
        env="EMAIL_HOST_PASSWORD",
        toml="email.host-password",
        default="",
    )


_EMAIL = EmailConf()

EMAIL_BACKEND: str = _EMAIL.backend
EMAIL_HOST: str = _EMAIL.host
EMAIL_PORT: str = _EMAIL.port
EMAIL_USE_TLS: bool = _EMAIL.use_tls
EMAIL_HOST_USER: str = _EMAIL.host_user
EMAIL_HOST_PASSWORD: str = _EMAIL.host_password


__all__: list[str] = [
    "CONTACTINFO_ADDRESS",
    "CONTACTINFO_EMAIL",
    "CONTACTINFO_PHONE",
    "EMAIL_BACKEND",
    "EMAIL_HOST",
    "EMAIL_PORT",
    "EMAIL_USE_TLS",
    "EMAIL_HOST_USER",
    "EMAIL_HOST_PASSWORD",
]
