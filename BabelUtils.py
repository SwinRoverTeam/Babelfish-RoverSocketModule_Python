import json
from BabelDataConverter import BabelDataHandler

conv = BabelDataHandler()

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
    match cmd:
        case "DMP":
            return f"{cmd}:{payload.get('MID', 0)}:0x00:0x00:0x00:0x00:0x00:0x00:0x00\n"
        case "RQT":
            isTarget = payload.get("T", False)
            if isTarget:
                return f"{cmd}:{payload.get('MID', 0)}:{payload.get('TID', 0)}:0x01:0x00:0x00:0x00:0x00:0x00\n"
            else:
                return f"{cmd}:{payload.get('MID', 0)}:{payload.get('PID', 0)}:0x00:0x00:0x00:0x00:0x00:0x00\n"
        case "SET":
            value = payload.get("Value", 0)
            datatype = payload.get("datatype", "FL32")
            match datatype:
                case "FL32":
                    value = conv.fl32_to_bytes(value)
                    return f"{cmd}:{payload.get('MID', 0)}:{payload.get('TID', 0)}:0x00:{value[0]}:{value[1]}:{value[2]}:{value[3]}:0x07\n"
                case "INT32":
                    value = conv.int32_to_bytes(value)
                    return f"{cmd}:{payload.get('MID', 0)}:{payload.get('TID', 0)}:0x00:{value[0]}:{value[1]}:{value[2]}:{value[3]}:0x04\n"
                case "BOOL":
                    value = 1 if value else 0
                    return f"{cmd}:{payload.get('MID', 0)}:{payload.get('TID', 0)}:0x00:0x00:0x00:0x00:0x0{value}:0x01\n"
                case "ASCII":
                    value = [hex(ord(x)) for x in value]
                    return f"{cmd}:{payload.get('MID', 0)}:{payload.get('TID', 0)}:0x00:{value[0]}:{value[1]}:{value[2]}:{value[3]}:0x02\n"
        case "RST":
            return f"{cmd}:{payload.get('MID', 0)}:0x00:0x00:0x00:0x00:0x00:0x00\n"
        case _:
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

def sendTLT(MID,TID,Value,datatype,Target):
    json_command = {"CMD": "TLT", "Data": {}}
    json_command["Data"] = {
        "MID": MID,
        "TID": TID, 
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
