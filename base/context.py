from __future__ import annotations

from typing import TYPE_CHECKING, Any, Sequence

from discord import Embed, Message
from discord.ext.commands import Context

if TYPE_CHECKING:
    from main import ProjectHyperlink


class HyperlinkContext(Context[ProjectHyperlink]):
    async def translate(
        self,
        content: str | None,
        embed: Embed | None,
        embeds: Sequence[Embed] | None,
        l10n_context: dict[str, Any] = {},
    ) -> dict[str, str | Embed | Sequence[Embed] | None]:
        l10n = await self.bot.get_l10n(self.guild.id if self.guild else 0)

        if content is not None:
            content = l10n.format_value(content, l10n_context)

        if not embeds and embed is not None:
            embeds = [embed]

        if embeds:
            for embed in embeds:
                if embed.author.name:
                    embed.author.name = l10n.format_value(embed.author.name)
                if embed.title:
                    embed.title = l10n.format_value(embed.title)

                for field in embed.fields:
                    assert field.name is not None
                    field.name = l10n.format_value(field.name)

        return dict(content=content, embeds=embeds)

    async def send(
        self,
        content: str | None = None,
        *,
        l10n_context: dict[str, Any] = {},
        **kwargs,
    ) -> Message:
        items = await self.translate(
            content,
            kwargs.pop("embed", None),
            kwargs.pop("embeds", None),
            l10n_context,
        )
        return await super().send(**items, **kwargs)

    async def reply(
        self,
        content: str | None = None,
        *,
        l10n_context: dict[str, Any] = {},
        **kwargs,
    ) -> Message:
        items = await self.translate(
            content,
            kwargs.pop("embed", None),
            kwargs.pop("embeds", None),
            l10n_context,
        )
        return await super().reply(**items, **kwargs)
