import config

ALL_EXTENSIONS = [
    "cogs.drive",
    "cogs.errors.handler",
    "cogs.events",
    "cogs.help",
    "cogs.info",
    "cogs.logger",
    "cogs.owner",
    "cogs.prefix",
    "cogs.verification",
]

if config.TESTING_MODE is True:
    INITIAL_EXTENSIONS = [
        "cogs.owner",
        # "cogs.",
    ]
else:
    INITIAL_EXTENSIONS = ALL_EXTENSIONS
