"""예시 도메인: 새 도메인을 만들 때 이 폴더를 복사해서 시작하세요"""
import logging

from core.bot import MyBot
from .commands import Example

log = logging.getLogger(__name__)


async def setup(bot: MyBot) -> None:
    await bot.add_cog(Example(bot))
    log.info("Example cog 로드 완료")
