import json
from fluent.runtime import FluentLocalization, FluentResourceLoader

loader = FluentResourceLoader("l10n/{locale}")

loaded = {}
def get_l10n(guild_id, filename):
    if (l10n := loaded.get(guild_id)) and (l10n := l10n.get(filename)):
        return l10n

    with open('db/guilds.json') as f:
        guild_data = json.load(f)

    if not loaded.get(guild_id):
        loaded[guild_id] = {}

    language = guild_data[str(guild_id)].get('language', 'en-gb')
    loaded[guild_id][filename] = FluentLocalization([language], [f'{filename}.ftl'], loader)

    return loaded[guild_id][filename]
