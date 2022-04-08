from fluent.runtime import FluentLocalization, FluentResourceLoader

loader = FluentResourceLoader("l10n/{locale}")
loaded = {}

languages: dict[int, str] = {}


async def get_l10n(id: int, filename: str, conn) -> FluentLocalization:
    if not (language := languages.get(id)):
        languages[id] = await conn.fetchval(
            'SELECT language FROM guild WHERE id = $1', id
        ) or 'en-GB'

    if (lang := loaded.get(language)) and (l10n := lang.get(filename)):
        return l10n

    if not loaded.get(language):
        loaded[language] = {}

    loaded[language][filename] = FluentLocalization([language], [f'{filename}.ftl'], loader)
    return loaded[language][filename]
