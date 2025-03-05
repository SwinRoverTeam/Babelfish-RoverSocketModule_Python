import json
import struct

def format_ws_message(data):
    """
    Formats a BabelFish command dictionary into a JSON string.
    """
    return json.dumps(data)
def format_serial_message(data):
    """
    Formats a BabelFish command dictionary into a serial command string.
    """
    cmd = data.get("CMD", "UNKNOWN")
    payload = data.get("Data", {})
    if cmd == "RQT":
        return f"{cmd}:{payload.get('MID', 0)}:{payload.get('PNo', 0)}:{payload.get('TNo', 0)}\n"
    elif cmd == "SET":
        return f"{cmd}:{payload.get('MID', 0)}:{payload.get('PID', 0)}:{payload.get('Value', 0)}\n"
    elif cmd == "RST":
        return f"{cmd}:{payload.get('MID', 0)}\n"
    else:
        return None

def getDatatype(value):
    if type(value) == int:
        return "INT"
    elif type(value) == float:
        return "FL32"
    elif type(value) == str:
        return "STR"
    else:
        return None
    

def sendTLM(MID,PID,Value,datatype):
    json_command = {"CMD": "TLM", "Data": {}}
    json_command["Data"] = {
        "MID": MID,
        "PID": PID, 
        "Value": Value,
        "datatype": datatype
    }
    return json_command

def sendTLT(MID,PID,Value,datatype,Target):
    json_command = {"CMD": "TLT", "Data": {}}
    json_command["Data"] = {
        "MID": MID,
        "PID": PID, 
        "Value": Value,
        "datatype": datatype,
        "Target": Target
    }
    return json_command

def sendWHO(MID,PNo,TNo):
    json_command = {"CMD": "WHO", "Data": {}}
    json_command["Data"] = {
        "MID": MID,
        "PNo": PNo,
        "TNo": TNo
    }
    return json_command

def sendFCK(MID, ERR):
    json_command = {"CMD": "FCK", "Data": {}}
    json_command["Data"] = {
        "MID": MID,
        "ERR": ERR
    }
    return json_command
