import json
from fluent.runtime import FluentLocalization, FluentResourceLoader

loader = FluentResourceLoader("l10n/{locale}")

def get_l10n(guild_id, filename):
    with open('db/guilds.json') as f:
        guild_data = json.load(f)

    language = guild_data[str(guild_id)].get('language', 'en-UK')
    return FluentLocalization([language], [f'{filename}.ftl'], loader)
