import os
import time
import struct
import random
import math
import threading 

from tqdm import trange
from ..conmunicator.INS401_Ethernet import Ethernet_Dev
from moudle.gps_time_module import get_curr_time, gps_time, cal_time_diff, stamptime_to_datetime
from moudle.nmea_module import *
from ..test_framwork.Jsonf_Creater import Json_Creat
from ..test_framwork.Test_Logger import TestLogger

INPUT_PACKETS = [b'\x01\xcc', b'\x02\xcc', b'\x03\xcc', b'\x04\xcc', b'\x05\xcc', b'\x06\xcc', b'\x01\x0b', b'\x02\x0b', b'\x07\xcc']
OTHER_OUTPUT_PACKETS = [b'\x01\n', b'\x02\n', b'\x03\n', b'\x04\n', b'\x05\n', b'\x06\n']

rtcm_data = [1, 2, 3, 4, 5, 6, 7, 8]
vehicle_speed_value = 80
LONGTERM_RUNNING_COUNT = 10000

class Test_Scripts:
    uut = None

    def __init__(self, device):
        self.eth = Ethernet_Dev()
        Test_Scripts.uut = device
        self.tlock = threading.Lock()
        self.product_sn = None
        self.test_time = time.strftime("%Y_%m_%d_%H_%M_%S", time.localtime())
        jsonf = Json_Creat()
        self.test_log = TestLogger()
        self.properties = jsonf.creat()
    
    def hex_string(self, number_bytes = []):
        if number_bytes is None:
            return None
        return hex(int(struct.unpack('<H', number_bytes)[0]))

    ### section1  User command test function ###

    def get_production_info(self):
        message_bytes = []
        command = INPUT_PACKETS[0]
        response = self.uut.write_read_response(command, message_bytes, 0.1)
        info_text = response[2].decode()
        expect_info = self.properties["productINFO"]

        if info_text == expect_info:
            return True, info_text, expect_info
        else:
            return False, info_text, expect_info
    
    def info_separator_check(self):
        old_separator = ','
        expect_separator = ' '
        message_bytes = []
        command = INPUT_PACKETS[0]
        response = self.uut.write_read_response(command, message_bytes, 0.1)
        info_text = response[2].decode()
        self.product_sn = info_text.split(' ')[2]

        if info_text.find(old_separator) == -1:
            return True, f"{expect_separator}", f"{expect_separator}"
        else:
            return False, f"{old_separator}", f"{expect_separator}"

    def get_user_configuration_parameters(self):
        command = INPUT_PACKETS[1]
        
        for field_id in range(12):
            message_bytes = []
            field_id_bytes = struct.pack('<I', field_id)
            message_bytes.extend(field_id_bytes)

            response = self.uut.write_read_response(command, message_bytes, 0.1)
 
        if response[0] == command:
            return True, f'{response[0].hex()}', f'{command.hex()}'
        else:
            return True, f'{response[0].hex()}', f'{command.hex()}'
                
    def set_user_configuration(self):
        command = INPUT_PACKETS[2]
        
        for field_id in range(12):
            message_bytes = []
            field_id_bytes = struct.pack('<I', field_id)
            message_bytes.extend(field_id_bytes)

            if field_id >= 0 and field_id < 12:
                field_value_bytes = struct.pack('<f', 0)
                message_bytes.extend(field_value_bytes)
                
            response = self.uut.write_read_response(command, message_bytes, 0.1)
                
        if response[0] == command:
            return True, f'{response[0].hex()}', f'{command.hex()}'
        else:
            return True, f'{response[0].hex()}', f'{command.hex()}'  
 
    def save_user_configuration(self):
        command = INPUT_PACKETS[3]
        message_bytes = []

        response = self.uut.write_read_response(command, message_bytes, 0.1)

        if response[0] == command:
            return True, f'{response[0].hex()}', f'{command.hex()}'
        else:
            return True, f'{response[0].hex()}', f'{command.hex()}'  
            
    def send_system_reset_command(self):
        reset_command = INPUT_PACKETS[5]
        ping_command = INPUT_PACKETS[0]
        message_bytes = []

        reset_response = self.uut.write_read_response(reset_command, message_bytes, 0.1)
        if reset_response[0] == reset_command:
            is_get_reset_response = True
        else:
            is_get_reset_response = False
        time.sleep(30)
        self.eth.find_device(times=1)
        self.eth.ping_device()
        ping_response = self.eth.write_read_response(ping_command, message_bytes, 0.1)
        if ping_response[0] == ping_command:
            is_get_ping_response = True
        else:
            is_get_ping_response = False
        
        if is_get_reset_response == True and is_get_ping_response == True:
            return True, f'INS401 reset: {is_get_reset_response} INS401 reconnect: {is_get_ping_response}', f'INS401 reset: True INS401 reconnect: True'
        else:
            return False, f'INS401 reset: {is_get_reset_response} INS401 reconnect: {is_get_ping_response}', f'INS401 reset: True INS401 reconnect: True'

    def set_base_rtcm_data(self):
        '''TODO
        1. add ntrip to provide rtcm base data
        2. check whether position type in GNSS Solution packet turn to 4 from 1
        3. log the ntrip data
        '''
        command = INPUT_PACKETS[7]
        message_bytes = []
        
        message_bytes.extend(rtcm_data)
        
        for i in range(10):
            self.uut.send_message(command, message_bytes)
            time.sleep(1)
        
        return True, self.hex_string(command), self.hex_string(command)
        
    def set_vehicle_speed_data(self):
        '''TODO
        1. use real odo data to do this test
        2. check whether the Ether port have odo data output
        '''
        command = INPUT_PACKETS[6]
        message_bytes = []        

        field_value_bytes = struct.pack('<f', vehicle_speed_value)
        message_bytes.extend(field_value_bytes)
        
        self.uut.send_message(command, message_bytes)
        
        return True, self.hex_string(command), self.hex_string(command)

    ### section2 Output ODR packet test function ###

    def output_packet_gnss_solution_test(self):
        result = False
        interval = None
        logf_name = f'./data/Packet_ODR_test_data/{self.product_sn}_{self.test_time}/gnss_solution.bin'
        self.test_log.creat_binf_sct2(file_name=logf_name, sn_num=self.product_sn, test_time=self.test_time)
 
        gps_millisecs_lst = []
        self.uut.start_listen_data(0x020a)
        start_time = time.time()
        self.uut.reset_buffer()
        while time.time() - start_time <= 120:
            data = self.uut.read_data()
            if data is not None:
                self.test_log.write2bin(data)
                parse_data = data[8:8+77]
                fmt = '<HIBdddfffBBffffffff'
                parse_data_lst = struct.unpack(fmt, parse_data)
                gps_week = parse_data_lst[0]
                gps_millisecs = parse_data_lst[1]
                gps_sec = gps_time(gps_week, gps_millisecs)
                gps_millisecs_lst.append(gps_sec)
        self.uut.stop_listen_data()

        for i in range(len(gps_millisecs_lst)):
            if i + 1 < len(gps_millisecs_lst):
                interval = gps_millisecs_lst[i+1] - gps_millisecs_lst[i]
            else:
                break
            if interval >= 999 or interval <= 1001:
                result = True
            else:
                result = False
                break
        
        if result == True:
            return result, f'{interval}', f'~1000.0'
        else:
            return result, f'{interval}', f'~1000.0'
            
    def output_packet_ins_solution_test(self):
        result = False
        interval = None
        logf_name = f'./data/Packet_ODR_test_data/{self.product_sn}_{self.test_time}/ins_solution.bin'
        self.test_log.creat_binf_sct2(file_name=logf_name, sn_num=self.product_sn, test_time=self.test_time)
 
        gps_millisecs_lst = []
        self.uut.start_listen_data(0x030a)
        start_time = time.time()
        self.uut.reset_buffer()
        while time.time() - start_time <= 120:
            data = self.uut.read_data()
            if data is not None:
                self.test_log.write2bin(data)
                parse_data = data[8:8+110]
                fmt = '<HIBBdddfffffffffffffffffffH'
                parse_data_lst = struct.unpack(fmt, parse_data)
                gps_week = parse_data_lst[0]
                gps_millisecs = parse_data_lst[1]
                gps_sec = gps_time(gps_week, gps_millisecs)
                gps_millisecs_lst.append(gps_sec)
        self.uut.stop_listen_data()

        for i in range(len(gps_millisecs_lst)):
            if i + 1 < len(gps_millisecs_lst):
                interval = gps_millisecs_lst[i+1] - gps_millisecs_lst[i]
            else:
                break
            if interval >= 9 or interval <= 11:
                result = True
            else:
                result = False
                break
        
        if result == True:
            return result, f'{interval}', f'~10.0'
        else:
            return result, f'{interval}', f'~10.0'

    def output_packet_diagnostic_message_test(self):
        result = False
        interval = None
        logf_name = f'./data/Packet_ODR_test_data/{self.product_sn}_{self.test_time}/diagnostic_message.bin'
        self.test_log.creat_binf_sct2(file_name=logf_name, sn_num=self.product_sn, test_time=self.test_time)
 
        gps_millisecs_lst = []
        self.uut.start_listen_data(0x050a)
        start_time = time.time()
        self.uut.reset_buffer()
        while time.time() - start_time <= 120:
            data = self.uut.read_data()
            if data is not None:
                self.test_log.write2bin(data)
                parse_data = data[8:8+22]
                fmt = '<HIIfff'
                parse_data_lst = struct.unpack(fmt, parse_data)
                gps_week = parse_data_lst[0]
                gps_millisecs = parse_data_lst[1]
                gps_sec = gps_time(gps_week, gps_millisecs)
                gps_millisecs_lst.append(gps_sec)
        self.uut.stop_listen_data()

        for i in range(len(gps_millisecs_lst)):
            if i + 1 < len(gps_millisecs_lst):
                interval = gps_millisecs_lst[i+1] - gps_millisecs_lst[i]
            else:
                break
            if interval >= 999 or interval <= 1001:
                result = True
            else:
                result = False
                break
        
        if result == True:
            return result, f'{interval}', f'~1000.0'
        else:
            return result, f'{interval}', f'~1000.0'

    def output_packet_raw_imu_data_test(self):
        result = False
        interval = None
        logf_name = f'./data/Packet_ODR_test_data/{self.product_sn}_{self.test_time}/raw_imu.bin'
        self.test_log.creat_binf_sct2(file_name=logf_name, sn_num=self.product_sn, test_time=self.test_time)
 
        gps_millisecs_lst = []
        self.uut.start_listen_data(0x010a)
        start_time = time.time()
        self.uut.reset_buffer()
        while time.time() - start_time <= 120:
            data = self.uut.read_data()
            if data is not None:
                self.test_log.write2bin(data)
                parse_data = data[8:8+30]
                fmt = '<HIffffff'
                parse_data_lst = struct.unpack(fmt, parse_data)
                gps_week = parse_data_lst[0]
                gps_millisecs = parse_data_lst[1]
                gps_sec = gps_time(gps_week, gps_millisecs)
                gps_millisecs_lst.append(gps_sec)
        self.uut.stop_listen_data()

        for i in range(len(gps_millisecs_lst)):
            if i + 1 < len(gps_millisecs_lst):
                interval = gps_millisecs_lst[i+1] - gps_millisecs_lst[i]
            else:
                break
            if interval >= 9 or interval <= 11:
                result = True
            else:
                result = False
                break
        
        if result == True:
            return result, f'{interval}', f'~10.0'
        else:
            return result, f'{interval}', f'~10.0'

    ### section3 ID setting verification without repower ###

    def parameters_set_with_reset(self, field_id):
        set_command = INPUT_PACKETS[2]
        save_command = INPUT_PACKETS[3]
        get_command = INPUT_PACKETS[1]
        reset_command = INPUT_PACKETS[5]
        except_list = []
        actual_list = []
        result = False
        true_times = 0

        save_message_bytes = []
        reset_message_bytes = []
        
        for i in range(3):
            # Set message bytes
            set_message_bytes = []
            field_id_bytes = struct.pack('<I', (field_id+i))
            set_message_bytes.extend(field_id_bytes)

            if (field_id >= 0) and (field_id <= 12):
                params = round(random.uniform(-180, 180), 1)
                except_list.append(params)
                field_value_bytes = struct.pack('<f', params)
                set_message_bytes.extend(field_value_bytes)

            # Get message bytes
            get_message_bytes = []
            field_id_bytes = struct.pack('<I', (field_id+i))
            get_message_bytes.extend(field_id_bytes)

            self.uut.send_message(set_command, set_message_bytes)
            time.sleep(0.5)
            self.uut.send_message(save_command, save_message_bytes)
            self.uut.send_message(reset_command, reset_message_bytes)
            self.uut.reset_dev()
            time.sleep(30)
            self.uut.find_device(times=0)
            get_response = self.uut.write_read_response(get_command, get_message_bytes, 0.1)
            get_params = float('%.2f' % (struct.unpack('<f', get_response[2][4:]))[0])
            actual_list.append(get_params)
            if get_params == params:
                result = True
                true_times += 1
            else:
                result = False

        if(result):
            print(f'True times: {true_times}')
            return True, f'{except_list}', f'{actual_list}'
        else:
            return False, f'{except_list}', f'{actual_list}'

    ### section4 ID settiong verification with reset ###

    def set_parameters_verify(self, field_id, val):
        set_command = INPUT_PACKETS[2]
        get_command = INPUT_PACKETS[1]
        result = False
        
        # Set message bytes 
        set_message_bytes = []
        field_id_bytes = struct.pack('<I', (field_id))
        set_message_bytes.extend(field_id_bytes)

        if (field_id >= 0) and (field_id <= 12):
            field_value_bytes = struct.pack('<f', val)
            set_message_bytes.extend(field_value_bytes)

        # Get message bytes
        get_message_bytes = []
        field_id_bytes = struct.pack('<I', (field_id))
        get_message_bytes.extend(field_id_bytes)

        # self.uut.send_message(reset_command, reset_message_bytes)
        # time.sleep(0.5)
        self.uut.send_message(set_command, set_message_bytes)
        time.sleep(0.5)
        get_response = self.uut.write_read_response(get_command, get_message_bytes, 0.1)
        get_params = float('%.2f' % (struct.unpack('<f', get_response[2][4:]))[0])
        if get_params == val:
            result = True
        else:
            result = False

        if result == True:
            return True, f'{val}', f'{get_params}'
        else:
            return False, f'{val}', f'{get_params}'

    ### section5 Long term test function

    def long_term_test(self):
        result = True
        command = INPUT_PACKETS[0]
        message_bytes = []
        
        # long term count manual setting
        result = self.uut.async_write_read(command, message_bytes, self.properties["long term test"]["LONGTERM_RUNNING_COUNT"])       
        if(result):
            return True, 'Non zero packets', 'Non zero packets'
        else:
            return False, 'Non zero packets', 'Non zero packets'

    def long_term_test_setup(self):
        longterm_run_time = self.properties["long term test"]["LONGTERM_RUNNING_TIME"]
        filter_type = self.properties["long term test"]["TypeFilter"]
        logf_name = f'./data/Packet_long_term_test_data/long_terms_data_{self.test_time}.bin' 
        # logf_name = f'./data/Packet_long_term_test_data/long_terms_data_{self.test_time}.pcap' 
        self.test_log.cerat_binf_sct5(logf_name)
        start_time = time.time()
        self.uut.start_listen_data(filter_type)
        self.uut.reset_buffer()    
        self.tlock.acquire()    
        while time.time() - start_time <= longterm_run_time:
            data = self.uut.read_data()
            self.test_log.write2bin(data)
            # self.test_log.write2pcap(data, logf_name)
        self.tlock.release()
        self.uut.stop_listen_data()
        if self.uut.check_len() != 0:
            while True:
                data = self.uut.read_data()
                self.test_log.write2bin(data)
                if self.uut.check_len() == 0:
                    break
        return True, '', ''          

    def gnss_solution_gps_time_jump_test(self):
        logf_name = f'./data/Packet_long_term_test_data/long_terms_data_{self.test_time}.bin'
        gps_time_of_week_lst = []
        result = True

        if not os.path.exists(logf_name):
            self.long_term_test_setup()
            logf = open(logf_name, 'rb')
        else:
            logf = open(logf_name, 'rb')
        log_data = logf.read()
        gnss_packet_type = [0x55, 0x55, 0x02, 0x0a]
        for i in range(len(log_data)):
            data = log_data[i:i+87]
            packet_start_flag = data.find(bytes(gnss_packet_type))
            if packet_start_flag == 0:
                payload = data[8:-2]
                fmt = '<HIBdddfffBBffffffff'
                gps_time_of_week = struct.unpack(fmt, payload)[1]
                gps_time_of_week_lst.append(gps_time_of_week)

        for i in range(len(gps_time_of_week_lst)-1):
            time_interval = gps_time_of_week_lst[i+1] - gps_time_of_week_lst[i]
            if time_interval != 1000:
                error_pos = i
                result = False
                break
        
        if len(gps_time_of_week_lst) == 0:
            result = False
            error_pos = None
        
        if result == True:
            return True, 'No time jump', 'No time jump'
        elif result == False and error_pos == None:
            return False, 'No gnss single', 'No time jump'
        else:
            return False, f'No.{error_pos} packet time jump', 'No time jump'

    def ins_solution_gps_time_jump_test(self):
        logf_name = f'./data/Packet_long_term_test_data/long_terms_data_{self.test_time}.bin'
        gps_time_of_week_lst = []
        result = True

        if not os.path.exists(logf_name):
            self.long_term_test_setup()
            logf = open(logf_name, 'rb')
        else:
            logf = open(logf_name, 'rb')

        log_data = logf.read()
        ins_packet_type = [0x55, 0x55, 0x03, 0x0a]
        for i in range(len(log_data)):
            data = log_data[i:i+120]
            packet_start_flag = data.find(bytes(ins_packet_type))
            if packet_start_flag == 0:
                payload = data[8:-2]
                fmt = '<HIBBdddfffffffffffffffffffH'
                gps_time_of_week = struct.unpack(fmt, payload)[1]
                gps_time_of_week_lst.append(gps_time_of_week)
        for i in range(len(gps_time_of_week_lst)-1):
            time_interval = gps_time_of_week_lst[i+1] - gps_time_of_week_lst[i]
            if time_interval != 10:
                error_pos = i
                result = False
                break
        
        if len(gps_time_of_week_lst) == 0:
            result = False
            error_pos = None
        
        if result == True:
            return True, 'No time jump', 'No time jump'
        elif result == False and error_pos == None:
            return False, 'No gnss single', 'No time jump'
        else:
            return False, f'No.{error_pos} packet time jump', 'No time jump'

    def dm_solution_gps_time_jump_test(self):
        logf_name = f'./data/Packet_long_term_test_data/long_terms_data_{self.test_time}.bin'
        gps_time_of_week_lst = []
        result = True

        if not os.path.exists(logf_name):
            self.long_term_test_setup()
            logf = open(logf_name, 'rb')
        else:
            logf = open(logf_name, 'rb')

        log_data = logf.read()
        ins_packet_type = [0x55, 0x55, 0x05, 0x0a]
        for i in range(len(log_data)):
            data = log_data[i:i+32]
            packet_start_flag = data.find(bytes(ins_packet_type))
            if packet_start_flag == 0:
                payload = data[8:-2]
                fmt = '<HIIfff'
                gps_time_of_week = struct.unpack(fmt, payload)[1]
                gps_time_of_week_lst.append(gps_time_of_week)
        for i in range(len(gps_time_of_week_lst)-1):
            time_interval = gps_time_of_week_lst[i+1] - gps_time_of_week_lst[i]
            if time_interval != 1000:
                error_pos = i
                result = False
                break

        if len(gps_time_of_week_lst) == 0:
            result = False
            error_pos = None
        
        if result == True:
            return True, 'No time jump', 'No time jump'
        elif result == False and error_pos == None:
            return False, 'No gnss single', 'No time jump'
        else:
            return False, f'No.{error_pos} packet time jump', 'No time jump'

    def imu_solution_gps_time_jump_test(self):
        logf_name = f'./data/Packet_long_term_test_data/long_terms_data_{self.test_time}.bin'
        gps_time_of_week_lst = []
        result = True

        if not os.path.exists(logf_name):
            self.long_term_test_setup()
            logf = open(logf_name, 'rb')
        else:
            logf = open(logf_name, 'rb')

        log_data = logf.read()
        ins_packet_type = [0x55, 0x55, 0x01, 0x0a]
        for i in range(len(log_data)):
            data = log_data[i:i+40]
            packet_start_flag = data.find(bytes(ins_packet_type))
            if packet_start_flag == 0:
                payload = data[8:-2]
                fmt = '<HIffffff'
                gps_time_of_week = struct.unpack(fmt, payload)[1]
                gps_time_of_week_lst.append(gps_time_of_week)
        for i in range(len(gps_time_of_week_lst)-1):
            time_interval = gps_time_of_week_lst[i+1] - gps_time_of_week_lst[i]
            if time_interval != 10:
                error_pos = i
                result = False
                break
        
        if len(gps_time_of_week_lst) == 0:
            result = False
            error_pos = None
        
        if result == True:
            return True, 'No time jump', 'No time jump'
        elif result == False and error_pos == None:
            return False, 'No gnss single', 'No time jump'
        else:
            return False, f'No.{error_pos} packet time jump', 'No time jump'

    def parameters_set_loop(self, field_id, val):
        set_command = INPUT_PACKETS[2]
        save_command = INPUT_PACKETS[3]
        get_command = INPUT_PACKETS[1]
        turns = 50
        failed_times = 0

        save_message_bytes = []
        
        for x in trange(turns):
            for i in range(3):
                # Set message bytes
                set_message_bytes = []
                field_id_bytes = struct.pack('<I', (field_id+i))
                set_message_bytes.extend(field_id_bytes)

                if (field_id >= 0) and (field_id <= 12) and x % 2 == 1:
                    field_value_bytes = struct.pack('<f', val[0])
                    set_message_bytes.extend(field_value_bytes)
                elif (field_id >= 0) and (field_id <= 12) and x % 2 == 0:
                    field_value_bytes = struct.pack('<f', val[1])
                    set_message_bytes.extend(field_value_bytes)

                # Get message bytes
                get_message_bytes = []
                field_id_bytes = struct.pack('<I', (field_id+i))
                get_message_bytes.extend(field_id_bytes)

                # Test progress
                self.uut.send_message(set_command, set_message_bytes)
                time.sleep(0.5)
                self.uut.send_message(save_command, save_message_bytes)
                get_response = self.uut.write_read_response(get_command, get_message_bytes, 0.1)
                get_params = float('%.2f' % (struct.unpack('<f', get_response[2][4:]))[0])
                if x % 2 == 1: 
                    if get_params == val[0]:
                        pass
                    else:
                        failed_times += 1
                        print(f'turn{x} paramId{field_id+i}: Expected:{val}, Actual:{get_params}')
                elif x % 2 == 0:
                    if get_params == val[1]:
                        pass
                    else:
                        failed_times += 1
                        print(f'turn{x} paramId{field_id+i}: Expected:{val}, Actual:{get_params}')

        if failed_times == 0:
            return True, "Failed times 0", f"Failed times {failed_times}"
        else:
            return False, "Failed times 0", f"Failed times {failed_times}"

    ### section6 Vehicle code function test

    def vehicle_code_setting_test(self, field_id, val):
        set_command = INPUT_PACKETS[2]
        
        # Set message bytes 
        set_message_bytes = []
        field_id_bytes = struct.pack('<I', (field_id))
        set_message_bytes.extend(field_id_bytes)

        if (field_id >= 0) and (field_id <= 14):
            set_message_bytes.extend(bytes(val))

        set_response = self.uut.write_read_response(set_command, set_message_bytes, 0.1)[2]
        set_response_val = struct.unpack('<I', set_response)[0]

        if set_response_val == 0:
            result = True
        else:
            result = False

        if(result):
            return True, f'{0}', f'{set_response_val}'
        else:
            return False, f'{0}', f'{set_response_val}'

    def vehicle_code_status_test(self, field_id, val):
        set_command = INPUT_PACKETS[2]
        
        # Set message bytes 
        set_message_bytes = []
        field_id_bytes = struct.pack('<I', (field_id))
        set_message_bytes.extend(field_id_bytes)

        if (field_id >= 0) and (field_id <= 14):
            set_message_bytes.extend(bytes(val))
        self.uut.send_message(set_command, set_message_bytes)

        check_command = INPUT_PACKETS[8]
        check_message_bytes = []
        check_response = self.uut.write_read_response(check_command, check_message_bytes, 0.1)[2]

        error_lst = []
        if check_response[0] != 1:
            error_lst.append(check_response[0])
        elif check_response[1] != 1:
            error_lst.append(check_response[1])
        elif check_response[4:8] != bytes(val):
            error_lst.append(check_response[4:8])

        if len(error_lst) == 0:
            result = True
        else:
            result = False

        if(result):
            return True, f'{[]}', f'{error_lst}'
        else:
            return False, f'{[]}', f'{error_lst}'

    def vehicle_code_params_test(self, field_id, val):
        set_command = INPUT_PACKETS[2]
        
        # Set message bytes 
        set_message_bytes = []
        field_id_bytes = struct.pack('<I', (field_id))
        set_message_bytes.extend(field_id_bytes)

        if (field_id >= 0) and (field_id <= 14):
            set_message_bytes.extend(bytes(val))
        self.uut.send_message(set_command, set_message_bytes)

        check_command = INPUT_PACKETS[8]
        check_message_bytes = []
        check_response = self.uut.write_read_response(check_command, check_message_bytes, 0.1)[2]

        params_lst = []
        params_buffer = check_response[8:56]
        for i in range(int(len(params_buffer)/4)):
            params_bytes = params_buffer[i*4:i*4+4]
            params = struct.unpack('<f', params_bytes)[0]
            params = round(params, 6)
            params_lst.append(params)

        if bytes(val) == b'VF33':
            except_params_lst = self.properties["vehicle code"]["vcode params"]["VF33"]
        if bytes(val) == b'VF34':
            except_params_lst = self.properties["vehicle code"]["vcode params"]["VF34"]
        if bytes(val) == b'VF35':
            except_params_lst = self.properties["vehicle code"]["vcode params"]["VF35"]
        if bytes(val) == b'VF36':
            except_params_lst = self.properties["vehicle code"]["vcode params"]["VF36"]

        if params_lst == except_params_lst:
            result = True
        else:
            result = False

        if(result):
            return True, f'{except_params_lst}', f'{params_lst}'
        else:
            return False, f'{except_params_lst}', f'{params_lst}'

    def vehicle_table_version_test(self, except_ver):
        cmd = INPUT_PACKETS[8]
        message_bytes = []

        check_response = self.uut.write_read_response(cmd, message_bytes, 0.1)[2]
        vcode_ver_payload = check_response[2:4]
        vcode_ver = struct.unpack('<h', vcode_ver_payload)[0]

        if vcode_ver == except_ver:
            return True, f'vehicle table version: {except_ver}', f'vehicle table version: {vcode_ver}'
        else:
            return False, f'vehicle table version: {except_ver}', f'vehicle table version: {vcode_ver}'

    def GNSS_packet_reasonable_check_week(self):
        result = False
        logf_name = f'./data/Packet_ODR_test_data/{self.uut.serial_number}_{self.test_time}/GNSS_packet_week.bin'
        self.test_log.creat_binf_sct2(file_name=logf_name, sn_num=self.uut.serial_number, test_time=self.test_time)
 
        gps_week_list = []
        gps_ms_list = []
        gps_secs_lst = []
        real_time_list = []
        unmatch_time_count = 0
        gps_signal_loss = 0
        self.uut.start_listen_data(0x020a)
        start_time = time.time()
        self.uut.reset_buffer()
        while time.time() - start_time <= 10:
            data = self.uut.read_data()
            if data is not None:
                real_time = get_curr_time()
                self.test_log.write2bin(data)
                parse_data = data[8:8+77]
                fmt = '<HIBdddfffBBffffffff'
                parse_data_lst = struct.unpack(fmt, parse_data)
                gps_week_list.append(parse_data_lst[0])
                gps_ms_list.append(parse_data_lst[1])
                real_time_list.append(real_time)
        self.uut.stop_listen_data()
        
        for i in range(len(gps_week_list)):
            if gps_week_list[i] < 2232:
                gps_signal_loss = gps_signal_loss +1
            else:
                gps_sec = gps_time(gps_week_list[i], gps_ms_list[i]/1000)
                gps_secs_lst.append(gps_sec)
                time_diff = cal_time_diff(gps_secs_lst[i], real_time_list[i])
                print(f'real time - gps time = {time_diff}')
                if time_diff > 1 or time_diff < -1:
                    unmatch_time_count = unmatch_time_count + 1

        if len(gps_week_list) == 0:
            return False, f'no GNSS packets', 'could capture GNSS packets'
        else:
            if unmatch_time_count == 0 and gps_signal_loss != len(gps_week_list):
                return True, f'number of unmatch real time = {unmatch_time_count}, packets have GNSS time = {len(gps_week_list)-gps_signal_loss}', 'match real time <1s'
            elif unmatch_time_count == 0 and gps_signal_loss == len(gps_week_list):
                return False, f'packets have GNSS time = {len(gps_week_list)-gps_signal_loss}, GNSS packets = {len(gps_week_list)} ', 'at last one GNSS packet has GPS time'
            else:
                return False, f'number of unmatch real time = {unmatch_time_count}, no GNSS singal = {gps_signal_loss}', 'match real time, <1s'

    def GNSS_packet_reasonable_check_time_ms(self):
        result = False
        interval = None
        logf_name = f'./data/Packet_ODR_test_data/{self.uut.serial_number}_{self.test_time}/GNSS_packet_time_ms.bin'
        self.test_log.creat_binf_sct2(file_name=logf_name, sn_num=self.uut.serial_number, test_time=self.test_time)
 
        gps_week_list = []
        gps_ms_list = []
        gps_millisecs_lst = []
        gps_signal_loss = 0
        num_interval_err = 0
        neighbor_gps_pair = 0
        self.uut.start_listen_data(0x020a)
        start_time = time.time()
        self.uut.reset_buffer()
        while time.time() - start_time <= 10:
            data = self.uut.read_data()
            if data is not None:
                self.test_log.write2bin(data)
                parse_data = data[8:8+77]
                fmt = '<HIBdddfffBBffffffff'
                parse_data_lst = struct.unpack(fmt, parse_data)
                gps_week_list.append(parse_data_lst[0])
                gps_ms_list.append(parse_data_lst[1])
        self.uut.stop_listen_data()

        if len(gps_week_list) >= 2:
            for i in range(len(gps_week_list)):
                if i + 1 < len(gps_week_list):
                    if gps_week_list[i] >= 2232:
                        if gps_week_list[i+1] >=2232:
                            time_interval = gps_ms_list[i+1] - gps_ms_list[i]
                            neighbor_gps_pair = neighbor_gps_pair +1
                            if time_interval == 1000:
                                continue
                            else:
                                num_interval_err = num_interval_err +1
                    else:
                        gps_signal_loss = gps_signal_loss + 1    
            if gps_week_list[-1] < 2232:
                gps_signal_loss = gps_signal_loss + 1

        if len(gps_week_list) == 0:
            return False, f'no GNSS packets', 'could capture GNSS packets'
        elif len(gps_week_list) < 2:
            return False, f'GNSS packets = {len(gps_week_list)} ', 'at last need two neighbor DM packets have GPS time'
        elif len(gps_week_list) >=2 and neighbor_gps_pair <1:
            return False, f'GNSS packets = {len(gps_week_list)}, packets have gps time = {len(gps_week_list)-gps_signal_loss}, neighbor gps pairs = {neighbor_gps_pair} ', 'at last one pair neighbor DM packets has gps signal'
        else:
            return True, f'GNSS packets = {len(gps_week_list)}, packets have gps time = {len(gps_week_list)-gps_signal_loss}, neighbor gps pair = {neighbor_gps_pair} ', 'interval = 1000ms'

    def DM_packet_reasonable_check_week(self):
        result = False
        logf_name = f'./data/Packet_ODR_test_data/{self.uut.serial_number}_{self.test_time}/DM_packet_week.bin'
        self.test_log.creat_binf_sct2(file_name=logf_name, sn_num=self.uut.serial_number, test_time=self.test_time)
 
        gps_week_list = []
        gps_ms_list = []
        gps_secs_lst = []
        real_time_list = []
        unmatch_time_count = 0
        gps_signal_loss = 0
        self.uut.start_listen_data(0x050a)
        start_time = time.time()
        self.uut.reset_buffer()
        while time.time() - start_time <= 10:
            data = self.uut.read_data()
            if data is not None:
                real_time = get_curr_time()
                self.test_log.write2bin(data)
                parse_data = data[8:8+22]
                fmt = '<HIIfff'
                parse_data_lst = struct.unpack(fmt, parse_data)
                gps_week_list.append(parse_data_lst[0])
                gps_ms_list.append(parse_data_lst[1])
                real_time_list.append(real_time)
        self.uut.stop_listen_data()
        
        for i in range(len(gps_week_list)):
            if gps_week_list[i] < 2232:
                gps_signal_loss = gps_signal_loss +1
            else:
                gps_sec = gps_time(gps_week_list[i], gps_ms_list[i]/1000)
                gps_secs_lst.append(gps_sec)
                time_diff = cal_time_diff(gps_secs_lst[i], real_time_list[i])
                print(f'real time - gps time = {time_diff}')
                if time_diff > 1 or time_diff < -1:
                    unmatch_time_count = unmatch_time_count + 1

        if len(gps_week_list) == 0:
            return False, f'no DM packets', 'could capture DM packets'
        else:
            if unmatch_time_count == 0 and gps_signal_loss != len(gps_week_list):
                return True, f'number of unmatch real time = {unmatch_time_count}, packets have gps time = {len(gps_week_list)-gps_signal_loss}', 'match real time <1s'
            elif unmatch_time_count == 0 and gps_signal_loss == len(gps_week_list):
                return False, f'packets have gps time = {len(gps_week_list)-gps_signal_loss}, DM packets = {len(gps_week_list)} ', 'at last one DM packet has GPS time'
            else:
                return False, f'number of unmatch real time = {unmatch_time_count}, no gps singal = {gps_signal_loss}', 'match real time, <1s'

    def DM_packet_reasonable_check_time_ms(self):
        result = False
        interval = None
        logf_name = f'./data/Packet_ODR_test_data/{self.uut.serial_number}_{self.test_time}/DM_packet_time_ms.bin'
        self.test_log.creat_binf_sct2(file_name=logf_name, sn_num=self.uut.serial_number, test_time=self.test_time)
 
        gps_week_list = []
        gps_ms_list = []
        gps_millisecs_lst = []
        gps_signal_loss = 0
        num_interval_err = 0
        neighbor_gps_pair = 0
        self.uut.start_listen_data(0x050a)
        start_time = time.time()
        self.uut.reset_buffer()
        while time.time() - start_time <= 10:
            data = self.uut.read_data()
            if data is not None:
                self.test_log.write2bin(data)
                parse_data = data[8:8+22]
                fmt = '<HIIfff'
                parse_data_lst = struct.unpack(fmt, parse_data)
                gps_week_list.append(parse_data_lst[0])
                gps_ms_list.append(parse_data_lst[1])
        self.uut.stop_listen_data()

        if len(gps_week_list) >= 2:
            for i in range(len(gps_week_list)):
                if i + 1 < len(gps_week_list):
                    if gps_week_list[i] >= 2232:
                        if gps_week_list[i+1] >=2232:
                            time_interval = gps_ms_list[i+1] - gps_ms_list[i]
                            neighbor_gps_pair = neighbor_gps_pair +1
                            if time_interval == 1000:
                                continue
                            else:
                                num_interval_err = num_interval_err +1
                    else:
                        gps_signal_loss = gps_signal_loss + 1    
            if gps_week_list[-1] < 2232:
                gps_signal_loss = gps_signal_loss + 1

        if len(gps_week_list) == 0:
            return False, f'no DM packets', 'could capture DM packets'
        elif len(gps_week_list) < 2:
            return False, f'DM packets = {len(gps_week_list)} ', 'at last need two neighbor DM packets have GPS time'
        elif len(gps_week_list) >=2 and neighbor_gps_pair <1:
            return False, f'DM packets = {len(gps_week_list)}, packets have gps time = {len(gps_week_list)-gps_signal_loss}, neighbor gps pairs = {neighbor_gps_pair} ', 'at last one pair neighbor DM packets has gps signal'
        else:
            return True, f'DM packets = {len(gps_week_list)}, packets have gps time = {len(gps_week_list)-gps_signal_loss}, neighbor gps pair = {neighbor_gps_pair} ', 'interval = 1000ms'

    def DM_packet_reasonable_check_temp(self):
        #result = False
        logf_name = f'./data/Packet_ODR_test_data/{self.uut.serial_number}_{self.test_time}/DM_packet_check_temp.bin'
        self.test_log.creat_binf_sct2(file_name=logf_name, sn_num=self.uut.serial_number, test_time=self.test_time)
 
        temp_list = []
        self.uut.start_listen_data(0x050a)
        start_time = time.time()
        self.uut.reset_buffer()
        while time.time() - start_time <= 10:
            data = self.uut.read_data()
            if data is not None:
                self.test_log.write2bin(data)
                parse_data = data[8:8+22]
                fmt = '<HIIfff'
                parse_data_lst = struct.unpack(fmt, parse_data)
                gps_millisecs = parse_data_lst[1]
                IMU_temp = parse_data_lst[3]
                MCU_temp = parse_data_lst[4]
                GNSS_chip_temp = parse_data_lst[5]
                print(f'IMU = {IMU_temp}, MCU = {MCU_temp}, GNSS = {GNSS_chip_temp}')
                temp_list.append([IMU_temp,MCU_temp,GNSS_chip_temp])
        self.uut.stop_listen_data()
        if len(temp_list) == 0:
            print('no DM packets!')

        imu_out = 0
        mcu_out = 0
        gnss_out = 0
        for i in range(len(temp_list)):
            if temp_list[i][0] < 85 and temp_list[i][0] > 40:
                if temp_list[i][1] < 85 and temp_list[i][1] > 40:
                    if temp_list[i][2] < 85 and temp_list[i][2] > 40:
                        continue
                    else:
                        gnss_out = gnss_out +1
                else:
                    mcu_out = mcu_out +1
            else:
                imu_out = imu_out +1
        
        if len(temp_list) == 0:
            return False, 'no DM packets', 'could capture DM packets'
        else:
            if imu_out + mcu_out + gnss_out == 0:
                return True, 'Temperature of IMU/MCU/GNSS chip is in reasonable range', '-40 < temp <85'
            else:
                return False, f'amount out of temp range: IMU={imu_out},MCU={mcu_out},GNSS={gnss_out}', '-40 < temp <85'

    def DM_packet_reasonable_check_status_gnss(self):
        result = False
        interval = None
        logf_name = f'./data/Packet_ODR_test_data/{self.uut.serial_number}_{self.test_time}/DM_packet_check_status_gnss.bin'
        self.test_log.creat_binf_sct2(file_name=logf_name, sn_num=self.uut.serial_number, test_time=self.test_time)
 
        pps_list = []
        gnss_data_list = []
        gnss_signal_list = []
        self.uut.start_listen_data(0x050a)
        start_time = time.time()
        self.uut.reset_buffer()
        while time.time() - start_time <= 10:
            data = self.uut.read_data()
            if data is not None:
                self.test_log.write2bin(data)
                parse_data = data[8:8+22]
                fmt = '<HIIfff'
                parse_data_lst = struct.unpack(fmt, parse_data)
                status_bit = parse_data_lst[2]
                dev_status_bin = "{0:{fill}32b}".format(status_bit, fill='0')
                #PPS status = bit10, 31-10=21
                #GNSS data status = bit11
                #GNSS signal status = bit12
                pps_list.append(dev_status_bin[21])
                if pps_list[-1] == '1':
                    print('1PPS pulse exception ', end=' || ')
                elif pps_list[-1] == '0':
                    print('PPS normal ', end=' || ')
                gnss_data_list.append(dev_status_bin[20])
                if gnss_data_list[-1] == '1':
                    print('GNSS chipset has NO data output', end=' || ')
                elif gnss_data_list[-1] == '0':
                    print('GNSS data normal', end=' || ')
                gnss_signal_list.append(dev_status_bin[19])
                if gnss_signal_list[-1] == '1':
                    print(' GNSS chipset has data output, but no valid signal detected')
                elif gnss_signal_list[-1] == '0':
                    print('GNSS signal normal')
        self.uut.stop_listen_data()
        if len(pps_list) == 0:
            print('no DM packets!')

        pps_err_count = pps_list.count('1')
        gnss_data_err_count = gnss_data_list.count('1')
        gnss_signal_err_count = gnss_signal_list.count('1')
        
        if len(pps_list) == 0:
            return False, 'no DM packets', 'could capture DM packets'
        else:
            if pps_err_count > 0 or gnss_data_err_count or gnss_signal_err_count >0:
                return False, f'GNSS status error count: PPS error={pps_err_count} gnss data={gnss_data_err_count} gnss signal={gnss_signal_err_count}', 'pps status is always 0'
            else:
                return True, 'GNSS status PPS / GNSS data / GNSS signal is always 0', 'GNSS status is always 0'

    def DM_packet_reasonable_check_status_imu(self):
        result = False
        interval = None
        logf_name = f'./data/Packet_ODR_test_data/{self.uut.serial_number}_{self.test_time}/DM_packet_check_status_imu.bin'
        self.test_log.creat_binf_sct2(file_name=logf_name, sn_num=self.uut.serial_number, test_time=self.test_time)
 
        master_fail_list = []
        hw_err_list = []
        sw_err_list = []
        config_err_list = []
        cali_err_list = []
        accel_deg_err_list = []
        gyro_deg_err_list = []
        forced_restart_list = [] 
        crc_err_list = []
        tx_overflow_err_list = []
        self.uut.start_listen_data(0x050a)
        start_time = time.time()
        self.uut.reset_buffer()
        while time.time() - start_time <= 10:
            data = self.uut.read_data()
            if data is not None:
                self.test_log.write2bin(data)
                parse_data = data[8:8+22]
                fmt = '<HIIfff'
                parse_data_lst = struct.unpack(fmt, parse_data)
                imu_status_bit = parse_data_lst[2]
                dev_status_bin = "{0:{fill}32b}".format(imu_status_bit, fill='0')
                #Master status = bit0, 31-0=31
                master_fail_list.append(dev_status_bin[31])
                hw_err_list.append(dev_status_bin[30])
                sw_err_list.append(dev_status_bin[29])
                config_err_list.append(dev_status_bin[28])
                cali_err_list.append(dev_status_bin[27])
                accel_deg_err_list.append(dev_status_bin[26])
                gyro_deg_err_list.append(dev_status_bin[25])
                forced_restart_list.append(dev_status_bin[24])
                if forced_restart_list[-1] == '1':
                    print('forced restart = 1')
                elif forced_restart_list[-1] == '0':
                    print('forced restart = 0 normal')
                crc_err_list.append(dev_status_bin[23])
                tx_overflow_err_list.append(dev_status_bin[22])
        self.uut.stop_listen_data()
        if len(master_fail_list) == 0:
            print('no DM packets!')

        master_fail_count = master_fail_list.count('1')
        hw_err_count = hw_err_list.count('1')
        sw_err_count = sw_err_list.count('1')
        config_err_count = config_err_list.count('1')
        cali_err_count = cali_err_list.count('1')
        accel_deg_err_count = accel_deg_err_list.count('1')
        gyro_deg_err_count = gyro_deg_err_list.count('1')
        forced_restart_count = forced_restart_list.count('1')
        crc_err_count = crc_err_list.count('1')
        tx_overflow_err_count = tx_overflow_err_list.count('1')
        
        count_total = master_fail_count + hw_err_count + sw_err_count + config_err_count + cali_err_count + \
            accel_deg_err_count + gyro_deg_err_count + forced_restart_count + crc_err_count + tx_overflow_err_count

        if len(master_fail_list) == 0:
            return False, 'no DM packets', 'could capture DM packets'
        else:
            if count_total > 0:
                return False, f'IMU status error! Master fail={master_fail_count},HW error={hw_err_count}\
,SW error={sw_err_count},Config error={config_err_count},Calibrarion error={cali_err_count}\
,Accel degradation={accel_deg_err_count},Gyro degradation ={gyro_deg_err_count}\
,Forced restart={forced_restart_count},CRC error={crc_err_count}\
,Tx overflow error={tx_overflow_err_count}', 'IMU status is always 0'
            else:
                return True, 'IMU status is always 0', 'IMU status is always 0'

    def DM_packet_reasonable_check_status_operation(self):
        result = False
        interval = None
        logf_name = f'./data/Packet_ODR_test_data/{self.uut.serial_number}_{self.test_time}/DM_packet_check_status_operation.bin'
        self.test_log.creat_binf_sct2(file_name=logf_name, sn_num=self.uut.serial_number, test_time=self.test_time)
 
        power_list = []
        mcu_list = []
        temp_u_mcu_list = []
        temp_u_sta_list = []
        temp_u_imu_list = []
        temp_o_mcu_list = []
        temp_o_sta_list = []
        temp_o_imu_list = []
        self.uut.start_listen_data(0x050a)
        start_time = time.time()
        self.uut.reset_buffer()
        while time.time() - start_time <= 10:
            data = self.uut.read_data()
            if data is not None:
                self.test_log.write2bin(data)
                parse_data = data[8:8+22]
                fmt = '<HIIfff'
                parse_data_lst = struct.unpack(fmt, parse_data)
                imu_status_bit = parse_data_lst[2]
                dev_status_bin = "{0:{fill}32b}".format(imu_status_bit, fill='0')
                #Power status = bit13, 31-13=18
                power_list.append(dev_status_bin[18])
                mcu_list.append(dev_status_bin[17])
                temp_u_mcu_list.append(dev_status_bin[16])
                temp_u_sta_list.append(dev_status_bin[15])
                temp_u_imu_list.append(dev_status_bin[14])
                temp_o_mcu_list.append(dev_status_bin[13])
                temp_o_sta_list.append(dev_status_bin[12])
                temp_o_imu_list.append(dev_status_bin[11])
        self.uut.stop_listen_data()
        if len(power_list) == 0:
            print('no DM packets!')

        power_count = power_list.count('1')
        mcu_count = mcu_list.count('1')
        temp_u_mcu_count = temp_u_mcu_list.count('1')
        temp_u_sta_count = temp_u_sta_list.count('1')
        temp_u_imu_count = temp_u_imu_list.count('1')
        temp_o_mcu_count = temp_o_mcu_list.count('1')
        temp_o_sta_count = temp_o_sta_list.count('1')
        temp_o_imu_count = temp_o_imu_list.count('1')
        
        count_total = power_count + mcu_count + temp_u_mcu_count + temp_u_mcu_count + temp_u_sta_count \
            + temp_u_imu_count + temp_o_mcu_count + temp_o_sta_count + temp_o_imu_count

        if len(power_list) == 0:
            return False, 'no DM packets', 'could capture DM packets'
        else:
            if count_total > 0:
                return False, f'Operation status error! Power fail={power_count},mcu error={mcu_count}\
,Temperature under MCU flag={temp_u_mcu_count},Temperature under STA flag={temp_u_sta_count},Temperature under IMU flag={temp_u_imu_count}\
,Temperature over MCU flag={temp_o_mcu_count},Temperature over STA flag ={temp_o_sta_count}\
,Temperature over IMU flag={temp_o_imu_count}'
            else:
                return True, 'IMU status is always 0', 'IMU status is always 0'

    def IMU_data_packet_reasonable_check_week(self):
        result = False
        interval = None
        logf_name = f'./data/Packet_ODR_test_data/{self.uut.serial_number}_{self.test_time}/RawIMU_packet_check_week.bin'
        self.test_log.creat_binf_sct2(file_name=logf_name, sn_num=self.uut.serial_number, test_time=self.test_time)
 
        imu_week_list = []
        imu_ms_list = []
        imu_gps_time = []
        real_time_list = []
        unmatch_time_count = 0
        gps_signal_loss = 0
        self.uut.start_listen_data(0x010a)
        start_time = time.time()
        self.uut.reset_buffer()
        while time.time() - start_time <= 10:
            data = self.uut.read_data()
            if data is not None:
                real_time = get_curr_time()
                self.test_log.write2bin(data)
                parse_data = data[8:8+30]
                fmt = '<HIffffff'
                parse_data_lst = struct.unpack(fmt, parse_data)
                imu_week_list.append(parse_data_lst[0])
                imu_ms_list.append(parse_data_lst[1])
                real_time_list.append(real_time)
        self.uut.stop_listen_data()
        if len(imu_week_list) == 0:
            print('no Raw IMU packets!')

        for i in range(len(imu_week_list)):
            if imu_week_list[i] < 2232:
                gps_signal_loss = gps_signal_loss +1
            else:
                gps_sec = gps_time(imu_week_list[i], imu_ms_list[i]/1000)
                imu_gps_time.append(gps_sec)
                time_diff = cal_time_diff(gps_sec, real_time_list[i])
                #print(f'real time - gps time = {time_diff}')
                if time_diff > 1 or time_diff < -1:
                    unmatch_time_count = unmatch_time_count + 1

        if len(imu_week_list) == 0:
            return False, f'no DM packets', 'could capture DM packets'
        else:
            if unmatch_time_count == 0 and gps_signal_loss != len(imu_week_list):
                return True, f'number of unmatch real time = {unmatch_time_count}, packets have gps time \
= {len(imu_week_list)-gps_signal_loss}', 'match real time <1s'
            elif unmatch_time_count == 0 and gps_signal_loss == len(imu_week_list):
                return False, f'packets have gps time = {len(imu_week_list)-gps_signal_loss}, DM packets \
= {len(imu_week_list)} ', 'at last one DM packet has GPS time'
            else:
                return False, f'number of unmatch real time = {unmatch_time_count}, no gps singal \
= {gps_signal_loss}', 'match real time, <1s'

    def IMU_data_packet_reasonable_check_ms(self):
        result = False
        interval = None
        logf_name = f'./data/Packet_ODR_test_data/{self.uut.serial_number}_{self.test_time}/RawIMU_packet_check_ms.bin'
        self.test_log.creat_binf_sct2(file_name=logf_name, sn_num=self.uut.serial_number, test_time=self.test_time)
 
        imu_week_list = []
        imu_ms_list = []
        real_time_list = []
        neighbor_gps_pair = 0
        gps_signal_loss = 0
        num_interval_err = 0
        self.uut.start_listen_data(0x010a)
        start_time = time.time()
        self.uut.reset_buffer()
        while time.time() - start_time <= 10:
            data = self.uut.read_data()
            if data is not None:
                real_time = get_curr_time()
                self.test_log.write2bin(data)
                parse_data = data[8:8+30]
                fmt = '<HIffffff'
                parse_data_lst = struct.unpack(fmt, parse_data)
                imu_week_list.append(parse_data_lst[0])
                imu_ms_list.append(parse_data_lst[1])
                real_time_list.append(real_time)
        self.uut.stop_listen_data()
        if len(imu_week_list) == 0:
            print('no Raw IMU packets!')

        if len(imu_week_list) >= 2:
            for i in range(len(imu_week_list)):
                if i + 1 < len(imu_week_list):
                    if imu_week_list[i] >= 2232:
                        if imu_week_list[i+1] >=2232:
                            time_interval = imu_ms_list[i+1] - imu_ms_list[i]
                            neighbor_gps_pair = neighbor_gps_pair +1
                            if time_interval == 10: #IMU 100pkts/Sec, interval=10ms
                                continue
                            else:
                                num_interval_err = num_interval_err +1
                    else:
                        gps_signal_loss = gps_signal_loss + 1    
            if imu_week_list[-1] < 2232:
                gps_signal_loss = gps_signal_loss + 1

        if len(imu_week_list) == 0:
            return False, f'no Raw IMU packets', 'could capture Raw IMU packets'
        elif len(imu_week_list) < 2:
            return False, f'Raw IMU packets = {len(imu_week_list)} ', 'at last need two Raw IMU packets have GPS time'
        elif len(imu_week_list) >=2 and neighbor_gps_pair <1:
            return False, f'Raw IMU packets = {len(imu_week_list)}, packets have gps time \
= {len(imu_week_list)-gps_signal_loss}, neighbor gps pairs = {neighbor_gps_pair} ', \
'at last one pair neighbor Raw IMU packets has gps signal'
        else:
            if num_interval_err > 0:
                return False, f'Raw IMU packets = {len(imu_week_list)}, packets have gps time \
= {len(imu_week_list)-gps_signal_loss}, neighbor gps pair = {neighbor_gps_pair}, interval error = {num_interval_err} ', 'interval is not 1000ms'
            else:
                return True, f'Raw IMU packets = {len(imu_week_list)}, packets have gps time \
= {len(imu_week_list)-gps_signal_loss}, neighbor gps pair = {neighbor_gps_pair}, interval error = {num_interval_err} ', 'interval = 1000ms'

    def IMU_data_packet_reasonable_check_accel(self):
        logf_name = f'./data/Packet_ODR_test_data/{self.uut.serial_number}_{self.test_time}/RawIMU_packet_check_accel.bin'
        self.test_log.creat_binf_sct2(file_name=logf_name, sn_num=self.uut.serial_number, test_time=self.test_time)
 
        imu_accel_x_list = []
        imu_accel_y_list = []
        imu_accel_z_list = []
        accel_mod_err_list = []
        self.uut.start_listen_data(0x010a)
        start_time = time.time()
        self.uut.reset_buffer()
        while time.time() - start_time <= 10:
            data = self.uut.read_data()
            if data is not None:
                self.test_log.write2bin(data)
                parse_data = data[8:8+30]
                fmt = '<HIffffff'
                parse_data_lst = struct.unpack(fmt, parse_data)
                imu_accel_x_list.append(parse_data_lst[2])
                imu_accel_y_list.append(parse_data_lst[3])
                imu_accel_z_list.append(parse_data_lst[4])
        self.uut.stop_listen_data()
        if len(imu_accel_x_list) == 0:
            print('no Raw IMU packets!')

        for i in range(len(imu_accel_x_list)):
            s2 = math.pow(imu_accel_x_list[i],2) + math.pow(imu_accel_y_list[i],2) + math.pow(imu_accel_z_list[i],2)
            accel_mod_value = math.pow(s2, 1/2)
            #accel_mod_value = abs(imu_accel_x_list[i]) + abs(imu_accel_y_list[i]) + abs(imu_accel_z_list[i])
            if 9.7 < abs(accel_mod_value) < 9.9:
                continue
            else:
                print(imu_accel_x_list[i],imu_accel_y_list[i],imu_accel_z_list[i])
                accel_mod_err_list.append([imu_accel_x_list[i],imu_accel_y_list[i],imu_accel_z_list[i]])

        if len(imu_accel_x_list) == 0:
            return False, f'no Raw IMU packets', 'could capture Raw IMU packets'
        elif len(accel_mod_err_list) > 0:
            return False, f'accel mode is not 1g, err count={len(accel_mod_err_list)},total packets={len(imu_accel_x_list)}', 'accel of module is about 1g'
        else:
            return True, f'accel mode = 1g,total packets={len(imu_accel_x_list)}', 'accel of module is about 1g'

    def IMU_data_packet_reasonable_check_gyro(self):
        logf_name = f'./data/Packet_ODR_test_data/{self.uut.serial_number}_{self.test_time}/RawIMU_packet_check_gyro.bin'
        self.test_log.creat_binf_sct2(file_name=logf_name, sn_num=self.uut.serial_number, test_time=self.test_time)
 
        imu_gyro_x_list = []
        imu_gyro_y_list = []
        imu_gyro_z_list = []
        imu_gyro_err_list = []
        self.uut.start_listen_data(0x010a)
        start_time = time.time()
        self.uut.reset_buffer()
        while time.time() - start_time <= 10:
            data = self.uut.read_data()
            if data is not None:
                self.test_log.write2bin(data)
                parse_data = data[8:8+30]
                fmt = '<HIffffff'
                parse_data_lst = struct.unpack(fmt, parse_data)
                imu_gyro_x_list.append(parse_data_lst[5])
                imu_gyro_y_list.append(parse_data_lst[6])
                imu_gyro_z_list.append(parse_data_lst[7])
        self.uut.stop_listen_data()
        if len(imu_gyro_x_list) == 0:
            print('no Raw IMU packets!')

        for i in range(len(imu_gyro_x_list)):
            if abs(imu_gyro_x_list[i])<5 and abs(imu_gyro_y_list[i])<5 and abs(imu_gyro_z_list[i])<5:
                continue
            else:
                print(imu_gyro_x_list[i], imu_gyro_y_list[i], imu_gyro_z_list[i])
                imu_gyro_err_list.append([imu_gyro_x_list[i], imu_gyro_y_list[i], imu_gyro_z_list[i]])

        if len(imu_gyro_x_list) == 0:
            return False, f'no Raw IMU packets', 'could capture Raw IMU packets'
        elif len(imu_gyro_err_list) > 0:
            return False, f'gyro is above 5 degree/s, error count={len(imu_gyro_err_list)} ', 'gyro of each axis is below 5 degree/s'
        else:
            return True, f'gyro of each axis is below 5 degree/s', 'gyro of each axis is below 5 degree/s'

    def NMEA_GNGGA_data_packet_check_ID_GNGGA(self):
        logf_name = f'./data/Packet_ODR_test_data/{self.uut.serial_number}_{self.test_time}/NMEA_GNGGA_ID.bin'
        self.test_log.creat_binf_sct2(file_name=logf_name, sn_num=self.uut.serial_number, test_time=self.test_time)
 
        gngga_list = []
        gngga_id_err_list = []
        self.uut.start_listen_data_nmea(0x4747)
        start_time = time.time()
        self.uut.reset_buffer()
        while time.time() - start_time <= 10:
            data = self.uut.read_data()
            if data is not None:
                self.test_log.write2bin(data)
                parse_data = str(data[0:82], 'utf-8')
                parse_data = str(data[0:37], 'utf-8')
                gngga_list.append(parse_data)
                #print(parse_data)
        self.uut.stop_listen_data()
        if len(gngga_list) == 0:
            print('no NMEA GNZDA packets!')

        for i in range(len(gngga_list)):
            gngga_talker = get_talker(gngga_list[i])
            gngga_sentence_type = get_sentence_type(gngga_list[i])
            if gngga_talker == 'GN':
                if gngga_sentence_type == 'GGA':
                    continue
                else:
                    gngga_id_err_list.append(gngga_list[i])
            else:
                gngga_id_err_list.append(gngga_list[i])

        if len(gngga_list) == 0:
            return False, f'no NMEA GNGGA packets!', 'could capture NMEA GNGGA packets'
        elif len(gngga_id_err_list) > 0:
            return False, f'nmea data do not include GNGGA, error count={len(gngga_id_err_list)} ', 'all nmea data include GNGGA'
        else:
            return True, f'all nmea data include GNGGA', 'all nmea data include GNGGA'

    def NMEA_GNGGA_data_packet_check_utc_time(self):
        logf_name = f'./data/Packet_ODR_test_data/{self.uut.serial_number}_{self.test_time}/NMEA_GNGGA_UTC_time.bin'
        self.test_log.creat_binf_sct2(file_name=logf_name, sn_num=self.uut.serial_number, test_time=self.test_time)
 
        gngga_utc_list = []
        gngga_utc_err_list = []
        real_time_list = []
        unmatch_time_list = []
        self.uut.start_listen_data_nmea(0x4747)
        start_time = time.time()
        self.uut.reset_buffer()
        while time.time() - start_time <= 10:
            data = self.uut.read_data()
            if data is not None:
                real_time = get_curr_time()
                self.test_log.write2bin(data)
                parse_data = str(data[0:82], 'utf-8')
                gngga_list = parse_data.split(",")
                gngga_utc_list.append(gngga_list[1])
                real_time_list.append(real_time)
        self.uut.stop_listen_data()
        if len(gngga_utc_list) == 0:
            print('no NMEA GNGGA packets!')

        for i in range(len(gngga_utc_list)):
            print(gngga_utc_list[i])
            hour = int(gngga_utc_list[i][0:2])
            minute = int(gngga_utc_list[i][2:4])
            second = int(gngga_utc_list[i][4:6])
            ms = int(gngga_utc_list[i][7:9])
            hour_real = real_time_list[i].hour
            minute_real = real_time_list[i].minute
            second_real = real_time_list[i].second
            microsec_real = real_time_list[i].microsecond
            time_diff = (second_real*1000+microsec_real/1000)-(second*1000+ms*100)
            if minute_real == minute:
                if abs(time_diff) < 1000:
                    continue
                else:
                    unmatch_time_list.append(gngga_list[i])
            else:
                unmatch_time_list.append(gngga_utc_list[i])

        if len(gngga_utc_list) == 0:
            return False, f'no NMEA GNGGA packets!', 'could capture NMEA GNGGA packets'
        elif len(unmatch_time_list) > 0:
            return False, f'UTC time do not matchs the real time, unmatch count={len(unmatch_time_list)}/{len(gngga_utc_list)}', 'UTC time in GNGGA matchs the real time '
        else:
            return True, f'UTC time in GNGGA matchs the real time', 'UTC time in GNGGA matchs the real time'

    def NMEA_GNGGA_data_packet_check_latitude(self):
        gngga_lat_p = self.properties["NMEA"]["latitude"]
        gngga_lat_dev_p = self.properties["NMEA"]["latitude_dev"]
        gngga_lat_dir_p = self.properties["NMEA"]["latitude_dir"]
        logf_name = f'./data/Packet_ODR_test_data/{self.uut.serial_number}_{self.test_time}/NMEA_GNGGA_latitude.bin'
        self.test_log.creat_binf_sct2(file_name=logf_name, sn_num=self.uut.serial_number, test_time=self.test_time)
 
        gngga_list = []
        unmatch_lat_list = []
        self.uut.start_listen_data_nmea(0x4747)
        start_time = time.time()
        self.uut.reset_buffer()
        while time.time() - start_time <= 10:
            data = self.uut.read_data()
            if data is not None:
                self.test_log.write2bin(data)
                parse_data = str(data[0:82], 'utf-8')
                gngga_list.append(parse_data)
        self.uut.stop_listen_data()
        if len(gngga_list) == 0:
            print('no NMEA GNGGA packets!')

        for i in range(len(gngga_list)):
            gngga_lat, gngga_lat_dir = get_latitude(gngga_list[i])
            #print(gngga_lat, gngga_lat_dir)
            if gngga_lat_dir == gngga_lat_dir_p:
                if abs(gngga_lat-gngga_lat_p) < gngga_lat_dev_p:
                    continue
                else:
                    unmatch_lat_list.append([gngga_lat, gngga_lat_dir])
            else:
                unmatch_lat_list.append([gngga_lat, gngga_lat_dir])

        if len(gngga_list) == 0:
            return False, f'no NMEA GNGGA packets!', 'could capture NMEA GNGGA packets'
        elif len(unmatch_lat_list) > 0:
            return False, f'latitude not within a reasonable range, unmatch count={len(unmatch_lat_list)}/{len(gngga_list)}', 'latitude in GNGGA within a reasonable range'
        else:
            return True, f'latitude in GNGGA within a reasonable range', 'latitude in GNGGA within a reasonable range'

    def NMEA_GNGGA_data_packet_check_longitude(self):
        gngga_lon_p = self.properties["NMEA"]["longitude"]
        gngga_lon_dev_p = self.properties["NMEA"]["longitude_dev"]
        gngga_lon_dir_p = self.properties["NMEA"]["longitude_dir"]
        logf_name = f'./data/Packet_ODR_test_data/{self.uut.serial_number}_{self.test_time}/NMEA_GNGGA_longitude.bin'
        self.test_log.creat_binf_sct2(file_name=logf_name, sn_num=self.uut.serial_number, test_time=self.test_time)
 
        gngga_list = []
        unmatch_lat_list = []
        self.uut.start_listen_data_nmea(0x4747)
        start_time = time.time()
        self.uut.reset_buffer()
        while time.time() - start_time <= 10:
            data = self.uut.read_data()
            if data is not None:
                self.test_log.write2bin(data)
                parse_data = str(data[0:82], 'utf-8')
                gngga_list.append(parse_data)
        self.uut.stop_listen_data()
        if len(gngga_list) == 0:
            print('no NMEA GNGGA packets!')

        for i in range(len(gngga_list)):
            gngga_lon, gngga_lon_dir = get_longitude(gngga_list[i])
            #print(gngga_lon, gngga_lon_dir)
            if gngga_lon_dir == gngga_lon_dir_p:
                if abs(gngga_lon-gngga_lon_p) < gngga_lon_dev_p:
                    continue
                else:
                    unmatch_lat_list.append([gngga_lon, gngga_lon_dir])
            else:
                unmatch_lat_list.append([gngga_lon, gngga_lon_dir])

        if len(gngga_list) == 0:
            return False, f'no NMEA GNGGA packets!', 'could capture NMEA GNGGA packets'
        elif len(unmatch_lat_list) > 0:
            return False, f'longitude not within a reasonable range, unmatch count={len(unmatch_lat_list)}/{len(gngga_list)}', 'longitude in GNGGA within a reasonable range'
        else:
            return True, f'longitude in GNGGA within a reasonable range', 'longitude in GNGGA within a reasonable range'

    def NMEA_GNGGA_data_packet_check_position_type(self):
        position_type_p = self.properties["NMEA"]["position type"]
        logf_name = f'./data/Packet_ODR_test_data/{self.uut.serial_number}_{self.test_time}/NMEA_GNGGA_position_type.bin'
        self.test_log.creat_binf_sct2(file_name=logf_name, sn_num=self.uut.serial_number, test_time=self.test_time)
 
        gngga_list = []
        unmatch_pos_list = []
        self.uut.start_listen_data_nmea(0x4747)
        start_time = time.time()
        self.uut.reset_buffer()
        while time.time() - start_time <= 10:
            data = self.uut.read_data()
            if data is not None:
                self.test_log.write2bin(data)
                parse_data = str(data[0:82], 'utf-8')
                gngga_list.append(parse_data)
        self.uut.stop_listen_data()
        if len(gngga_list) == 0:
            print('no NMEA GNGGA packets!')

        for i in range(len(gngga_list)):
            gngga_position_type = get_position_type(gngga_list[i])
            #print(gngga_position_type)
            if gngga_position_type == position_type_p:
                continue
            else:
                unmatch_pos_list.append(gngga_position_type)

        if len(gngga_list) == 0:
            return False, f'no NMEA GNGGA packets!', 'could capture NMEA GNGGA packets'
        elif len(unmatch_pos_list) > 0:
            return False, f'position type can not converges to 4, unmatch count={len(unmatch_pos_list)}/{len(gngga_list)}', 'position type in GNGGA can converges to 4'
        else:
            return True, f'position type in GNGGA can converges to 4', 'position type in GNGGA can converges to 4(RTK_fixed)'
        
    def NMEA_GNZDA_data_packet_check_ID_GNZDA(self):
        logf_name = f'./data/Packet_ODR_test_data/{self.uut.serial_number}_{self.test_time}/NMEA_GNZDA_ID.bin'
        self.test_log.creat_binf_sct2(file_name=logf_name, sn_num=self.uut.serial_number, test_time=self.test_time)
 
        gngga_list = []
        gngga_id_err_list = []
        self.uut.start_listen_data_nmea(0x5a44)
        start_time = time.time()
        self.uut.reset_buffer()
        while time.time() - start_time <= 10:
            data = self.uut.read_data()
            if data is not None:
                self.test_log.write2bin(data)
                parse_data = str(data[0:37], 'utf-8')
                gngga_list.append(parse_data)
                #print(parse_data)
        self.uut.stop_listen_data()
        if len(gngga_list) == 0:
            print('no NMEA GNZDA packets!')

        for i in range(len(gngga_list)):
            gngga_talker = get_talker(gngga_list[i])
            gngga_sentence_type = get_sentence_type(gngga_list[i])
            if gngga_talker == 'GN':
                if gngga_sentence_type == 'ZDA':
                    continue
                else:
                    gngga_id_err_list.append(gngga_list[i])
            else:
                gngga_id_err_list.append(gngga_list[i])

        if len(gngga_list) == 0:
            return False, f'no NMEA GNZDA packets!', 'could capture NMEA GNZDA packets'
        elif len(gngga_id_err_list) > 0:
            return False, f'nmea data do not include GNZDA, error count={len(gngga_id_err_list)} ', 'all nmea data include GNZDA'
        else:
            return True, f'all nmea data include GNZDA', 'all nmea data include GNZDA'

    def NMEA_GNZDA_data_packet_check_utc_time(self):
        logf_name = f'./data/Packet_ODR_test_data/{self.uut.serial_number}_{self.test_time}/NMEA_GNZDA_UTC_time.bin'
        self.test_log.creat_binf_sct2(file_name=logf_name, sn_num=self.uut.serial_number, test_time=self.test_time)
 
        gngga_list = []
        real_time_list = []
        unmatch_time_list = []
        self.uut.start_listen_data_nmea(0x5a44)
        start_time = time.time()
        self.uut.reset_buffer()
        while time.time() - start_time <= 10:
            data = self.uut.read_data()
            if data is not None:
                real_time = get_curr_time()
                self.test_log.write2bin(data)
                parse_data = str(data[0:37], 'utf-8')
                #gngga_list = parse_data.split(",")
                #gngga_utc_list.append(gngga_list[1])
                gngga_list.append(parse_data)
                real_time_list.append(real_time)
        self.uut.stop_listen_data()
        if len(gngga_list) == 0:
            print('no NMEA GNZDA packets!')

        for i in range(len(gngga_list)):
            datetime_zda = get_zda_utc(gngga_list[i])
            #print(f'gnzda utc = {datetime_zda}')
            time_now = real_time_list[i]
            #print(f'local time = {time_now}')
            time_diff = float(time_now.timestamp()) - datetime_zda.timestamp()
            #print(time_diff)
            if -1 < time_diff < 1:
                continue
            else:
                unmatch_time_list.append(gngga_list[i])

        if len(gngga_list) == 0:
            return False, f'no NMEA GNZDA packets!', 'could capture NMEA GNZDA packets'
        elif len(unmatch_time_list) > 0:
            return False, f'UTC time do not matchs the real time, unmatch count={len(unmatch_time_list)}/{len(gngga_list)}', 'UTC time in GNZDA matchs the real time '
        else:
            return True, f'UTC time in GNZDA matchs the real time', 'UTC time in GNZDA matchs the real time'
