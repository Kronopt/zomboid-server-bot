import logging
from typing import TYPE_CHECKING, List, Optional
import discord
from discord import app_commands, Interaction
from discord.ext import commands
import rcon_handler


if TYPE_CHECKING:
    from bot import Bot


class Commands(commands.Cog):

    def __init__(self, bot: "Bot", rcon: rcon_handler.RCON, allowed_roles: List[str]):
        super().__init__()
        self.bot = bot
        self.rcon = rcon
        self.allowed_roles = allowed_roles

    async def interaction_check(self, interaction: Interaction) -> bool:
        """
        Only lets users with one of the allowed roles (matched by name or ID) call commands, if any are configured
        """
        if not self.allowed_roles:
            return True

        # users in private messages have no roles
        roles = getattr(interaction.user, "roles", [])
        return any(
            role.name in self.allowed_roles or str(role.id) in self.allowed_roles
            for role in roles
        )

    async def cog_app_command_error(self, interaction: Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CheckFailure):
            self.log_command_call(interaction, interaction.command.name, "denied, missing an allowed role")
            await interaction.response.send_message(
                "🚫 you don't have permission to use this command", ephemeral=True
            )
            return

        # discord.py stops logging command errors once a cog error handler exists
        logging.getLogger("bot.commands").error(
            "error in command %r", interaction.command.name, exc_info=error
        )

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

    def log_command_call(self, interaction: "Interaction", command_name: str, note: str = ""):
        logger = logging.getLogger(f"bot.commands.{command_name}")

        guild = interaction.guild
        channel = interaction.channel
        channel = (
            f"{guild.name}.{channel.name} ({str(channel.type)})"
            if guild
            else "Private Message"
        )
        user = f"{interaction.user.name}#{interaction.user.discriminator}"
        logger.info(f"channel: {channel}: user: {user}{f': {note}' if note else ''}")


class Bot(commands.Bot):

    def __init__(self, rcon_port: int, rcon_password: str, server_path: str, running_server_name: str, allowed_roles: Optional[List[str]] = None):
        self.logger = logging.getLogger("bot")
        self.logger.info("starting bot...")

        intents = discord.Intents.default()
        intents.message_content = True

        self.rcon = rcon_handler.RCON(rcon_port, rcon_password, server_path, running_server_name)
        self.allowed_roles = allowed_roles or []

        super().__init__(command_prefix=commands.when_mentioned, intents=intents)

    async def setup_hook(self) -> None:
        self.logger.info("setting up commands...")
        if not self.allowed_roles:
            self.logger.info("no allowed roles set, everyone can call commands")
        else:
            self.logger.info(f"only users with one of the roles {self.allowed_roles} can call commands")

        cog = Commands(self, self.rcon, self.allowed_roles)
        await self.add_cog(cog)

        self.logger.info("syncing commands...")
        await self.tree.sync()

        self.logger.info("finished setting up bot...")
