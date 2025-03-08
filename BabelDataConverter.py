import struct


class BabelDataHandler:


    def hex_to_datatype(self,value):
        """
        Converts a hex string to a datatype.
        """
        number = int(value, 16)
        #print('number:',number)
        match number:
            case 1:
                return "BOOL"
            case 2:
                return "ASCII"
            case 4:
                return "INT32"
            case 5:
                return "INT64"
            case 6:
                return "FL16"
            case 7:
                return "FL32"
            case 8:
                return "FL64"
            
            case _:
                return None


    def bytes_to_int16(self, byte_array):
        valbytes = [int(x, 16) for x in byte_array[0:2]]
        value = struct.unpack('!h', bytes(valbytes))[0]
        return value
    
    def bytes_to_fl16(self, byte_array):
        valbytes = [int(x, 16) for x in byte_array[0:2]]
        value = struct.unpack('!e', bytes(valbytes))[0]
        return value
    
    def bytes_to_int32(self, byte_array):
        valbytes = [int(x, 16) for x in byte_array[0:4]]
        value = struct.unpack('!i', bytes(valbytes))[0]
        return value
    
    def bytes_to_fl32(self, byte_array):
        valbytes = [int(x, 16) for x in byte_array[0:4]]
        value = struct.unpack('!f', bytes(valbytes))[0]
        return value
    
    def fl32_to_bytes(self, value):
        valbytes = struct.pack('!f', value)
        return [hex(x) for x in valbytes]
    
    def int32_to_bytes(self, value):
        valbytes = struct.pack('!i', value)
        return [hex(x) for x in valbytes]