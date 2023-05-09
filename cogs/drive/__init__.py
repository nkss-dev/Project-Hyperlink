from __future__ import annotations

from typing import TYPE_CHECKING

from .drive import Drive

if TYPE_CHECKING:
    from main import ProjectHyperlink


async def setup(bot: ProjectHyperlink):
    await bot.add_cog(Drive(bot))
