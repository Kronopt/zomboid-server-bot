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
        self.logger = logging.getLogger("bot.commands")

    @app_commands.command(name="players")
    async def command_players(self, interaction: Interaction):
        """
        Checks online players
        """
        self.log_command_call(interaction, "players")

        players = await self.rcon.online_players()

        if len(players) == 0:
            await interaction.response.send_message("no players online")
            return

        await interaction.response.send_message(f"online players: {players}")

    @app_commands.command(name="update_mods")
    async def command_update_mods(self, interaction: Interaction):
        """
        Updates mods on server
        """
        self.log_command_call(interaction, "update_mods")

        await self.rcon.update_mods()
        await interaction.response.send_message("mods are being updated")

    @app_commands.command(name="restart_server")
    async def command_restart_server(self, interaction: Interaction):
        """
        Restarts server
        """
        self.log_command_call(interaction, "restart_server")

        if len(await self.rcon.online_players()) != 0:
            await interaction.response.send_message(
                "can't restart server because there are players online"
            )
            return

        await self.rcon.restart_server()
        await interaction.response.send_message("mods are being updated")

    def log_command_call(self, interaction: "Interaction", command_name: str):
        guild = interaction.guild
        channel = interaction.channel
        channel = (
            f"{guild.name}.{channel.name} ({str(channel.type)})"
            if guild
            else "Private Message"
        )
        user = f"{interaction.user.name}#{interaction.user.discriminator}"
        self.logger.info(f"command: {command_name}; channel: {channel}; user: {user}")


class Bot(commands.Bot):

    def __init__(self, rcon_port: int, rcon_password: str):
        self.logger = logging.getLogger("bot")
        self.logger.info("starting bot...")

        intents = discord.Intents.default()
        intents.message_content = True

        self.rcon = rcon_handler.RCON(rcon_port, rcon_password)

        super().__init__(command_prefix=commands.when_mentioned, intents=intents)

    async def setup_hook(self) -> None:
        self.logger.info("setting up commands...")
        await self.add_cog(Commands(self, self.rcon))

        self.logger.info("syncing commands...")
        await self.tree.sync()
