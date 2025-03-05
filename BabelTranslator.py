import json
import threading
import struct
import time
import psutil
import platform

from WebsocketHandler import WebsocketHandler
from BabelSerialInterface import BabelSerialInterface
from BabelParam import BabelParams
from BabelUtils import sendTLM, sendTLT, sendWHO, sendFCK, format_ws_message, format_serial_message, getDatatype




MODULEID = '0x01'
OS = platform.system()

serial_port = "/dev/ttyACM0"  # Update to match the serial port
hostaddr = "0.0.0.0"
port = 9000

SERIAL = False
WEBSOCKET = True
ws = None
serial = None
if WEBSOCKET:
    ws = WebsocketHandler(greeting=format_ws_message(sendWHO(MODULEID, 2, 2)))

if SERIAL:
    serial = BabelSerialInterface(serial_port)

BabelP = BabelParams()
BabelT = BabelParams()

#BabelParams
#0 - CPU Temp
#1 - CPU Load
#2 - Net RSSI
#3 - Net Bandwidth

#BabelTargets
#0 - Stream1
#1 - Stream2




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
            json_command = sendWHO(cmd_parts[1], cmd_parts[2], cmd_parts[3])
            
        
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
            json_command = sendTLM(cmd_parts[1], cmd_parts[2], value, datatype)
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
    action = False
    data = json.loads(command)
    print(data)
    cmd = data.get("CMD", "UNKNOWN")
    print(cmd)
    payload = data.get("Data", {})
    print(payload)
    match cmd:
        case "DMP":
            MID = payload.get("MID", 0)
            if MID == MODULEID:
                action = True
                #send all params and targets to websocket
                p = BabelP.get_all()
                t = BabelT.get_all()
                for i in p:
                    msg = sendTLM(MID, i.name, i.value, "FL32")
                    ws.send(format_ws_message(msg))
                for i in t:
                    msg = sendTLT(MID, i.name, i.value, "FL32", i.target)
                    ws.send(format_ws_message(msg))
            else:
                #forward the command to the serial port
                pass
        case "RQT":
            #request a babel param/target
            MID = payload.get("MID", 0)
            if MID == MODULEID:
                action = True
                if payload.get("T") == False:
                    #get param and send to websocket
                    value = BabelP.get_param(payload.get("PID"))
                    msg = sendTLM(MID, payload.get("PID"), value, "FL32")
                    ws.send(format_ws_message(msg))
                    pass
                elif payload.get("T") == True:
                    #get target
                    
                    value = BabelT.get_param(payload.get("TID"))
                    msg = sendTLT(MID, payload.get("TID"), value, "FL32", payload.get("TID"))
                    ws.send(format_ws_message(msg))
                    pass
                else:
                    #invalid target
                    pass
            else:
                #forward the command to the serial port
                pass

        case "SET":
            MID = payload.get("MID", 0)
            if MID == MODULEID:
                action = True
                TID = payload.get("TID")
                BabelT.set_param(TID, payload.get("Value"))
            else:
                #forward the command to the serial port
                pass

        case "RST":
            MID = payload.get("MID", 0)
            if MID == MODULEID:
                pass
            else:
                #forward the command to the serial port
                pass
    if not action:
        #pass command to serial
        msg = format_serial_message(data)
        return msg
    else:
        return None
        #List goes on for all possible sent commands and return commands

    
def mainThread():
    #set up camera interface + babel params
    BabelT.set_param('0x00', 0, 0)
    BabelT.set_param('0x01', 1, 1)

    while True:
        if ws is not None and ws.is_client_connected():
            if ws.msg_avail():
                message = ws.get_msg()
                print(f"Received from WebSocket: {message}")
                serial_message = parse_babelfishws_command(message)
                print(f"Sending to Serial: {serial_message}")
                if serial is not None and serial_message is not None:
                    serial.send(serial_message)
            else:
                pass
        if serial is not None:
            if serial.msg_avail():
                message = serial.get_msg()
                print(f"Received from Serial: {message}")
                
            else:
                pass
        # fetch internal sensor and update babel params
        if OS == 'Linux':
            BabelP.set_param('0x00', psutil.sensors_temperatures()['coretemp'][0].current)
        else:
            BabelP.set_param('0x00', 0)
        BabelP.set_param('0x01', psutil.cpu_percent())


        time.sleep(0.1)

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


def main():
    # Start serial port and socket handlers in separate threads
    main_thread = threading.Thread(target=mainThread)
    if SERIAL:
        serial_thread = serial.start_in_thread()
    if WEBSOCKET:
        socket_thread = ws.start_in_thread()

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