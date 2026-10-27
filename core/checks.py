from discord import app_commands, Interaction

from core.bot import MyBot


def has_admin_role():
    """관리자 역할을 가진 사용자만 실행할 수 있도록 하는 체크"""
    async def predicate(interaction: Interaction) -> bool:
        client = interaction.client
        return isinstance(client, MyBot) and client.is_admin(interaction.user)

    return app_commands.check(predicate)
