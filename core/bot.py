import logging
from pathlib import Path

import discord
from discord import app_commands, Interaction
from discord.ext import commands

from core.config import Config

log = logging.getLogger(__name__)


class MyBot(commands.Bot):
    def __init__(self, config: Config, extension_dir: Path) -> None:
        intents = discord.Intents.default()
        intents.members = True  # 필요 없으면 끄세요 (개발자 포털에서도 활성화 필요)
        super().__init__(
            command_prefix=commands.when_mentioned,
            intents=intents,
            application_id=config.application_id,
            activity=discord.Game(config.activity),
            status=discord.Status.online,
        )
        self._config = config
        self._extension_dir = extension_dir
        self.tree.on_error = self._on_app_command_error

    @property
    def config(self) -> Config:
        """읽기 전용 설정"""
        return self._config

    def is_admin(self, user: discord.abc.User) -> bool:
        """관리자 역할을 가진 서버 멤버인지 확인 (DM 사용자는 항상 False)"""
        if not isinstance(user, discord.Member):
            return False
        return any(role.id in self._config.admin_role_ids for role in user.roles)

    async def sync_commands(self, guild: discord.abc.Snowflake | None = None) -> list[app_commands.AppCommand]:
        """슬래시 명령어 동기화. guild를 주면 해당 서버에만 즉시 반영"""
        if guild is None:
            return await self.tree.sync()
        self.tree.copy_global_to(guild=guild)
        return await self.tree.sync(guild=guild)

    async def setup_hook(self) -> None:
        """확장 기능 폴더의 모든 Cog 자동 로드 후 명령어 동기화"""
        package = self._extension_dir.name
        for file in sorted(self._extension_dir.glob("*.py")):
            if file.stem.startswith("_"):
                continue
            ext = f"{package}.{file.stem}"
            try:
                await self.load_extension(ext)
                log.info("확장 기능 로드 성공: %s", ext)
            except commands.ExtensionError:
                log.exception("확장 기능 %s 로드 실패", ext)

        guild_id = self._config.dev_guild_id
        try:
            synced = await self.sync_commands(discord.Object(id=guild_id) if guild_id else None)
            log.info("%d개 명령어 동기화 완료", len(synced))
        except discord.HTTPException:
            log.exception("명령어 트리 동기화 오류")

    async def on_ready(self) -> None:
        log.info("봇 온라인: %s (ID: %s)", self.user, self.user.id)

    async def _on_app_command_error(self, interaction: Interaction, error: app_commands.AppCommandError) -> None:
        """모든 슬래시 명령어의 공통 오류 처리"""
        if isinstance(error, app_commands.NoPrivateMessage):
            message = "이 명령어는 서버에서만 사용할 수 있습니다."
        elif isinstance(error, app_commands.CommandOnCooldown):
            message = f"쿨다운 중입니다. {error.retry_after:.1f}초 후 다시 시도하세요."
        elif isinstance(error, app_commands.CheckFailure):
            message = "이 명령어를 사용할 권한이 없습니다."
        else:
            name = interaction.command.qualified_name if interaction.command else "알 수 없음"
            log.error("명령어 오류: %s", name, exc_info=error)
            message = "명령어 실행 중 오류가 발생했습니다."

        try:
            if interaction.response.is_done():
                await interaction.followup.send(f"❌ {message}", ephemeral=True)
            else:
                await interaction.response.send_message(f"❌ {message}", ephemeral=True)
        except discord.HTTPException:
            log.warning("오류 메시지 전송 실패 (interaction 만료 등)")
