import asyncio
import logging
import sys
from pathlib import Path

import discord

from core.bot import MyBot
from core.config import Config, ConfigError

try:
    import uvloop  # Windows 외 환경에서 설치돼 있으면 더 빠른 이벤트 루프 사용
    run = uvloop.run
except ImportError:
    run = asyncio.run

# PyInstaller로 빌드한 경우: 코드(command/)는 번들 내부, config.yml은 실행 파일 옆에서 읽음
if getattr(sys, "frozen", False):
    APP_DIR = Path(sys.executable).resolve().parent
else:
    APP_DIR = Path(__file__).resolve().parent
BUNDLE_DIR = Path(getattr(sys, "_MEIPASS", APP_DIR))


async def main() -> None:
    config = Config.load(APP_DIR / "config.yml")

    async with MyBot(config, extension_dir=BUNDLE_DIR / "command") as bot:
        await bot.start(config.token)


if __name__ == "__main__":
    discord.utils.setup_logging(level=logging.INFO)
    # 오류는 async with가 봇 연결을 정리한 뒤 여기로 전달됨
    try:
        run(main())
    except ConfigError as e:
        sys.exit(f"설정 오류: {e}")
    except discord.LoginFailure:
        sys.exit("오류: 로그인 실패. 토큰이 올바른지 확인하세요.")
    except discord.PrivilegedIntentsRequired:
        sys.exit("오류: 개발자 포털에서 Server Members Intent를 켜거나 config.yml의 members_intent를 false로 하세요.")
    except KeyboardInterrupt:
        pass
