import asyncio
import os
from typing import List
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
        response = await rcon(
            "players", host=self.host, port=self.port, passwd=self.password
        )

        # first line of response is informative, ex:
        #   players online: Players connected (3):
        # all other lines are player names in the form of "-{name}", ex:
        #   -player1
        #   -player2
        return response.replace("-", "").strip().split("\n")[1:]

    async def restart_server(self):
        await rcon("quit", host=self.host, port=self.port, passwd=self.password)
        await asyncio.sleep(30)

        os.system(
            f"tmux send-keys -t zomboid-server 'cd {self.server_path} && bash start-server.sh -servername {self.running_server_name}' C-m"
        )
