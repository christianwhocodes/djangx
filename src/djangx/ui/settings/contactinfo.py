# ==============================================================================
# Email Configuration
# https://docs.djangoproject.com/en/stable/topics/email/
# ==============================================================================
from ... import Conf, ConfField


class ContactInfoAddressConf(Conf):
    """ContactInfo Address configuration settings."""

    country = ConfField(
        env="CONTACTINFO_ADDRESS_COUNTRY",
        toml="contactinfo.address.country",
        type=str,
    )
    state = ConfField(env="CONTACTINFO_ADDRESS_STATE", toml="contactinfo.address.state", type=str)
    city = ConfField(env="CONTACTINFO_ADDRESS_CITY", toml="contactinfo.address.city", type=str)
    street = ConfField(env="CONTACTINFO_ADDRESS_STREET", toml="contactinfo.address.street", type=str)


class ContactInfoEmailConf(Conf):
    """ContactInfo Email configuration settings."""

    primary = ConfField(env="CONTACTINFO_EMAIL_PRIMARY", toml="contactinfo.email.primary", type=str)
    additional = ConfField(
        env="CONTACTINFO_EMAIL_ADDITIONAL",
        toml="contactinfo.email.additional",
        type=list,
    )


class ContactInfoPhoneConf(Conf):
    """ContactInfo Phone Number configuration settings."""

    primary = ConfField(
        env="CONTACTINFO_NUMBER_PRIMARY", toml="contactinfo.number.primary", type=str
    )
    additional = ConfField(
        env="CONTACTINFO_NUMBER_ADDITIONAL",
        toml="contactinfo.number.additional",
        type=list,
    )


CONTACTINFO_ADDRESS = ContactInfoAddressConf()
CONTACTINFO_EMAIL = ContactInfoEmailConf()
CONTACTINFO_PHONE = ContactInfoPhoneConf()


class EmailConf(Conf):
    """Email configuration settings."""

    backend = ConfField(env="EMAIL_BACKEND", toml="email.backend", type=str)
    host = ConfField(env="EMAIL_HOST", toml="email.host", type=str)
    port = ConfField(env="EMAIL_PORT", toml="email.port", type=str)
    use_tls = ConfField(env="EMAIL_USE_TLS", toml="email.use-tls", type=bool)
    host_user = ConfField(env="EMAIL_HOST_USER", toml="email.host-user", type=str)
    host_password = ConfField(env="EMAIL_HOST_PASSWORD", toml="email.host-password", type=str)


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
