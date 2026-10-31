import logging
from pathlib import Path

import discord
from discord import app_commands, Interaction
from discord.ext import commands

from core.config import Config

log = logging.getLogger(__name__)

# 오류 종류별 사용자 안내 메시지 (위에서부터 먼저 매칭, {e}는 오류 객체)
ERROR_MESSAGES: list[tuple[type[Exception], str]] = [
    (app_commands.NoPrivateMessage, "이 명령어는 서버에서만 사용할 수 있습니다."),
    (app_commands.CommandOnCooldown, "쿨다운 중입니다. {e.retry_after:.1f}초 후 다시 시도하세요."),
    (app_commands.BotMissingPermissions, "봇에게 이 명령어를 실행할 권한이 없습니다. 서버 관리자에게 문의하세요."),
    (app_commands.CheckFailure, "이 명령어를 사용할 권한이 없습니다."),
    (app_commands.TransformerError, "입력값이 올바르지 않습니다."),
    # 코드와 Discord에 등록된 명령어가 다를 때 (동기화 필요)
    (app_commands.CommandNotFound, "명령어 정보가 최신이 아닙니다. 잠시 후 다시 시도하세요."),
    (app_commands.CommandSignatureMismatch, "명령어 정보가 최신이 아닙니다. 잠시 후 다시 시도하세요."),
]
DEFAULT_ERROR_MESSAGE = "명령어 실행 중 오류가 발생했습니다."


def build_intents(members: bool) -> discord.Intents:
    intents = discord.Intents.default()
    intents.typing = False  # 슬래시 명령어 봇엔 불필요한 이벤트
    intents.members = members  # 켜려면 개발자 포털에서도 Server Members Intent 활성화 필요
    return intents


class MyBot(commands.Bot):

    def __init__(self, config: Config, extension_dir: Path) -> None:
        super().__init__(
            command_prefix=commands.when_mentioned,
            help_command=None,  # 접두사 명령어를 쓰지 않으므로 기본 help 제거
            intents=build_intents(config.members_intent),
            application_id=config.application_id,
            activity=discord.Game(config.activity) if config.activity else None,
            max_messages=None,  # 메시지 캐시 끔 (메모리 절약, on_message_edit 등이 필요하면 제거)
        )
        self._config = config
        self._extension_dir = extension_dir
        self.tree.on_error = self._on_app_command_error

    # ── 공개 API ─────────────────────────────────────────

    @property
    def config(self) -> Config:
        """읽기 전용 설정"""
        return self._config

    def is_admin(self, user: discord.abc.User) -> bool:
        """관리자 역할을 가진 서버 멤버인지 확인 (DM 사용자는 항상 False)"""
        if not isinstance(user, discord.Member):
            return False

        # user.roles는 서버 캐시에 있는 역할만 돌려주므로, interaction 데이터의 역할 ID 목록(_roles)을 직접 비교
        return not self._config.admin_role_ids.isdisjoint(user._roles)

    async def sync_commands(self, guild: discord.abc.Snowflake | None = None) -> list[app_commands.AppCommand]:
        """슬래시 명령어 동기화. guild를 주면 해당 서버에만 즉시 반영"""
        if guild is None:
            return await self.tree.sync()

        self.tree.copy_global_to(guild=guild)
        return await self.tree.sync(guild=guild)

    # ── 시작 과정 ────────────────────────────────────────

    async def setup_hook(self) -> None:
        # 로그인 직후 한 번만 실행 (on_ready는 재연결마다 다시 호출되므로 초기화는 여기서)
        await self._load_all_extensions()
        await self._initial_sync()

    async def on_ready(self) -> None:
        log.info("봇 온라인: %s (ID: %s)", self.user, self.user.id)

    async def _load_all_extensions(self) -> None:
        """확장 기능 폴더의 .py 파일을 모두 로드 (_로 시작하는 파일 제외)"""
        package = self._extension_dir.name

        for file in sorted(self._extension_dir.glob("*.py")):
            if file.stem.startswith("_"):
                continue

            extension = f"{package}.{file.stem}"
            try:
                await self.load_extension(extension)
                log.info("확장 기능 로드 성공: %s", extension)
            except commands.ExtensionError:
                log.exception("확장 기능 로드 실패: %s", extension)

    async def _initial_sync(self) -> None:
        """dev_guild_id가 있으면 해당 서버에, 없으면 글로벌로 동기화"""
        guild_id = self._config.dev_guild_id
        target = discord.Object(id=guild_id) if guild_id else None

        try:
            synced = await self.sync_commands(target)
            log.info("%d개 명령어 동기화 완료", len(synced))
        except discord.HTTPException:
            log.exception("명령어 동기화 실패")

    # ── 오류 처리 ────────────────────────────────────────

    async def _on_app_command_error(self, interaction: Interaction, error: app_commands.AppCommandError) -> None:
        """모든 슬래시 명령어의 공통 오류 처리"""
        message = self._error_message_for(error)

        if message == DEFAULT_ERROR_MESSAGE:
            command_name = interaction.command.qualified_name if interaction.command else "알 수 없음"
            log.error("명령어 오류: %s", command_name, exc_info=error)
        elif isinstance(error, (app_commands.CommandNotFound, app_commands.CommandSignatureMismatch)):
            log.warning("등록된 명령어와 코드가 다릅니다. 동기화가 필요합니다: %s", error)

        # 자동완성 요청에는 메시지로 응답할 수 없음
        if interaction.type is not discord.InteractionType.autocomplete:
            await self._reply_error(interaction, message)

    @staticmethod
    def _error_message_for(error: Exception) -> str:
        for error_type, message in ERROR_MESSAGES:
            if isinstance(error, error_type):
                return message.format(e=error)
        return DEFAULT_ERROR_MESSAGE

    @staticmethod
    async def _reply_error(interaction: Interaction, message: str) -> None:
        """응답 여부에 맞춰 오류 메시지 전송 (interaction 만료 시 무시)"""
        content = f"❌ {message}"
        try:
            if interaction.response.is_done():
                await interaction.followup.send(content, ephemeral=True)
            else:
                await interaction.response.send_message(content, ephemeral=True)
        except (discord.HTTPException, discord.InteractionResponded) as e:
            log.warning("오류 메시지 전송 실패 (interaction 만료 등): %s", e)
