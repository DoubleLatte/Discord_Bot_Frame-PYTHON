import discord
from discord import app_commands, Interaction, Embed, ButtonStyle
from discord.ext import commands
from discord.ui import Button, View


def has_admin_role():
    async def predicate(interaction: Interaction) -> bool:
        # config에서 관리자 역할 ID 가져오기
        admin_role_ids = interaction.client.config.get('administrator_role_ids', [])
        return any(role.id in admin_role_ids for role in interaction.user.roles)
    
    return app_commands.check(predicate)


class Example(commands.Cog):

    
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.user_channel_count = {}
    
    @app_commands.command(
        name="예시 명령어", 
        description="명령어 설명"
    )
    @has_admin_role()
    async def example_command(self, interaction: Interaction) -> None:
        # 테스트 메시지 전송
        await interaction.response.send_message("테스트")
    
    @example_command.error
    async def example_command_error(self, interaction: Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CheckFailure):
            await interaction.response.send_message(
                "이 명령어를 사용할 권한이 없습니다.", 
                ephemeral=True
            )
        else:
            print(f"example 명령어에서 오류 발생: {error}")
            await interaction.response.send_message(
                "명령어 실행 중 오류가 발생했습니다.", 
                ephemeral=True
            )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Example(bot))
    print("EXAMPLE cog가 성공적으로 로드되었습니다")