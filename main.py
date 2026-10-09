import argparse
import discord
import bot


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description="run zomboid discord bot")
    cli.add_argument("token", help="discord token")
    cli.add_argument("rcon_port", help="zomboid server RCON port", type=int)
    cli.add_argument("rcon_password", help="zomboid server RCON password")
    cli.add_argument("running_server_name", help="running server name to interact with (ex: server-sophie-1-12-1)")
    cli.add_argument("-p", "--server_path", help="zomboid server install folder (full path)", default="/opt/pzserver/")
    cli.add_argument("-r", "--allowed_roles", help="comma-separated names or IDs of the discord roles allowed to call commands (ex: \"Admin,Moderator\", default: everyone, also when empty)", default="")
    cli = cli.parse_args()

    allowed_roles = [role.strip() for role in cli.allowed_roles.split(",") if role.strip()]

    discord.utils.setup_logging()
    bot.Bot(cli.rcon_port, cli.rcon_password, cli.server_path, cli.running_server_name, allowed_roles).run(cli.token)
