import json
import threading
import struct
import serial


from WebsocketHandler import WebsocketHandler


ws = WebsocketHandler()

serial_port = "/dev/ttyACM0"  # Update to match the serial port
hostaddr = "0.0.0.0"
port = 9000


def parse_babelfishserial_command(command):
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

def value_to_hex(value, precision=32):
    """
    Converts values based on type:
    - If it starts with "0x", return as is (already hex).
    - If it contains ".", convert it as a 32-bit IEEE 754 float.
    - If it is an integer, convert to hex.
    - Otherwise, return the string as is.
    """
    if isinstance(value, str) and value.startswith("0x"):  
        return value[2:].upper()  # Keep as hex, remove "0x" prefix

    elif isinstance(value, str) and "." in value:  
        # Convert float to IEEE 754 (single-precision)
        float_hex = struct.unpack('!I', struct.pack('!f', float(value)))[0]
        return hex(float_hex)[2:].upper()

    elif isinstance(value, str) and value.isdigit():  
        return hex(int(value))[2:].upper()

    elif isinstance(value, int):  
        return hex(value)[2:].upper()

    elif isinstance(value, float):  
        float_hex = struct.unpack('!I', struct.pack('!f', value))[0]
        return hex(float_hex)[2:].upper()

    else:  
        return value  # Return the string as-is
    

def parse_babelfishws_command(command):
    data = json.loads(command)
    cmd = data.get("CMD", "UNKNOWN")
    module_id = data.get("MID", "UNKNOWN")
    part_num = data.get("PNo", "UNKNOWN")
    t_no = data.get("TNo", "UNKNOWN")
    p_id = data.get("PID", "UNKNOWN")
    value = data.get("Data", {}).get("value", "UNKNOWN")
    target = data.get("Target", "UNKNOWN")
    data_type = data.get("Data", {}).get("datatype", "UNKNOWN")
    err = data.get("ERR", "UNKNOWN")
    command_ID = None
    match cmd:
        case "RQT":
            command_ID = "0x00"
            #logic that does something
            pass

        case "SET":
            command_ID = "0x01"
            #logic that does something
            pass

        case "RST":
            command_ID = "0x02"
            #logic that does something
            pass

        #List goes on for all possible sent commands and return commands

    serial_message = f"{cmd}:{value_to_hex(module_id)}:{value_to_hex(part_num)}:{value_to_hex(t_no)}:{value_to_hex(p_id)}:{value_to_hex(value)}:{value_to_hex(target)}:{value_to_hex(data_type)}:{value_to_hex(err)}\n"
    uart = serial.Serial(serial_port, baudrate=115200, timeout=1)
    uart.write(serial_message.encode('utf-8'))
    # Parse the JSON packet and assemble into serial (on a per command basis (use switch or match case))
    



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

#

def mainThread():
    while True:
        if ws.msg_avail():
            message = ws.get_msg()
            print(f"Received from WebSocket: {message}")
        else:
            pass

def main():
    # Start serial port and socket handlers in separate threads
    main_thread = threading.Thread(target=mainThread)
    serial_thread = threading.Thread(target=handle_serial, args=(serial_port,))
    socket_thread = ws.start_in_thread()


    serial_thread.start()
    socket_thread.start()
    main_thread.start()

    try:
        serial_thread.join()
        socket_thread.join()
    except KeyboardInterrupt:
        print("Main program exiting...")

if __name__ == "__main__":
    main()