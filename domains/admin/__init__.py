"""관리자 도메인: 확장 기능 관리 명령어 (/dev reload, /dev load ...)"""
import logging

from core.bot import MyBot
from .commands import DevCommands

log = logging.getLogger(__name__)


async def setup(bot: MyBot) -> None:
    await bot.add_cog(DevCommands(bot))
    log.info("DevCommands cog 로드 완료")
