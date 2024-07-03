import argparse
import discord
import bot


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description="run zomboid discord bot")
    cli.add_argument("token", help="discord token")
    cli.add_argument("rcon_port", help="zomboid server RCON port", type=int)
    cli.add_argument("rcon_password", help="zomboid server RCON password")
    cli = cli.parse_args()

    discord.utils.setup_logging()
    bot.Bot(cli.rcon_port, cli.rcon_password).run(cli.token)
