import sqlite3
from fluent.runtime import FluentLocalization, FluentResourceLoader

loader = FluentResourceLoader("l10n/{locale}")
loaded = {}

conn = sqlite3.connect('db/details.db')
c = conn.cursor()


def get_l10n(id, filename) -> FluentLocalization:
    language = c.execute(
        'select Language from guilds where ID = ?', (id,)
    ).fetchone()
    language = language[0] if language else 'en-gb'

    if (lang := loaded.get(language)) and (l10n := lang.get(filename)):
        return l10n

    if not loaded.get(language):
        loaded[language] = {}

    loaded[language][filename] = FluentLocalization([language], [f'{filename}.ftl'], loader)
    return loaded[language][filename]
