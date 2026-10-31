import logging
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

from core import errors
from core.config import Config

log = logging.getLogger(__name__)


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
        self.tree.on_error = errors.on_app_command_error

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

    def available_extensions(self) -> list[str]:
        """확장 기능 폴더의 도메인 목록 (__init__.py가 있는 폴더, _로 시작하는 이름 제외)
        폴더 바로 아래의 .py 파일은 도메인 공용 모듈이므로 로드하지 않음"""
        package = self._extension_dir.name
        return [
            f"{package}.{path.name}"
            for path in sorted(self._extension_dir.iterdir())
            if not path.name.startswith("_") and (path / "__init__.py").is_file()
        ]

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
        for extension in self.available_extensions():
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
