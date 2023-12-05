from __future__ import annotations

from typing import TYPE_CHECKING

from .affiliates import AffiliateVerification
from .clubs import ClubVerification
from .verification import EntryPoint

if TYPE_CHECKING:
    from main import ProjectHyperlink


class Verification(AffiliateVerification, ClubVerification, EntryPoint):
    """The Great Wall of NITKKR"""


async def setup(bot: ProjectHyperlink):
    await bot.add_cog(Verification(bot))
