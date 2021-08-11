from fluent.runtime import FluentLocalization, FluentResourceLoader

loader = FluentResourceLoader("l10n/{locale}")
l10n = FluentLocalization(["en-US"], ["main.ftl"], loader)
