from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import discord
from discord.app_commands import commands

from base.cog import HyperlinkCog
from base.context import HyperlinkContext
import cogs.checks as checks
import config

if TYPE_CHECKING:
    from main import ProjectHyperlink


class VerificationSetup(HyperlinkCog):
    """Setup Verification for a server"""

    async def cog_load(self) -> None:
        return await super().cog_load()

    verification_group = commands.Group()
    
    @commands.command(name="verification", description="Your mom")
    @commands.guild_only()
    async def foo(self, interaction: discord.Interaction) -> None:
        pass
