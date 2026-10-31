from collections.abc import Iterable

import discord
from discord import app_commands, Interaction
from discord.ext import commands

from core.bot import MyBot
from domains.responses import respond
from . import service
from .service import Result


# GroupCog 클래스에 붙인 app_commands.check는 하위 명령어에 적용되지 않으므로
# 권한 확인은 interaction_check에서 처리 (guild_only, default_permissions는 그룹에 적용됨)
# default_permissions: 서버 관리자 외에는 명령어 목록에서 숨김 (서버 설정 > 연동에서 역할별 허용 가능)
@app_commands.guild_only()
@app_commands.default_permissions(administrator=True)
class DevCommands(commands.GroupCog, group_name="dev", group_description="개발자용 명령어"):
    """개발자를 위한 명령어 관리 Cog. 실제 처리는 service, 여기서는 입력과 응답만 담당"""

    def __init__(self, bot: MyBot) -> None:
        self.bot = bot
        super().__init__()

    async def interaction_check(self, interaction: Interaction) -> bool:
        """모든 /dev 하위 명령어에 적용되는 관리자 역할 체크 (실패 시 CheckFailure)"""
        return self.bot.is_admin(interaction.user)

    def _choices(self, interaction: Interaction, current: str, names: Iterable[str]) -> list[app_commands.Choice[str]]:
        # 자동완성은 interaction_check를 거치지 않으므로 직접 확인
        if not self.bot.is_admin(interaction.user):
            return []
        return [
            app_commands.Choice(name=name, value=name)
            for name in names
            if current.lower() in name.lower()
        ][:25]

    async def loaded_autocomplete(self, interaction: Interaction, current: str) -> list[app_commands.Choice[str]]:
        return self._choices(interaction, current, service.loaded_extensions(self.bot))

    async def unloaded_autocomplete(self, interaction: Interaction, current: str) -> list[app_commands.Choice[str]]:
        return self._choices(interaction, current, service.unloaded_extensions(self.bot))

    @app_commands.command(name="reload", description="지정한 도메인을 다시 로드합니다")
    @app_commands.describe(extension="다시 로드할 확장 기능 이름 (예: domains.example)")
    @app_commands.autocomplete(extension=loaded_autocomplete)
    @respond()
    async def reload_command(self, interaction: Interaction, extension: str) -> Result:
        return await service.reload_extension(self.bot, extension.strip())

    @app_commands.command(name="load", description="새 도메인을 로드합니다")
    @app_commands.describe(extension="로드할 확장 기능 이름 (예: domains.example)")
    @app_commands.autocomplete(extension=unloaded_autocomplete)
    @respond()
    async def load_command(self, interaction: Interaction, extension: str) -> Result:
        return await service.load_extension(self.bot, extension.strip())

    @app_commands.command(name="unload", description="도메인을 언로드합니다")
    @app_commands.describe(extension="언로드할 확장 기능 이름 (예: domains.example)")
    @app_commands.autocomplete(extension=loaded_autocomplete)
    @respond()
    async def unload_command(self, interaction: Interaction, extension: str) -> Result:
        return await service.unload_extension(self.bot, extension.strip())

    @app_commands.command(name="sync", description="슬래시 명령어를 동기화합니다")
    @app_commands.describe(scope="동기화 범위 (현재 서버 / 글로벌)")
    @app_commands.choices(scope=[
        app_commands.Choice(name="현재 서버 (즉시 반영)", value="guild"),
        app_commands.Choice(name="글로벌", value="global"),
    ])
    @respond()
    async def sync_command(self, interaction: Interaction, scope: str = "guild") -> Result:
        # interaction.guild는 캐시에 없으면 None이라 글로벌 동기화로 바뀔 수 있으므로 guild_id 사용
        guild_id = interaction.guild_id if scope == "guild" else None
        return await service.sync_commands(self.bot, guild_id)

    @app_commands.command(name="extensions", description="현재 로드된 모든 확장 기능을 표시합니다")
    @respond(defer=False)
    async def list_extensions(self, interaction: Interaction) -> Result | discord.Embed:
        loaded = service.loaded_extensions(self.bot)
        if not loaded:
            return Result(False, "현재 로드된 확장 기능이 없습니다.")
        return discord.Embed(
            title="로드된 확장 기능 목록",
            description="\n".join(f"`{i}.` {ext}" for i, ext in enumerate(loaded, 1)),
            color=discord.Color.blurple(),
        )
