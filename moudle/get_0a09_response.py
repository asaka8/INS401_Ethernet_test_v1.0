import time
import struct
import io
import random
from tqdm import trange
from INS401_Ethernet import Ethernet_Dev

class test:
    def __init__(self):
        self.uut = Ethernet_Dev()

    def sniff(self):
        result = self.uut.find_device(times=1)
        if result != True:
            return
        result = self.uut.ping_device()
        if result != True:
            print('Ethernet ping error.')
            return

    def find_packet(self):
        self.sniff()
        command = b'\x09\n'
        binfile = open('./log.bin', "ab")
        # cmd_type = struct.unpack('>H', command)[0]
        message_bytes = []
        self.uut.send_message(command, message_bytes)
        time.sleep(0.5) 
        get_response = self.uut.write_read_response(command, message_bytes, 0.1)
        save_info = get_response[2]
        binfile.write(save_info)
        print(save_info)

a = test()
a.find_packet()
        
        

