import json
import socket
import threading
import struct
import websocket  # Use the websocket-client library

def parse_babelfish_command(command):
    """
    Parses a BabelFish command string into a dictionary, extracts byte values,
    performs bitwise operations, and converts the result to a formatted JSON packet.
    """
    try:
        # Remove the newline and split the command
        cmd_parts = command.strip().split(":")
        if len(cmd_parts) < 2:
            raise ValueError("Invalid command format")

        command_type = cmd_parts[0]
        byte_values = list(map(int, cmd_parts[1:]))

        if len(byte_values) not in [2, 4, 8]:
            raise ValueError("Expected 2, 4, or 8 byte values")

        if len(byte_values) == 2:
            value = struct.unpack('!e', bytes(byte_values))[0]  # 16-bit half-precision float
            data_type = "FL16"
        elif len(byte_values) == 4:
            value = struct.unpack('!f', bytes(byte_values))[0]  # 32-bit float
            data_type = "FL32"
        else:
            value = struct.unpack('!d', bytes(byte_values))[0]  # 64-bit float
            data_type = "FL64"

        return {
            "CMD": command_type,
            "Data": {
                "type": data_type,
                "value": value
            }
        }
    except Exception as e:
        return {"error": str(e)}

def transmit_command(json_packet, host="0.0.0.0", port=9000):
    """
    Sends a JSON packet to the specified host and port.
    """
    try:
        ws = websocket.create_connection(f"ws://{host}:{port}")
        ws.send(json_packet)
        ws.close()
    except Exception as e:
        print(f"Error sending packets: {e}")

def handle_serial(serial_port):
    """
    Handles reading from the serial port, parsing commands, and sending them to the web socket.
    """
    try:
        import serial  # PySerial for standard Python (I was testing this in my pc not using micropython)
        uart = serial.Serial(serial_port, baudrate=115200, timeout=1)
        print(f"Listening on {serial_port} at 115200 baud...")

        while True:
            if uart.in_waiting > 0:
                raw_data = uart.readline().strip().decode('utf-8')
                parsed_command = parse_babelfish_command(raw_data)
                json_packet = json.dumps(parsed_command, indent=2)
                print(json_packet)
                transmit_command(json_packet)  # Call the synchronous function
    except Exception as e:
        print(f"Error with UART: {e}")

def receive_command(host="0.0.0.0", port=8000):
    """
    Handles receiving BabelFish commands over a TCP socket.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind((host, port))
            server_socket.listen(5)
            print(f"Listening for BabelFish commands on {host}:{port}...")

            while True:
                client_socket, client_address = server_socket.accept()
                with client_socket:
                    print(f"Connection established with {client_address}")
                    raw_data = client_socket.recv(1024).decode('utf-8').strip()
                    if raw_data:
                        parsed_command = parse_babelfish_command(raw_data)
                        json_packet = json.dumps(parsed_command, indent=2)
                        print(json_packet)
                        transmit_command(json_packet)  # Call the synchronous function
    except Exception as e:
        print(f"Error with socket: {e}")

def main():
    serial_port = "/dev/ttyACM0"  # Update to match the serial port

    # Start serial port and socket handlers in separate threads
    serial_thread = threading.Thread(target=handle_serial, args=(serial_port,))
    socket_thread = threading.Thread(target=receive_command)

    serial_thread.start()
    socket_thread.start()

    try:
        serial_thread.join()
        socket_thread.join()
    except KeyboardInterrupt:
        print("Main program exiting...")

if __name__ == "__main__":
    main()