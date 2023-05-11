import config

ALL_EXTENSIONS = [
    "cogs.drive",
    "cogs.errors.handler",
    "cogs.events",
    "cogs.help",
    "cogs.ign",
    "cogs.info",
    "cogs.logger",
    "cogs.mod",
    "cogs.owner",
    "cogs.prefix",
    "cogs.self_roles",
    "cogs.tag",
    "cogs.verification",
]

if config.dev is True:
    INITIAL_EXTENSIONS = [
        "cogs.owner",
        # "cogs.",
    ]
else:
    INITIAL_EXTENSIONS = ALL_EXTENSIONS
