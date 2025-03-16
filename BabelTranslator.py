import json
import threading
import time
import psutil
import platform
import rssi

from WebsocketHandler import WebsocketHandler
from BabelSerialInterface import BabelSerialInterface
from BabelDataConverter import BabelDataHandler
from BabelParam import BabelParams
from BabelUtils import sendTLM, sendTLT, sendWHO, sendFCK, format_ws_message, format_serial_message
from StreamHandler import WebcamStreamHandler

conv = BabelDataHandler()

MODULEID = '0x01'
OS = platform.system()

serial_port = "/dev/ttyACM1"  # Update to match the serial port
hostaddr = "0.0.0.0"
port = 9000
apname = "Swinburne Rover Team"

SERIAL = True
WEBSOCKET = True
CAMERAS = False

cam = None
ws = None
serial = None
if WEBSOCKET:
    ws = WebsocketHandler(host=hostaddr,port=port,greeting=format_ws_message(sendWHO(MODULEID, 2, 2)))

if SERIAL:
    serial = BabelSerialInterface(serial_port)

if CAMERAS:
    cam = WebcamStreamHandler()

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
io = psutil.net_io_counters()
lastread = time.time()

def readinternals():
    #fetch internal sensor and update babel params
    try:
        if OS == 'Linux':
            #BabelP.set_param('0x00', psutil.sensors_temperatures()['coretemp'][0].current)
            pass
        else:
            BabelP.set_param('0x00', 0)
        BabelP.set_param('0x01', psutil.cpu_percent())
        #fetch network stats and update babel params
        #BabelP.set_param('0x02', rssi.getAPinfo([apname]).get('signal', 0))
        global io
        global lastread
        newio = psutil.net_io_counters()
        dt = time.time() - lastread
        BabelP.set_param('0x03', round((newio.bytes_sent - io.bytes_sent) / dt / 1000, 2))  # convert to kbps
        io = newio
        lastread = time.time()
    except Exception as e:
        print(f"Error reading internals: {e}")

def parse_babelfishserial_command(command):
    """
    Parses a BabelFish command string into a dictionary, extracts byte values,
    performs bitwise operations, and converts the result to a formatted JSON packet. and conversion.
    """
    try:
        # Remove the newline and split the command
        cmd_parts = command.split(":")
        if len(cmd_parts) < 2:
            raise ValueError("Invalid command format")
        json_command = {"CMD": "", "Data": {}}
        command_type = cmd_parts[0]
        json_command["CMD"] = command_type
        match command_type:
            case 'WHO':
                json_command = sendWHO(cmd_parts[1], cmd_parts[2], cmd_parts[3])
            case 'TLM':
                datatype = cmd_parts[7]
                #print(datatype)
                datatype = conv.hex_to_datatype(datatype)
                value = None
                match datatype:
                    case "INT32":
                        value = conv.bytes_to_int32(cmd_parts[3:7])
                    case "FL32":
                        value = conv.bytes_to_fl32(cmd_parts[3:7])
                    case "BOOL":
                        value = int(cmd_parts[3], 16)
                    case "ASCII":
                        value = ''.join([chr(int(x, 16)) for x in cmd_parts[3:7]])
                    
                json_command = sendTLM(cmd_parts[1], cmd_parts[2], value, datatype)
            case 'TLT':
                datatype = cmd_parts[7]
                #print(datatype)
                datatype = conv.hex_to_datatype(datatype)
                value = None
                target = None
                match datatype:
                    case "INT16":
                        value = conv.bytes_to_int16(cmd_parts[5:7])
                        target = conv.bytes_to_int16(cmd_parts[3:5])
                    case "FL16":
                        value = conv.bytes_to_fl16(cmd_parts[5:7])
                        target = conv.bytes_to_fl16(cmd_parts[3:5])
                    case "BOOL":
                        value = int(cmd_parts[5], 16)
                        target = int(cmd_parts[3], 16)
                    case "ASCII":
                        value = ''.join([chr(int(x, 16)) for x in cmd_parts[5:7]])
                        target = ''.join([chr(int(x, 16)) for x in cmd_parts[3:5]])
                json_command = sendTLT(cmd_parts[1], cmd_parts[2], value, datatype, target)
                
            case 'FCK':
                error = ''.join(cmd_parts[2:9])
                json_command = sendFCK(cmd_parts[1], error)
            case _:
                return None
        return json_command
    
    except Exception as e:
        print(f"Error parsing serial command: {e}")
        return None
    
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
                action = True
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
                ws_message = parse_babelfishserial_command(message)
                if ws_message is not None:
                    ws.send(format_ws_message(ws_message))
            else:
                pass
        readinternals()

        time.sleep(0.1)


def Camhandle():
    #set up camera interface + babel params
    BabelT.set_param('0x00', 0, 0)
    BabelT.set_param('0x01', 1, 1)
    cam.switch_camera(0, BabelT.get_param('0x00'))
    #cam.switch_camera(1, BabelT.get_param('0x01'))
    while True:
        cam1 = cam.getStream(0)

        #print(cam1.command)
        #isolate the /dev/videoX part (ffmpeg -f v4l2 -i /dev/video0 -c:v libx264 -preset ultrafast -tune zerolatency -f rtsp rtsp://0.0.0.0:8554/stream0)
        cam1 = cam1.command.split(" ")
        cam1 = cam1[4]
        cam1 = cam1.split("/dev/video")
        cam1 = int(cam1[1])
        if cam1 != BabelT.get_param('0x00'):
            cam.switch_camera(0, BabelT.get_param('0x00'))
        time.sleep(0.1)

def main():
    # Start serial port and socket handlers in separate threads
    main_thread = threading.Thread(target=mainThread)
    if SERIAL:
        serial_thread = serial.start_in_thread()
    if WEBSOCKET:
        socket_thread = ws.start_in_thread()
    if CAMERAS:
        cam_thread = threading.Thread(target=Camhandle)
        cam_thread.start()
    main_thread.start()

    try:
        main_thread.join()
        if SERIAL:
            serial_thread.join()
        if WEBSOCKET:
            socket_thread.join()
        if CAMERAS:
            cam_thread.join()
    except KeyboardInterrupt:
        print("Main program exiting...")

if __name__ == "__main__":
    main()
