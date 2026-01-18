from typing import Literal, TypeAlias

SocialKey: TypeAlias = Literal[
    "facebook",
    "twitter-x",
    "instagram",
    "linkedin",
    "whatsapp",
    "youtube",
]


__all__: list[str] = ["SocialKey"]
