import json
import threading
import struct

from WebsocketHandler import WebsocketHandler



serial_port = "/dev/ttyACM0"  # Update to match the serial port
hostaddr = "0.0.0.0"
port = 9000

SERIAL = False
WEBSOCKET = True
ws = None

if WEBSOCKET:
    ws = WebsocketHandler()

def parse_babelfishserial_command(command):
    """
    Parses a BabelFish command string into a dictionary, extracts byte values,
    performs bitwise operations, and converts the result to a formatted JSON packet. and conversion.
    """
    try:
        # Remove the newline and split the command
        cmd_parts = command.strip().split(":")
        
        if len(cmd_parts) < 2:
            raise ValueError("Invalid command format")
        
      
        json_command = {"CMD": "", "Data": {}}
        
        command_type = cmd_parts[0]
        json_command["CMD"] = command_type
        
       
        if command_type == 'WHO':
            json_command["Data"] = {
                "MID": cmd_parts[1],
                "PNo": cmd_parts[2],
                "TNo": cmd_parts[3],
            }
        
        elif command_type == 'TLM':
            byte_values = list(map(int, cmd_parts[2:]))
            if len(byte_values) == 2:
                value = struct.unpack('!e', bytes(byte_values))[0]
                datatype = "FL16"
            elif len(byte_values) == 4:
                value = struct.unpack('!f', bytes(byte_values))[0]
                datatype = "FL32"
            elif len(byte_values) == 8:
                value = struct.unpack('!d', bytes(byte_values))[0]
                datatype = "FL64"
            else:
                raise ValueError("Expected 2, 4, or 8 byte values")
            
            json_command["Data"] = {
                "MID": cmd_parts[1],
                "PID": int(cmd_parts[2], 16), 
                "Value": value,
                "datatype": datatype
            }
        
        elif command_type == 'TLT':
            byte_values = list(map(int, cmd_parts[3:]))
            if len(byte_values) == 2:
                value = struct.unpack('!e', bytes(byte_values))[0]
                datatype = "FL16"
            elif len(byte_values) == 4:
                value = struct.unpack('!f', bytes(byte_values))[0]
                datatype = "FL32"
            elif len(byte_values) == 8:
                value = struct.unpack('!d', bytes(byte_values))[0]
                datatype = "FL64"
            else:
                raise ValueError("Expected 2, 4, or 8 byte values")
            
            target_values = list(map(int, cmd_parts[6:]))
            if len(target_values) == 2:
                target = struct.unpack('!e', bytes(target_values))[0]
            elif len(target_values) == 4:
                target = struct.unpack('!f', bytes(target_values))[0]
            elif len(target_values) == 8:
                target = struct.unpack('!d', bytes(target_values))[0]
            else:
                raise ValueError("Expected 2, 4, or 8 byte values for Target")

            json_command["Data"] = {
                "MID": cmd_parts[1],
                "TID": cmd_parts[2],
                "Value": value,
                "Target": target,
                "datatype": datatype
            }
        
        elif command_type == 'FCK':
            error = ''.join(cmd_parts[2:9])
            json_command["Data"] = {
                "MID": cmd_parts[1],
                "ERR": error
            }
        
        else:
            raise ValueError("Unknown command type")

        return json_command
    
    except Exception as e:
        return {"error": str(e)}
    
def parse_babelfishws_command(command):
    # Parse the JSON packet and assemble into serial (on a per command basis (use switch or match case))
    pass



def handle_serial(serial_port):
    """
    Handles reading from the serial port, parsing commands, and sending them to the web socket.
    """
    try:
        
        uart = serial.Serial(serial_port, baudrate=115200, timeout=1)
        print(f"Listening on {serial_port} at 115200 baud...")

        while True:
            if uart.in_waiting > 0:
                raw_data = uart.readline().strip().decode('utf-8')
                parsed_command = parse_babelfishserial_command(raw_data)
                json_packet = json.dumps(parsed_command, indent=2)
                print(json_packet)
                ws.send(json_packet)
    except Exception as e:
        print(f"Error with UART: {e}")

def mainThread():
    while True:
        if ws is not None and ws.is_client_connected():
            if ws.msg_avail():
                message = ws.get_msg()
                print(f"Received from WebSocket: {message}")
            else:
                pass

def main():
    # Start serial port and socket handlers in separate threads
    main_thread = threading.Thread(target=mainThread)
    if SERIAL:
        serial_thread = threading.Thread(target=handle_serial, args=(serial_port,))
    if WEBSOCKET:
        socket_thread = ws.start_in_thread()

    if SERIAL:
        serial_thread.start()
    main_thread.start()

    try:
        main_thread.join()
        if SERIAL:
            serial_thread.join()
        if WEBSOCKET:
            socket_thread.join()
    except KeyboardInterrupt:
        print("Main program exiting...")

if __name__ == "__main__":
    main()