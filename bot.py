import logging
from typing import TYPE_CHECKING
import discord
from discord import app_commands, Interaction
from discord.ext import commands
import rcon_handler


if TYPE_CHECKING:
    from bot import Bot


class Commands(commands.Cog):

    def __init__(self, bot: "Bot", rcon: rcon_handler.RCON):
        super().__init__()
        self.bot = bot
        self.rcon = rcon

    @app_commands.command(name="players")
    async def players(self, interaction: Interaction):
        """
        Checks for online players
        """
        self.log_command_call(interaction, "players")

        players = await self.rcon.online_players()

        if len(players) == 0:
            await interaction.response.send_message(
                "🤷 no players online", ephemeral=True
            )
            return

        formatted_players = ""
        for player in players:
            formatted_players += f"\n  🧟 {player}"

        await interaction.response.send_message(f"online players:{formatted_players}")

    @app_commands.command(name="restart_server")
    async def restart_server(self, interaction: Interaction):
        """
        Restarts server
        """
        self.log_command_call(interaction, "restart_server")

        if len(await self.rcon.online_players()) != 0:
            await interaction.response.send_message(
                "❌ can't restart server because there are players online"
            )
            return

        await interaction.response.send_message(
            "🔧 server is being restarted and mods updated"
        )
        await self.rcon.restart_server()

    def log_command_call(self, interaction: "Interaction", command_name: str):
        logger = logging.getLogger(f"bot.commands.{command_name}")

        guild = interaction.guild
        channel = interaction.channel
        channel = (
            f"{guild.name}.{channel.name} ({str(channel.type)})"
            if guild
            else "Private Message"
        )
        user = f"{interaction.user.name}#{interaction.user.discriminator}"
        logger.info(f"channel: {channel}: user: {user}")


class Bot(commands.Bot):

    def __init__(self, rcon_port: int, rcon_password: str, server_path: str, running_server_name: str):
        self.logger = logging.getLogger("bot")
        self.logger.info("starting bot...")

        intents = discord.Intents.default()
        intents.message_content = True

        self.rcon = rcon_handler.RCON(rcon_port, rcon_password, server_path, running_server_name)

        super().__init__(command_prefix=commands.when_mentioned, intents=intents)

    async def setup_hook(self) -> None:
        self.logger.info("setting up commands...")
        cog = Commands(self, self.rcon)
        await self.add_cog(cog)

        self.logger.info("syncing commands...")
        await self.tree.sync()

        self.logger.info("finished setting up bot...")
