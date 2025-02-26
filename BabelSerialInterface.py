import serial  # PySerial for standard Python (I was testing this in my pc not using micropython)
import threading
import asyncio

class BabelSerialInterface:
    def __init__(self, serial_port):
        self.serial_port = serial_port
        self.loop = asyncio.new_event_loop()
        self.message_buffer = []

    async def read_serial(self):
        try:
            uart = serial.Serial(self.serial_port, baudrate=115200, timeout=1)
            print(f"Listening on {self.serial_port} at 115200 baud...")
            while True:
                if uart.in_waiting > 0:
                    raw_data = uart.readline().strip().decode('utf-8')
                    print(f"Received from serial: {raw_data}")
                    self.message_buffer.append(raw_data)
        except Exception as e:
            print(f"Error with UART: {e}")

    def run(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.read_serial())

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