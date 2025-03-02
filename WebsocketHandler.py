import asyncio
import websockets
import threading

class WebsocketHandler:
    def __init__(self, host='localhost', port=8000):
        self.host = host
        self.port = port
        self.server = None
        self.loop = asyncio.new_event_loop()
        self.message_buffer = []
        self.clients = set()
        self.is_connected = False

    async def handler(self, websocket):
        self.clients.add(websocket)
        try:
            async for message in websocket:
                print(f"Received message: {message}")
                self.message_buffer.append(message)
                await websocket.send(f"Echo: {message}")
        finally:
            self.clients.remove(websocket)

    async def start_server(self):
        self.server = await websockets.serve(self.handler, self.host, self.port)
        print(f"WebSocket server started on ws://{self.host}:{self.port}")

    def send(self, message):
        for client in self.clients:
            asyncio.run_coroutine_threadsafe(client.send(message), self.loop)

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

    def is_client_connected(self):
        return len(self.clients) > 0