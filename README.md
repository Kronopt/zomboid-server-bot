# zomboid-server-bot

A small Discord bot for managing a [Project Zomboid](https://projectzomboid.com/) dedicated server from Discord. Players can see who is online and restart the server without needing shell access to the host. A restart also picks up updated Workshop mods.

## What it does

The bot registers two slash commands:

| Command           | What it does |
|-------------------|--------------|
| `/players`        | Lists the players currently connected. If nobody is online it replies with a message only the caller can see. |
| `/restart_server` | Restarts the server, but only when nobody is online. It sends `quit` over RCON, waits 30 seconds, then starts the server again inside a tmux session. Mods are updated when the server starts. |

### How it works

```
Discord ──slash command──▶ bot.py (discord.py)
                              │
                              ▼
                       rcon_handler.py
                         │          │
          RCON (127.0.0.1)          tmux send-keys -t zomboid-server
                         ▼          ▼
                Project Zomboid dedicated server
```

- [main.py](main.py) parses the command-line arguments, sets up logging and starts the bot.
- [bot.py](bot.py) defines the `Bot` client and a `Commands` cog that holds the slash commands. The commands are synced to Discord when the bot starts (`setup_hook`). Every command call is logged with the channel and the user who ran it.
- [rcon_handler.py](rcon_handler.py) talks to the game server:
  - `online_players()` sends the RCON `players` command and parses the reply.
  - `restart_server()` sends the RCON `quit` command, waits 30 seconds, and then sends `cd <server_path> && bash start-server.sh -servername <running_server_name>` to the `zomboid-server` tmux session.

RCON always connects to `127.0.0.1`. RCON sends the password in plain text, so the bot has to run on the same machine as the game server, and the RCON port should not be exposed to the internet.

## Requirements

- Python 3.10 or newer
- A Project Zomboid dedicated server on the same host, with RCON turned on
- `tmux`, with a session named **`zomboid-server`** that the server runs in. The bot types the start command into this session when it restarts the server.
- A Discord application with a bot user (see below)

### Setting up the Discord bot

1. Create an application at the [Discord Developer Portal](https://discord.com/developers/applications) and add a **Bot** to it.
2. Under **Bot → Privileged Gateway Intents**, turn on **Message Content Intent**. The bot asks for this intent and will not start without it.
3. Copy the bot **token**.
4. Invite the bot to your server. Use an OAuth2 URL with the `bot` and `applications.commands` scopes.

### Turning on RCON in Project Zomboid

In the server config file, usually `~/Zomboid/Server/<servername>.ini` for the user that runs the server, set:

```ini
RCONPort=27015
RCONPassword=choose-a-strong-password
```

Restart the server after you change these settings. `<servername>` is the value you pass to `start-server.sh -servername`, and it is also what the bot expects as `running_server_name`.

## Usage

```
python main.py <token> <rcon_port> <rcon_password> <running_server_name> [-p SERVER_PATH]
```

| Argument              | Description |
|-----------------------|-------------|
| `token`               | Discord bot token |
| `rcon_port`           | The server's RCON port (`RCONPort` in the server `.ini`) |
| `rcon_password`       | The server's RCON password (`RCONPassword` in the server `.ini`) |
| `running_server_name` | Server name used with `-servername` (for example `server-sophie-1-12-1`) |
| `-p`, `--server_path` | Full path to the dedicated server install folder, which contains `start-server.sh`. Default: `/opt/pzserver/` |

Example:

```bash
python main.py "$DISCORD_TOKEN" 27015 "$RCON_PASSWORD" server-sophie-1-12-1 -p /opt/pzserver/
```

Slash commands can take a few minutes to show up in Discord the first time the bot syncs them.

## Development

### Setup

```bash
git clone <this repo>
cd zomboid-server-bot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Dependencies (pinned in [requirements.txt](requirements.txt)):

- [discord.py](https://github.com/Rapptz/discord.py) for the Discord client and slash commands
- [rcon](https://github.com/conqp/rcon) for the Source RCON client used to talk to the game server

### Adding a command

Add a method to the `Commands` cog in [bot.py](bot.py) and decorate it with `@app_commands.command(name="...")`. The method's docstring is used as the command description in Discord. Call `self.log_command_call(...)` at the start of the method so the call is logged like the other commands. If the command needs to talk to the game server, add the logic to the `RCON` class in [rcon_handler.py](rcon_handler.py). The new command is synced to Discord the next time the bot starts.

### Testing

The project has no automated tests yet. To test a change by hand:

1. Use a separate Discord bot and a private Discord server for testing, so you don't touch the real one.
2. Run a local Project Zomboid dedicated server with RCON turned on, started inside a tmux session named `zomboid-server`:
   ```bash
   tmux new -s zomboid-server
   cd /opt/pzserver && bash start-server.sh -servername <name>
   # detach with Ctrl+b, then d
   ```
3. Start the bot with your test token and RCON settings, then run the commands from Discord:
   - `/players` with nobody connected should reply "no players online".
   - `/players` with a client connected should list that player.
   - `/restart_server` with a player online should refuse to restart.
   - `/restart_server` with nobody online should stop the server and, after about 30 seconds, start it again in the tmux session (check with `tmux attach -t zomboid-server`).
4. Check the bot's log output. Each command call is logged with the channel and the user.

To check RCON without Discord, you can use the `rconclt` CLI that comes with the `rcon` package. Set up a `~/.rcon.conf` or pass the host, port and password; see the package's documentation for the exact syntax.

## Deployment

The bot has to run **on the same host as the game server**, as the **same user that owns the `zomboid-server` tmux session**. Otherwise it can't reach RCON on localhost or send keys to that session. Both the game server and the bot run in their own tmux sessions, `zomboid-server` and `zomboid-bot`.

### 1. Install

```bash
sudo -u pzuser -i
git clone <this repo> ~/zomboid-server-bot
cd ~/zomboid-server-bot
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Replace `pzuser` with the user that runs your Project Zomboid server.

### 2. Run the game server in tmux

The bot expects the server to be running in a tmux session called `zomboid-server`:

```bash
tmux new -d -s zomboid-server
tmux send-keys -t zomboid-server 'cd /opt/pzserver && bash start-server.sh -servername <name>' C-m
```

### 3. Run the bot in tmux

Put the secrets in `~/zomboid-server-bot/.env` and make the file readable only by you (`chmod 600 .env`):

```bash
DISCORD_TOKEN=...
RCON_PORT=27015
RCON_PASSWORD=...
SERVER_NAME=server-sophie-1-12-1
SERVER_PATH=/opt/pzserver/
```

Start the bot in its own tmux session, `zomboid-bot`:

```bash
tmux new -d -s zomboid-bot
tmux send-keys -t zomboid-bot 'cd ~/zomboid-server-bot && set -a && source .env && set +a && .venv/bin/python main.py "$DISCORD_TOKEN" "$RCON_PORT" "$RCON_PASSWORD" "$SERVER_NAME" -p "$SERVER_PATH"' C-m
```

To see the bot's logs, run `tmux attach -t zomboid-bot`, then detach with `Ctrl+b`, `d`. The command runs inside a shell, so if the bot crashes the session stays open and you can still read the error.

Nothing restarts the bot automatically if it crashes or the host reboots. Run step 3 again to bring it back.

### Updating

```bash
cd ~/zomboid-server-bot
git pull
.venv/bin/pip install -r requirements.txt
tmux send-keys -t zomboid-bot C-c        # stop the bot
tmux send-keys -t zomboid-bot 'cd ~/zomboid-server-bot && set -a && source .env && set +a && .venv/bin/python main.py "$DISCORD_TOKEN" "$RCON_PORT" "$RCON_PASSWORD" "$SERVER_NAME" -p "$SERVER_PATH"' C-m
```

## Security notes

- Secrets are passed as command-line arguments, so other users on the host can see them in `ps`. Run the bot on a host you control, and keep the `.env` file `chmod 600`.
- Never expose the RCON port publicly. The bot only needs it on `127.0.0.1`.
- Anyone who can see the slash commands in your Discord server can use `/restart_server`. It refuses to restart while players are online, but you can restrict who can use it under **Server Settings → Integrations → \<your bot\>** in Discord.

## Known limitations

- The tmux session name `zomboid-server` is hard-coded in [rcon_handler.py](rcon_handler.py).
- The restart waits a fixed 30 seconds for the server to shut down before it starts it again.
- When the bot parses player names, it removes every `-` character, so a name like `cool-guy` shows up as `coolguy`.

## License

[MIT](LICENSE)
