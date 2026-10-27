import asyncio
import logging
import os
import sys
from pathlib import Path

import discord
import yaml
from discord import app_commands, Interaction
from discord.ext import commands

BASE_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
CONFIG_PATH = BASE_DIR / "config.yml"
COMMAND_DIR = BASE_DIR / "command"

log = logging.getLogger("bot")


def load_config() -> dict:
    """config.yml 파일에서 설정 불러오기 (환경변수 DISCORD_TOKEN 우선)"""
    try:
        config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}
    except FileNotFoundError:
        sys.exit(f"오류: {CONFIG_PATH} 파일을 찾을 수 없습니다.")
    except yaml.YAMLError as e:
        sys.exit(f"오류: {CONFIG_PATH} 파일 읽기 실패 - {e}")

    config["token"] = os.getenv("DISCORD_TOKEN") or config.get("token")
    if not config["token"]:
        sys.exit("오류: 토큰이 없습니다. DISCORD_TOKEN 환경변수나 config.yml의 token을 설정하세요.")
    return config


class MyBot(commands.Bot):
    def __init__(self, config: dict) -> None:
        intents = discord.Intents.default()
        intents.members = True  # 필요 없으면 끄세요 (개발자 포털에서도 활성화 필요)
        super().__init__(
            command_prefix=commands.when_mentioned,
            intents=intents,
            application_id=config.get("application_id"),
            activity=discord.Game(config.get("activity", "~~~ 하는중")),
            status=discord.Status.online,
        )
        self.config = config
        self.tree.on_error = self.on_app_command_error

    async def setup_hook(self) -> None:
        """command 폴더의 모든 Cog 자동 로드 후 명령어 동기화"""
        for file in sorted(COMMAND_DIR.glob("*.py")):
            if file.stem.startswith("_"):
                continue
            ext = f"command.{file.stem}"
            try:
                await self.load_extension(ext)
                log.info("확장 기능 로드 성공: %s", ext)
            except commands.ExtensionError:
                log.exception("확장 기능 %s 로드 실패", ext)

        try:
            guild_id = self.config.get("dev_guild_id")
            if guild_id:
                # 개발 서버에만 즉시 동기화 (글로벌 동기화는 반영이 느림)
                guild = discord.Object(id=guild_id)
                self.tree.copy_global_to(guild=guild)
                synced = await self.tree.sync(guild=guild)
            else:
                synced = await self.tree.sync()
            log.info("%d개 명령어 동기화 완료", len(synced))
        except discord.HTTPException:
            log.exception("명령어 트리 동기화 오류")

    async def on_ready(self) -> None:
        log.info("봇 온라인: %s (ID: %s)", self.user, self.user.id)

    async def on_app_command_error(self, interaction: Interaction, error: app_commands.AppCommandError) -> None:
        """모든 슬래시 명령어의 공통 오류 처리"""
        if isinstance(error, app_commands.CheckFailure):
            message = "이 명령어를 사용할 권한이 없습니다."
        elif isinstance(error, app_commands.CommandOnCooldown):
            message = f"쿨다운 중입니다. {error.retry_after:.1f}초 후 다시 시도하세요."
        else:
            log.exception("명령어 오류: %s", interaction.command, exc_info=error)
            message = "명령어 실행 중 오류가 발생했습니다."

        if interaction.response.is_done():
            await interaction.followup.send(f"❌ {message}", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ {message}", ephemeral=True)


async def main() -> None:
    discord.utils.setup_logging(level=logging.INFO)
    config = load_config()
    async with MyBot(config) as bot:
        try:
            await bot.start(config["token"])
        except discord.LoginFailure:
            sys.exit("오류: 로그인 실패. 토큰이 올바른지 확인하세요.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
