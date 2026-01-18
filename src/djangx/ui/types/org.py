from typing import Literal, TypeAlias

OrgKey: TypeAlias = Literal[
    "name",
    "short-name",
    "description",
    "logo-url",
    "favicon-url",
    "apple-touch-icon-url",
]

__all__: list[str] = ["OrgKey"]
