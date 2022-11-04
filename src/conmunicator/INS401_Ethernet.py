import time
import threading
import struct
import sys
import datetime
import collections
from scapy.all import sendp, sniff, conf, AsyncSniffer

PING_TYPE     = [0x01, 0xcc]
COMMAND_START = [0x55, 0x55]

class Ethernet_Dev:
    '''Ethernet_Dev'''

    def __init__(self, options=None):
        super().__init__()
        self.type = '100base-t1'
        self.src_mac = None
        self.dst_mac = 'FF:FF:FF:FF:FF:FF'
        self.ethernet_name = None
        self.data = None
        self.iface = None

        self.filter_device_type = None
        self.filter_device_type_assigned = False
        self.receive_packet_count = 0
        self.tlock = threading.Lock()

        self.iface_confirmed = False
        
        self.serial_number = None
        self.model_string = None
        self.app_version = None
        self.receive_cache = collections.deque(maxlen=10000)

        if options and options.device_type != 'auto':
            self.filter_device_type = options.device_type
            self.filter_device_type_assigned = True

    def reset_dev_info(self):
        self.app_version = None
        self.dst_mac = 'FF:FF:FF:FF:FF:FF'
        self.src_mac = None
        self.iface = None
        self.model_string = None
        self.read_result = None
        self.serial_number = None
        return

    def handle_receive_packet(self, packet):
        self.iface_confirmed = True
        self.dst_mac = packet.src

    def confirm_iface(self, iface, times):
        '''
        iface[0]: mac of target INS401
        iface[1]: mac of laptop
        '''
        filter_exp = 'ether dst host ' + \
            iface[1] + ' and ether[16:2] == 0x01cc'
        src_mac = bytes([int(x, 16) for x in iface[1].split(':')])
        command_line = self.build_packet(
            self.get_dst_mac(), src_mac, PING_TYPE)
        async_sniffer = AsyncSniffer(
            iface=iface[0], prn=self.handle_receive_packet, filter=filter_exp)
        async_sniffer.start()
        time.sleep(0.01)
        sendp(command_line, iface=iface[0], verbose=0, count = 2)
        time.sleep(0.5)
        async_sniffer.stop()

        if self.iface_confirmed:
            self.iface = iface[0]
            self.src_mac = iface[1]
            if times == 1:
                print('[NetworkCard]', self.iface)
            else:
                pass

    def find_device(self, times, callback = None, retries=1, not_found_handler=None):
        result = False
        self.device = None
        self.iface_confirmed = False

        # find network connection
        ifaces_list = self.get_network_card()
        for i in range(len(ifaces_list)):
            self.confirm_iface(ifaces_list[i], times)
            if self.iface_confirmed:
                result = True
                break
            else:
                if i == len(ifaces_list) - 1:
                    result = False
                    print('No available Ethernet card was found.')
                    break
        return result

    def open(self):
        '''
        open
        '''

    def close(self):
        '''
        close
        '''

    def can_write(self):
        if self.iface:
            return True
        return False

    def write(self, data, is_flush=False):
        '''
        write
        '''
        try:
            sendp(data, iface=self.iface, verbose=0) 
            # print(data)
        except Exception as e:
            raise

    def read(self, count = 0,filter_cmd_type=0,callback=None, timeout = 1):
        '''
        read
        '''
        if filter_cmd_type:
            filter_exp = 'ether dst host ' + self.src_mac + \
                ' and ether[16:2] == %d' % filter_cmd_type
        else:
            filter_exp = 'ether dst host ' + self.src_mac
            
        sniff(prn=callback, count=count, iface=self.iface, filter=filter_exp, timeout = timeout)

    def read_data(self):
        try:
            data = self.receive_cache.popleft()
        except:
            data = None
        return data

    def start_listen_data(self, filter_type=None, log2pcap=False):
        hard_code_mac = '04:00:00:00:00:04'
        if filter_type == None:
            filter_exp = f'ether src host {self.dst_mac} or {hard_code_mac} '
        elif isinstance(filter_type, int):
            filter_exp = f'ether src host {self.dst_mac} or {hard_code_mac}  and ether[16:2] == {filter_type}'
        elif isinstance(filter_type, list):
            filter_exp = f'ether src host {self.dst_mac} or {hard_code_mac}  and ether[16:2] == {filter_type[0]}'
            for i in range(len(filter_type)-1):
                filter_exp += f' || ether[16:2] == {filter_type[i+1]}'
        if log2pcap == False:
            self.async_sniffer = AsyncSniffer(
                iface=self.iface, prn=self.handle_catch_packet, filter=filter_exp, store=0)
        elif log2pcap == True:
            self.async_sniffer = AsyncSniffer(
                iface=self.iface, prn=self.handle_catch_whole_eth_packet, filter=filter_exp, store=0)
        self.tlock.acquire()
        self.async_sniffer.start()
        time.sleep(0.1)

    def start_listen_data_nmea(self, filter_type=None, log2pcap=False):
        hard_code_mac = '04:00:00:00:00:04'
        if filter_type == None:
            filter_exp = f'ether src host {self.dst_mac} or {hard_code_mac} '
        elif isinstance(filter_type, int):
            filter_exp = f'ether src host {self.dst_mac} or {hard_code_mac}  and ether[17:2] == {filter_type}'
        elif isinstance(filter_type, list):
            filter_exp = f'ether src host {self.dst_mac} or {hard_code_mac}  and ether[17:2] == {filter_type[0]}'
            for i in range(len(filter_type)-1):
                filter_exp += f' || ether[17:2] == {filter_type[i+1]}'
        if log2pcap == False:
            self.async_sniffer = AsyncSniffer(
                iface=self.iface, prn=self.handle_catch_packet, filter=filter_exp, store=0)
        elif log2pcap == True:
            self.async_sniffer = AsyncSniffer(
                iface=self.iface, prn=self.handle_catch_whole_eth_packet, filter=filter_exp, store=0)
        self.tlock.acquire()
        self.async_sniffer.start()
        time.sleep(0.1)

    def stop_listen_data(self):
        self.async_sniffer.stop()
        self.tlock.release()

    def check_len(self):
        return len(self.receive_cache)
    
    def handle_catch_packet(self, packet):
        packet_raw = bytes(packet)[12:]
        self.receive_cache.append(packet_raw[2:])

    def handle_catch_whole_eth_packet(self, packet):
        self.receive_cache.append(packet)
    
    def handle_receive_read_result(self, packet):
        self.read_result = bytes(packet)

    def write_read(self, data, filter_cmd_type=0, timeout = 0.1):
        if not self.src_mac:
            return None
    
        if filter_cmd_type:
            filter_exp = 'ether dst host ' + self.src_mac + \
                ' and ether[16:2] == %d' % filter_cmd_type
        else:
            filter_exp = 'ether dst host ' + self.src_mac

        self.read_result = None
        async_sniffer = AsyncSniffer(
            iface=self.iface, prn=self.handle_receive_read_result, filter=filter_exp, store=0)
        async_sniffer.start()
        time.sleep(0.01)
        sendp(data, iface=self.iface, verbose=0)

        time.sleep(timeout)
        async_sniffer.stop()
        if self.read_result:
            return self.read_result

        return None

    def handle_async_receive_read_result(self, packet):
        read_line = bytes(packet)
        if read_line:
            packet_raw = read_line[14:]
            packet_length = struct.unpack('<I', packet_raw[4:8])[0]
            packet_crc = list(packet_raw[packet_length+8:packet_length+10])
            
            # packet crc
            if packet_crc == self.calc_crc(packet_raw[2:8+packet_length]): 
                self.receive_packet_count = self.receive_packet_count + 1
            else:
                print('crc error')
                pass

    def async_write_read(self, command, message, count = 1):
        if not self.src_mac:
            return False
    
        command_line = self.build_packet(self.get_dst_mac(), self.get_src_mac(), command, message)
        
        cmd_type = struct.unpack('>H', command)[0]  
        
        if cmd_type:
            filter_exp = 'ether dst host ' + self.src_mac + \
                ' and ether[16:2] == %d' % cmd_type
        else:
            filter_exp = 'ether dst host ' + self.src_mac
        
        self.receive_packet_count = 0
        async_sniffer = AsyncSniffer(
            iface=self.iface, prn=self.handle_async_receive_read_result, filter=filter_exp, store=0)
        async_sniffer.start()
        
        time.sleep(1)
        print('Long term Test start time at :[{0}]'.format(
                datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
                
        for i in range(count):
            if i % 1000 == 0 or i == count - 1:
                print(i)
                time.sleep(0.2)
                
            sendp(command_line, iface=self.iface, verbose=0)


        time.sleep(5)
        print('Long term Test end time at :[{0}]'.format(
                datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        async_sniffer.stop()
        
        print(self.receive_packet_count, count)
        if self.receive_packet_count == count:
            return True
        else:
            return False
        
    def reset_buffer(self):
        self.receive_cache = collections.deque(maxlen=100000)

    def get_src_mac(self):
        if self.src_mac:        
            return bytes([int(x, 16) for x in self.src_mac.split(':')])
        return None

    def get_dst_mac(self):
        if self.dst_mac:
            return bytes([int(x, 16) for x in self.dst_mac.split(':')])
        return None

    def get_network_card(self):
        network_card_info = []
        for item in conf.ifaces:
            if conf.ifaces[item].ip == '127.0.0.1' or conf.ifaces[item].mac == '':
                continue
            network_card_info.append(
                (conf.ifaces[item].name, conf.ifaces[item].mac))
        return network_card_info

    # appends Header and Calculates CRC on data
    # data should have packet_type + payload_len + payload
    def build_packet(self, dest, src, message_type, message_bytes=[]):
        header = [0x55, 0x55]
        packet = []
        
        if not dest or not src:
            return None
                
        packet.extend(message_type)
        msg_len = len(message_bytes)

        packet_len = struct.pack("<I", msg_len)

        packet.extend(packet_len)
        final_packet = packet + message_bytes

        msg_len = len(COMMAND_START) + len(final_packet) + 2
        payload_len = struct.pack('<H', len(COMMAND_START) + len(final_packet) + 2)

        whole_packet=[]
        header = dest + src + bytes(payload_len)
        whole_packet.extend(header)

        whole_packet.extend(COMMAND_START)
        whole_packet.extend(final_packet)
        whole_packet.extend(self.calc_crc(final_packet))
        if msg_len < 46:
            fill_bytes = bytes(46-msg_len)
            whole_packet.extend(fill_bytes)

        return bytes(whole_packet)
        #print data
        # At this point, data is ready to send to the UUT
        # return data

    # appends Header and Calculates CRC on data
    # data should have packet_type + payload_len + payload
    def send_message(self,  command, message=[]):
        command_line = self.build_packet(self.get_dst_mac(), self.get_src_mac(), command, message)
        self.write(command_line)

    # returns Packet_type, Payload_length, payload
    def write_read_response(self, command, message=[], timeout = 1): 
        packet_type = []
        packet_length = 0
        packet_length_list = []
        data_buffer = []
        
        command_line = self.build_packet(self.get_dst_mac(), self.get_src_mac(), command, message)
        
        cmd_type = struct.unpack('>H', command)[0]         
        read_line = self.write_read(command_line, cmd_type, timeout)

        if read_line:
            packet_raw = read_line[14:]
            packet_type = packet_raw[2:4]
            if packet_type == command:
                packet_length_list = packet_raw[4:8]
                packet_length = struct.unpack('<I', packet_raw[4:8])[0]
                packet_crc = list(packet_raw[packet_length+8:packet_length+10])
 
                # packet crc
                if packet_crc == self.calc_crc(packet_raw[2:8+packet_length]): 
                    data_buffer = packet_raw[8:8+packet_length]
                else:
                    print('crc error')
                    pass

        return packet_type, packet_length_list, data_buffer
  

    # returns true if ping was successful
    def ping_device(self):
        command_line = self.build_packet(
        self.get_dst_mac(), self.get_src_mac(), PING_TYPE)

        data_buffer = []
        cmd_type = struct.unpack('>H', bytes(PING_TYPE))[0]
        read_line = self.write_read(command_line, cmd_type, 2)
        if read_line:
            packet_raw = read_line[14:]
            packet_type = packet_raw[2:4]
            if packet_type == bytes(PING_TYPE):
                packet_length = struct.unpack('<I', packet_raw[4:8])[0]
                data_buffer = packet_raw[8: 8 + packet_length]
                info_text = self.format_string(data_buffer)
                if info_text.find('INS401') > -1:
                    # print(info_text)
                    split_text = info_text.split(' ')
                    self.model_string = split_text[0]
                    self.serial_number = int(split_text[2])
                    self.app_version = split_text[7]
                    return True

        return False

   
    def format_string(self, data_buffer):
        parsed = bytearray(data_buffer) if data_buffer and len(
            data_buffer) > 0 else None

        formatted = ''
        if parsed is not None:
            try:
                if sys.version_info < (3, 0):
                    formatted = str(struct.pack(
                        '{0}B'.format(len(parsed)), *parsed))
                else:
                    formatted = str(struct.pack(
                        '{0}B'.format(len(parsed)), *parsed), 'utf-8')
            except UnicodeDecodeError:
                APP_CONTEXT.get_logger().logger.error('Parse data as string failed')
                formatted = ''

        return formatted

    def calc_crc(self, payload):
        '''
        Calculates 16-bit CRC-CCITT
        '''
        crc = 0x1D0F
        for bytedata in payload:
            crc = crc ^ (bytedata << 8)
            i = 0
            while i < 8:
                if crc & 0x8000:
                    crc = (crc << 1) ^ 0x1021
                else:
                    crc = crc << 1
                i += 1

        crc = crc & 0xffff
        crc_msb = (crc & 0xFF00) >> 8
        crc_lsb = (crc & 0x00FF)
        return [crc_msb, crc_lsb]
        
    def bytearray2string(self, data = []):
        str_list = ''
        for i in range(len(data)):
            str_list += chr(data[i])