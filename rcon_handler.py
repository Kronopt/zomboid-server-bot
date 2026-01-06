import asyncio
import os
from typing import List, Dict
from rcon.source import rcon


class RCON:

    def __init__(self, port: int, password: str, server_path: str, running_server_name: str):
        super().__init__()
        self.host = "127.0.0.1"  # defaults to localhost because rcon is an UNSAFE protocol, and shouldn't be used remotely on the clear web
        self.port = port
        self.password = password
        self.server_path = server_path
        self.running_server_name = running_server_name

    async def online_players(self) -> List[str]:
        response = await self._rcon("players")

        # first line of response is informative, ex:
        #   players online: Players connected (2):
        # all other lines are player names in the form of "-{name}", ex:
        #   -player1
        #   -player2
        return response.replace("-", "").strip().split("\n")[1:]

    async def restart_server(self):
        await self._rcon("quit")
        await asyncio.sleep(30)

        os.system(
            f"tmux send-keys -t zomboid-server 'cd {self.server_path} && bash start-server.sh -servername {self.running_server_name}' C-m"
        )
    
    async def list_current_settings(self) -> Dict[str, str]:
        response = await self._rcon("showoptions")

        # options are shown, one option per line, in the format "* {option_name}={value}", ex:
        #   * SpawnPoint=0,0,0
        option_per_line = response.split("\n")
        options = map(lambda option: option.lstrip("* ").split("="), option_per_line)
        return dict(options)
    
    async def change_setting(self, setting: str, value: str) -> str:
        response = await self._rcon("changeoption", setting, value)
        await self._rcon("reloadoptions")
        return response
    
    async def _rcon(self, command: str, *args: str):
        return await rcon(command, *args, host=self.host, port=self.port, passwd=self.password)

    # TODO
    # list lua vars
    # reload lua (command "reloadlua")
