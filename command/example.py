import logging

from discord import app_commands, Interaction
from discord.ext import commands

from core.bot import MyBot
from core.checks import has_admin_role

log = logging.getLogger(__name__)


class Example(commands.Cog):
    """예시 명령어 Cog"""

    def __init__(self, bot: MyBot) -> None:
        self.bot = bot

    # 슬래시 명령어 이름은 공백 없이 소문자/한글/-/_ 만 사용 가능 (최대 32자)
    @app_commands.command(name="예시", description="명령어 설명")
    @app_commands.guild_only()
    @has_admin_role()
    async def example_command(self, interaction: Interaction) -> None:
        await interaction.response.send_message("테스트")


async def setup(bot: MyBot) -> None:
    await bot.add_cog(Example(bot))
    log.info("Example cog 로드 완료")
