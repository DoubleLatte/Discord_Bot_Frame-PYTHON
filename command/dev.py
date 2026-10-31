import logging
from collections.abc import Iterable
from pathlib import Path

import discord
from discord import app_commands, Interaction
from discord.ext import commands

from core.bot import MyBot

log = logging.getLogger(__name__)

MAX_MESSAGE_LENGTH = 2000  # Discord 메시지 최대 길이
EXTENSION_DIR = Path(__file__).parent  # 이 파일이 있는 확장 기능 폴더


def available_extensions() -> list[str]:
    """확장 기능 폴더의 .py 파일 목록 (_로 시작하는 파일 제외)"""
    return [
        f"{__package__}.{file.stem}"
        for file in sorted(EXTENSION_DIR.glob("*.py"))
        if not file.stem.startswith("_")
    ]


# GroupCog 클래스에 붙인 app_commands.check는 하위 명령어에 적용되지 않으므로
# 권한 확인은 interaction_check에서 처리 (guild_only, default_permissions는 그룹에 적용됨)
# default_permissions: 서버 관리자 외에는 명령어 목록에서 숨김 (서버 설정 > 연동에서 역할별 허용 가능)
@app_commands.guild_only()
@app_commands.default_permissions(administrator=True)
class DevCommands(commands.GroupCog, group_name="dev", group_description="개발자용 명령어"):
    """개발자를 위한 명령어 관리 Cog (/dev reload, /dev load ...)"""

    def __init__(self, bot: MyBot) -> None:
        self.bot = bot
        super().__init__()

    async def interaction_check(self, interaction: Interaction) -> bool:
        """모든 /dev 하위 명령어에 적용되는 관리자 역할 체크 (실패 시 CheckFailure)"""
        return self.bot.is_admin(interaction.user)

    @staticmethod
    async def send_response(interaction: Interaction, message: str, success: bool) -> None:
        """공통 응답 메시지 전송 (defer 여부에 맞춰 응답, 길이 제한 처리)"""
        content = f"{'✅' if success else '❌'} {message}"
        if len(content) > MAX_MESSAGE_LENGTH:
            content = content[:MAX_MESSAGE_LENGTH - 1] + "…"

        if interaction.response.is_done():
            await interaction.followup.send(content, ephemeral=True)
        else:
            await interaction.response.send_message(content, ephemeral=True)

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
        return self._choices(interaction, current, self.bot.extensions)

    async def unloaded_autocomplete(self, interaction: Interaction, current: str) -> list[app_commands.Choice[str]]:
        loaded = self.bot.extensions
        return self._choices(interaction, current, [ext for ext in available_extensions() if ext not in loaded])

    # 확장 기능 (재)로드는 3초 응답 제한을 넘길 수 있으므로 먼저 defer
    @app_commands.command(name="reload", description="지정한 Cog를 다시 로드합니다")
    @app_commands.describe(extension="다시 로드할 확장 기능 이름 (예: command.example)")
    @app_commands.autocomplete(extension=loaded_autocomplete)
    async def reload_command(self, interaction: Interaction, extension: str) -> None:
        await interaction.response.defer(ephemeral=True)
        extension = extension.strip()
        try:
            await self.bot.reload_extension(extension)
            await self.send_response(interaction, f"`{extension}` 다시 로드 완료. 명령어 구조가 바뀌었다면 `/dev sync`를 실행하세요.", True)
        except commands.ExtensionError as e:
            await self.send_response(interaction, f"`{extension}` 다시 로드 중 오류: {e}", False)

    @app_commands.command(name="load", description="새 Cog를 로드합니다")
    @app_commands.describe(extension="로드할 확장 기능 이름 (예: command.example)")
    @app_commands.autocomplete(extension=unloaded_autocomplete)
    async def load_command(self, interaction: Interaction, extension: str) -> None:
        await interaction.response.defer(ephemeral=True)
        extension = extension.strip()
        try:
            await self.bot.load_extension(extension)
            await self.send_response(interaction, f"`{extension}` 로드 완료. 반영하려면 `/dev sync`를 실행하세요.", True)
        except (commands.ExtensionError, ImportError) as e:  # 상위 패키지가 없으면 ModuleNotFoundError
            await self.send_response(interaction, f"`{extension}` 로드 중 오류: {e}", False)

    @app_commands.command(name="unload", description="Cog를 언로드합니다")
    @app_commands.describe(extension="언로드할 확장 기능 이름 (예: command.example)")
    @app_commands.autocomplete(extension=loaded_autocomplete)
    async def unload_command(self, interaction: Interaction, extension: str) -> None:
        extension = extension.strip()
        if extension == __name__:
            await self.send_response(interaction, "개발 명령어 자체는 언로드할 수 없습니다.", False)
            return

        await interaction.response.defer(ephemeral=True)
        try:
            await self.bot.unload_extension(extension)
            await self.send_response(interaction, f"`{extension}` 언로드 완료. 반영하려면 `/dev sync`를 실행하세요.", True)
        except commands.ExtensionError as e:
            await self.send_response(interaction, f"`{extension}` 언로드 중 오류: {e}", False)

    @app_commands.command(name="sync", description="슬래시 명령어를 동기화합니다")
    @app_commands.describe(scope="동기화 범위 (현재 서버 / 글로벌)")
    @app_commands.choices(scope=[
        app_commands.Choice(name="현재 서버 (즉시 반영)", value="guild"),
        app_commands.Choice(name="글로벌", value="global"),
    ])
    async def sync_command(self, interaction: Interaction, scope: str = "guild") -> None:
        await interaction.response.defer(ephemeral=True)
        # interaction.guild는 캐시에 없으면 None이라 글로벌 동기화로 바뀔 수 있으므로 guild_id 사용
        guild = discord.Object(id=interaction.guild_id) if scope == "guild" else None
        try:
            synced = await self.bot.sync_commands(guild)
            await self.send_response(interaction, f"{len(synced)}개의 명령어 동기화 완료 ({scope})", True)
        except discord.HTTPException as e:
            await self.send_response(interaction, f"명령어 동기화 중 오류: {e}", False)

    @app_commands.command(name="extensions", description="현재 로드된 모든 확장 기능을 표시합니다")
    async def list_extensions(self, interaction: Interaction) -> None:
        loaded = list(self.bot.extensions)
        if not loaded:
            await self.send_response(interaction, "현재 로드된 확장 기능이 없습니다.", False)
            return
        embed = discord.Embed(
            title="로드된 확장 기능 목록",
            description="\n".join(f"`{i}.` {ext}" for i, ext in enumerate(loaded, 1)),
            color=discord.Color.blurple(),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: MyBot) -> None:
    await bot.add_cog(DevCommands(bot))
    log.info("DevCommands cog 로드 완료")
