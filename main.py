import asyncio
import logging
import sys
from pathlib import Path

import discord

from core.bot import MyBot
from core.config import Config, ConfigError

BASE_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))


async def main() -> None:
    discord.utils.setup_logging(level=logging.INFO)
    try:
        config = Config.load(BASE_DIR / "config.yml")
    except ConfigError as e:
        sys.exit(f"설정 오류: {e}")

    async with MyBot(config, extension_dir=BASE_DIR / "command") as bot:
        try:
            await bot.start(config.token)
        except discord.LoginFailure:
            sys.exit("오류: 로그인 실패. 토큰이 올바른지 확인하세요.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
