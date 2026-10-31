"""확장 기능 관리 로직. Discord 응답 방식과 분리해 결과(Result)만 돌려줌"""
from typing import NamedTuple

import discord
from discord.ext import commands

from core.bot import MyBot

SELF_EXTENSION = __package__  # 이 도메인 자신 (언로드 금지)


class Result(NamedTuple):
    success: bool
    message: str


def loaded_extensions(bot: MyBot) -> list[str]:
    return list(bot.extensions)


def unloaded_extensions(bot: MyBot) -> list[str]:
    return [ext for ext in bot.available_extensions() if ext not in bot.extensions]


async def reload_extension(bot: MyBot, name: str) -> Result:
    try:
        await bot.reload_extension(name)
    except commands.ExtensionError as e:
        return Result(False, f"`{name}` 다시 로드 중 오류: {e}")
    return Result(True, f"`{name}` 다시 로드 완료. 명령어 구조가 바뀌었다면 `/dev sync`를 실행하세요.")


async def load_extension(bot: MyBot, name: str) -> Result:
    try:
        await bot.load_extension(name)
    except (commands.ExtensionError, ImportError) as e:  # 상위 패키지가 없으면 ModuleNotFoundError
        return Result(False, f"`{name}` 로드 중 오류: {e}")
    return Result(True, f"`{name}` 로드 완료. 반영하려면 `/dev sync`를 실행하세요.")


async def unload_extension(bot: MyBot, name: str) -> Result:
    if name == SELF_EXTENSION:
        return Result(False, "개발 명령어 자체는 언로드할 수 없습니다.")
    try:
        await bot.unload_extension(name)
    except commands.ExtensionError as e:
        return Result(False, f"`{name}` 언로드 중 오류: {e}")
    return Result(True, f"`{name}` 언로드 완료. 반영하려면 `/dev sync`를 실행하세요.")


async def sync_commands(bot: MyBot, guild_id: int | None) -> Result:
    """guild_id가 있으면 해당 서버에만, 없으면 글로벌로 동기화"""
    scope = "현재 서버" if guild_id else "글로벌"
    try:
        synced = await bot.sync_commands(discord.Object(id=guild_id) if guild_id else None)
    except discord.HTTPException as e:
        return Result(False, f"명령어 동기화 중 오류: {e}")
    return Result(True, f"{len(synced)}개의 명령어 동기화 완료 ({scope})")
