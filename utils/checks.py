import discord
from discord import app_commands, Interaction


def has_admin_role():
    """config.yml의 관리자 역할을 가진 사용자만 실행할 수 있도록 하는 체크"""
    async def predicate(interaction: Interaction) -> bool:
        # DM에서는 역할 정보가 없으므로 차단
        if not isinstance(interaction.user, discord.Member):
            return False
        admin_role_ids = set(interaction.client.config.get("administrator_role_ids", []))
        return any(role.id in admin_role_ids for role in interaction.user.roles)

    return app_commands.check(predicate)
