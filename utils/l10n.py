import json
from fluent.runtime import FluentLocalization, FluentResourceLoader

loader = FluentResourceLoader("l10n/{locale}")

loaded = {}
def get_l10n(id, filename):
    with open('db/guilds.json') as f:
        guild_data = json.load(f)
    language = guild_data[str(id)].get('language', 'en-gb') if id else 'en-gb'

    if (l10n := loaded.get(language)) and (l10n := l10n.get(filename)):
        return l10n

    if not loaded.get(language):
        loaded[language] = {}

    loaded[language][filename] = FluentLocalization([language], [f'{filename}.ftl'], loader)
    return loaded[language][filename]
