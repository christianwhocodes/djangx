"""App definitions mappings."""

from typing import Final

from ..enums import AppEnum, MiddlewareEnum, TemplateContextProcessorEnum

__all__: list[str] = ["APP_TEMPLATE_CONTEXT_PROCESSOR_MAP", "APP_MIDDLEWARE_MAP"]

APP_TEMPLATE_CONTEXT_PROCESSOR_MAP: Final[dict[AppEnum, list[TemplateContextProcessorEnum]]] = {
    AppEnum.AUTH: [TemplateContextProcessorEnum.AUTH],
    AppEnum.MESSAGES: [TemplateContextProcessorEnum.MESSAGES],
}

APP_MIDDLEWARE_MAP: Final[dict[AppEnum, list[MiddlewareEnum]]] = {
    AppEnum.SESSIONS: [MiddlewareEnum.SESSION],
    AppEnum.AUTH: [MiddlewareEnum.AUTH],
    AppEnum.MESSAGES: [MiddlewareEnum.MESSAGES],
    AppEnum.HTTP_COMPRESSION: [MiddlewareEnum.HTTP_COMPRESSION],
    AppEnum.MINIFY_HTML: [MiddlewareEnum.MINIFY_HTML],
    AppEnum.BROWSER_RELOAD: [MiddlewareEnum.BROWSER_RELOAD],
}
