import logging

import discord
from discord import app_commands, Interaction

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


async def on_app_command_error(interaction: Interaction, error: app_commands.AppCommandError) -> None:
    """모든 슬래시 명령어의 공통 오류 처리 (CommandTree.on_error로 등록)"""
    message = error_message_for(error)

    if message == DEFAULT_ERROR_MESSAGE:
        command_name = interaction.command.qualified_name if interaction.command else "알 수 없음"
        log.error("명령어 오류: %s", command_name, exc_info=error)
    elif isinstance(error, (app_commands.CommandNotFound, app_commands.CommandSignatureMismatch)):
        log.warning("등록된 명령어와 코드가 다릅니다. 동기화가 필요합니다: %s", error)

    # 자동완성 요청에는 메시지로 응답할 수 없음
    if interaction.type is not discord.InteractionType.autocomplete:
        await reply_error(interaction, message)


def error_message_for(error: Exception) -> str:
    for error_type, message in ERROR_MESSAGES:
        if isinstance(error, error_type):
            return message.format(e=error)
    return DEFAULT_ERROR_MESSAGE


async def reply_error(interaction: Interaction, message: str) -> None:
    """응답 여부에 맞춰 오류 메시지 전송 (interaction 만료 시 무시)"""
    content = f"❌ {message}"
    try:
        if interaction.response.is_done():
            await interaction.followup.send(content, ephemeral=True)
        else:
            await interaction.response.send_message(content, ephemeral=True)
    except (discord.HTTPException, discord.InteractionResponded) as e:
        log.warning("오류 메시지 전송 실패 (interaction 만료 등): %s", e)
