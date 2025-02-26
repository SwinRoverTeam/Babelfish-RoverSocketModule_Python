import asyncio
import websockets
import threading

class WebsocketHandler:
    def __init__(self, host='localhost', port=9000):
        self.host = host
        self.port = port
        self.server = None
        self.loop = asyncio.new_event_loop()
        self.message_buffer = []

    async def handler(self, websocket, path):
        async for message in websocket:
            print(f"Received message: {message}")
            self.message_buffer.append(message)
            await websocket.send(f"Echo: {message}")

    async def start_server(self):
        self.server = await websockets.serve(self.handler, self.host, self.port)
        print(f"WebSocket server started on ws://{self.host}:{self.port}")
        await self.server.wait_closed()

    def send(self, message):
        asyncio.run_coroutine_threadsafe(self.server.send(message), self.loop)

    def run(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.start_server())
        self.loop.run_forever()

    def start_in_thread(self):
        thread = threading.Thread(target=self.run)
        thread.start()
        return thread

    def msg_avail(self):
        return len(self.message_buffer) > 0

    def get_msg(self):
        if self.msg_avail():
            return self.message_buffer.pop(0)
        return None