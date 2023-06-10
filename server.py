import asyncio
import logging
import websockets
import json
import names
from websockets import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosedOK
from datetime import datetime
import aiofile
from main import main as fetch_exchange_rate

logging.basicConfig(level=logging.INFO)


class Server:
    clients = set()

    async def register(self, ws: WebSocketServerProtocol):
        ws.name = names.get_full_name()
        self.clients.add(ws)
        logging.info(f"{ws.remote_address} connects")

    async def unregister(self, ws: WebSocketServerProtocol):
        self.clients.remove(ws)
        logging.info(f"{ws.remote_address} disconnects")

    async def send_to_clients(self, message: str):
        if self.clients:
            [await client.send(message) for client in self.clients]

    async def ws_handler(self, ws: WebSocketServerProtocol):
        await self.register(ws)
        try:
            await self.distrubute(ws)
        except ConnectionClosedOK:
            pass
        finally:
            await self.unregister(ws)

    async def distrubute(self, ws: WebSocketServerProtocol):
        async for message in ws:
            if message.startswith("exchange"):
                command, *args = message.split()

                try:
                    days = int(args[0])
                except (ValueError, IndexError):
                    await ws.send(
                        "Invalid command. Use format: exchange <days> <currencies>"
                    )
                    continue

                currencies = args[1:] if len(args) > 1 else ["USD", "EUR"]

                exchange_info = await fetch_exchange_rate(days, currencies)

                exchange_info_str = json.dumps(exchange_info, indent=2)

                await ws.send(exchange_info_str)

                async with aiofile.AIOFile("log.txt", "a") as afp:
                    await afp.write(
                        f"{datetime.now()}: Exchange command executed in chat\n"
                    )
                    await afp.fsync()
            else:
                await self.send_to_clients(f"{ws.name}: {message}")


async def main():
    server = Server()
    async with websockets.serve(server.ws_handler, "localhost", 8080):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
