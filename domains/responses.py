import functools
from collections.abc import Awaitable, Callable
from typing import Any

import discord
from discord import Interaction

MAX_MESSAGE_LENGTH = 2000  # Discord 메시지 최대 길이

# @respond를 붙인 명령어가 return할 수 있는 값
Response = tuple[bool, str] | discord.Embed


async def _send(interaction: Interaction, **kwargs: Any) -> None:
    """defer 여부에 맞춰 본인에게만 보이는 메시지로 응답"""
    if interaction.response.is_done():
        await interaction.followup.send(ephemeral=True, **kwargs)
    else:
        await interaction.response.send_message(ephemeral=True, **kwargs)


async def send_response(interaction: Interaction, success: bool, message: str) -> None:
    """✅/❌ 결과 메시지 전송 (길이 제한 처리)"""
    content = f"{'✅' if success else '❌'} {message}"
    if len(content) > MAX_MESSAGE_LENGTH:
        content = content[:MAX_MESSAGE_LENGTH - 1] + "…"
    await _send(interaction, content=content)


async def send_embed(interaction: Interaction, embed: discord.Embed) -> None:
    await _send(interaction, embed=embed)


def respond(*, defer: bool = True):
    """명령어가 return한 값을 응답으로 전송하는 데코레이터 (@app_commands.command 바로 아래에 붙임)

    - (성공 여부, 메시지) → ✅/❌ 메시지
    - discord.Embed      → embed
    defer=True면 실행 전에 먼저 defer (오래 걸리는 작업의 3초 응답 제한 대비)
    """
    def decorator(func: Callable[..., Awaitable[Response]]):
        @functools.wraps(func)  # app_commands가 원래 함수의 인자로 명령어 옵션을 만들도록 시그니처 보존
        async def wrapper(*args: Any, **kwargs: Any) -> None:
            # discord.py는 (cog, interaction) 또는 (interaction)을 위치 인자로, 옵션은 키워드로 전달
            interaction: Interaction = args[-1]
            if defer:
                await interaction.response.defer(ephemeral=True)

            result = await func(*args, **kwargs)
            if isinstance(result, discord.Embed):
                await send_embed(interaction, result)
            elif isinstance(result, tuple):
                await send_response(interaction, *result)
            else:
                raise TypeError(f"@respond 명령어는 (성공 여부, 메시지) 또는 Embed를 return해야 합니다: {result!r}")

        return wrapper

    return decorator
