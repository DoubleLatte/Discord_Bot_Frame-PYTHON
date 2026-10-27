import logging

import discord
from discord import app_commands, Interaction
from discord.ext import commands

from utils.checks import has_admin_role

log = logging.getLogger(__name__)


@app_commands.guild_only()
@has_admin_role()
class DevCommands(commands.GroupCog, group_name="dev", group_description="개발자용 명령어"):
    """개발자를 위한 명령어 관리 Cog (/dev reload, /dev load ...)"""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        super().__init__()

    @staticmethod
    async def send_response(interaction: Interaction, message: str, success: bool) -> None:
        """공통 응답 메시지를 전송하는 유틸리티 함수"""
        emoji = "✅" if success else "❌"
        await interaction.response.send_message(f"{emoji} {message}", ephemeral=True)

    async def extension_autocomplete(self, interaction: Interaction, current: str) -> list[app_commands.Choice[str]]:
        return [
            app_commands.Choice(name=ext, value=ext)
            for ext in self.bot.extensions
            if current.lower() in ext.lower()
        ][:25]

    @app_commands.command(name="reload", description="지정한 Cog를 다시 로드합니다")
    @app_commands.describe(extension="다시 로드할 확장 기능 이름 (예: command.example)")
    @app_commands.autocomplete(extension=extension_autocomplete)
    async def reload_command(self, interaction: Interaction, extension: str) -> None:
        try:
            await self.bot.reload_extension(extension)
            await self.send_response(interaction, f"`{extension}` 다시 로드 완료. 명령어 구조가 바뀌었다면 `/dev sync`를 실행하세요.", True)
        except commands.ExtensionError as e:
            await self.send_response(interaction, f"`{extension}` 다시 로드 중 오류: {e}", False)

    @app_commands.command(name="load", description="새 Cog를 로드합니다")
    @app_commands.describe(extension="로드할 확장 기능 이름 (예: command.example)")
    async def load_command(self, interaction: Interaction, extension: str) -> None:
        try:
            await self.bot.load_extension(extension)
            await self.send_response(interaction, f"`{extension}` 로드 완료. 반영하려면 `/dev sync`를 실행하세요.", True)
        except commands.ExtensionError as e:
            await self.send_response(interaction, f"`{extension}` 로드 중 오류: {e}", False)

    @app_commands.command(name="unload", description="Cog를 언로드합니다")
    @app_commands.describe(extension="언로드할 확장 기능 이름 (예: command.example)")
    @app_commands.autocomplete(extension=extension_autocomplete)
    async def unload_command(self, interaction: Interaction, extension: str) -> None:
        if extension == __name__:
            await self.send_response(interaction, "개발 명령어 자체는 언로드할 수 없습니다.", False)
            return
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
        try:
            if scope == "guild":
                self.bot.tree.copy_global_to(guild=interaction.guild)
                synced = await self.bot.tree.sync(guild=interaction.guild)
            else:
                synced = await self.bot.tree.sync()
            await interaction.followup.send(f"✅ {len(synced)}개의 명령어 동기화 완료 ({scope})", ephemeral=True)
        except discord.HTTPException as e:
            await interaction.followup.send(f"❌ 명령어 동기화 중 오류: {e}", ephemeral=True)

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


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(DevCommands(bot))
    log.info("DevCommands cog 로드 완료")
