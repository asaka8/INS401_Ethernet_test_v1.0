import os
import time
import struct
import random
import math
import threading 

from tqdm import trange
from ..conmunicator.INS401_Ethernet import Ethernet_Dev
from ..conmunicator.ntrip_center import *
from moudle.gps_time_module import get_curr_time, gps_time, cal_time_diff, stamptime_to_datetime
from moudle.nmea_module import *
from ..test_framwork.Jsonf_Creater import Json_Creat
from ..test_framwork.Test_Logger import TestLogger

INPUT_PACKETS = [b'\x01\xcc', b'\x02\xcc', b'\x03\xcc', b'\x04\xcc', b'\x05\xcc', b'\x06\xcc', b'\x01\x0b', b'\x02\x0b', b'\x07\xcc']
OTHER_OUTPUT_PACKETS = [b'\x01\n', b'\x02\n', b'\x03\n', b'\x04\n', b'\x05\n', b'\x06\n']

rtcm_data = [1, 2, 3, 4, 5, 6, 7, 8]
vehicle_speed_value = 80
LONGTERM_RUNNING_COUNT = 10000
REAL_CAP_START_TIME = None

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
        response = self.uut.write_read_response(command, message_bytes, 0.5)
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
        response = self.uut.write_read_response(command, message_bytes, 0.5)
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

        response = self.uut.write_read_response(command, message_bytes, 0.5)

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
            self.uut.reset_dev_info()
            time.sleep(60)
            self.uut.find_device(times=0)
            get_response = self.uut.write_read_response(get_command, get_message_bytes, 0.5)
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
        get_response = self.uut.write_read_response(get_command, get_message_bytes, 0.5)
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
                get_response = self.uut.write_read_response(get_command, get_message_bytes, 0.5)
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

        set_response = self.uut.write_read_response(set_command, set_message_bytes, 0.5)[2]
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
        check_response = self.uut.write_read_response(check_command, check_message_bytes, 0.5)[2]

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
        check_response = self.uut.write_read_response(check_command, check_message_bytes, 0.5)[2]

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

        check_response = self.uut.write_read_response(cmd, message_bytes, 0.5)[2]
        vcode_ver_payload = check_response[2:4]
        vcode_ver = struct.unpack('<h', vcode_ver_payload)[0]

        if vcode_ver == except_ver:
            return True, f'vehicle table version: {except_ver}', f'vehicle table version: {vcode_ver}'
        else:
            return False, f'vehicle table version: {except_ver}', f'vehicle table version: {vcode_ver}'

    ### section7 GNSS packet reasonable check (connect antenna)

    def static_test_setup(self):
        global REAL_CAP_START_TIME
        static_run_time = self.properties["static test"]["STATIC_RUNNING_TIME"]
        #filter_type = self.properties["static test"]["TypeFilter"]
        # logf_name = f'./data/static_test_data/{self.product_sn}_{self.test_time}/static_test_data_{self.test_time}.bin' 
        # logf_name = f'./data/Packet_long_term_test_data/long_terms_data_{self.test_time}.pcap' 
        logf_name = f'./data/static_test_data/static_test_data_{self.test_time}.bin'
        self.test_log.creat_binf_sct7(logf_name)

        self.eth.find_device(0)
        ntrip = RuNtrip(self.eth)
        #self.eth.find_device(1)
        ntrip_thread = threading.Thread(target=ntrip.ntrip_client_thread, args=(static_run_time,))
        print("Run ntrip...")
        ntrip_thread.start()

        start_time = time.time()
        self.uut.start_listen_data()
        self.uut.reset_buffer()
        REAL_CAP_START_TIME = get_curr_time()    
        self.tlock.acquire()    
        while time.time() - start_time <= static_run_time:
            data = self.uut.read_data()
            self.test_log.write2bin(data)
            # self.test_log.write2pcap(data, logf_name)
        self.tlock.release()
        ntrip_thread.join()
        print("ntrip stop!")
        self.uut.stop_listen_data()
        if self.uut.check_len() != 0:
            while True:
                data = self.uut.read_data()
                self.test_log.write2bin(data)
                if self.uut.check_len() == 0:
                    break

    def GNSS_packet_reasonable_check_week(self):
        logf_name = f'./data/static_test_data/static_test_data_{self.test_time}.bin'

        if not os.path.exists(logf_name):
            self.static_test_setup()
            logf = open(logf_name, 'rb')
        else:
            logf = open(logf_name, 'rb')
        log_data = logf.read()
        gnss_packet_type = [0x55, 0x55, 0x02, 0x0a]
 
        gps_week_list = []
        gps_ms_list = []
        gps_secs_lst = []
        unmatch_time_count = 0
        gps_signal_loss = 0
        for i in range(len(log_data)):
            data = log_data[i:i+87]
            packet_start_flag = data.find(bytes(gnss_packet_type))
            if packet_start_flag == 0:
                parse_data = data[8:-2]
                fmt = '<HIBdddfffBBffffffff'
                parse_data_lst = struct.unpack(fmt, parse_data)
                gps_week_list.append(parse_data_lst[0])
                gps_ms_list.append(parse_data_lst[1])
        
        for i in range(len(gps_week_list)):
            if gps_week_list[i] < 2232:
                gps_signal_loss = gps_signal_loss + 1
            else:
                gps_sec = gps_time(gps_week_list[i], gps_ms_list[i]/1000)
                gps_secs_lst.append(gps_sec)
                time_diff = cal_time_diff(gps_secs_lst[i], REAL_CAP_START_TIME)
                #print(f'real time - gps time = {time_diff}')
                if (-2-i) > time_diff or time_diff > (0-i):
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
        logf_name = f'./data/static_test_data/static_test_data_{self.test_time}.bin'

        if not os.path.exists(logf_name):
            self.static_test_setup()
            logf = open(logf_name, 'rb')
        else:
            logf = open(logf_name, 'rb')
        log_data = logf.read()
        gnss_packet_type = [0x55, 0x55, 0x02, 0x0a]
 
        gps_week_list = []
        gps_ms_list = []
        gps_interval_err_lst = []
        gps_signal_loss = 0
        num_interval_err = 0
        neighbor_gps_pair = 0
        for i in range(len(log_data)):
            data = log_data[i:i+87]
            packet_start_flag = data.find(bytes(gnss_packet_type))
            if packet_start_flag == 0:
                parse_data = data[8:-2]
                fmt = '<HIBdddfffBBffffffff'
                parse_data_lst = struct.unpack(fmt, parse_data)
                gps_week_list.append(parse_data_lst[0])
                gps_ms_list.append(parse_data_lst[1])

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
                                gps_interval_err_lst.append([i+2,time_interval])
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
        elif len(gps_interval_err_lst) >0:
            return False, f'GNSS packets={len(gps_week_list)}, packets have gps time={len(gps_week_list)-gps_signal_loss}, neighbor gps pair={neighbor_gps_pair} error interval={len(gps_interval_err_lst)} ', 'interval = 1000ms'
        else:
            return True, f'GNSS packets = {len(gps_week_list)}, packets have gps time = {len(gps_week_list)-gps_signal_loss}, neighbor gps pair = {neighbor_gps_pair} error interval={len(gps_interval_err_lst)}', 'interval = 1000ms'

    def GNSS_packet_reasonable_check_position_type(self):
        logf_name = f'./data/static_test_data/static_test_data_{self.test_time}.bin'

        if not os.path.exists(logf_name):
            self.static_test_setup()
            logf = open(logf_name, 'rb')
        else:
            logf = open(logf_name, 'rb')
        log_data = logf.read()
        gnss_packet_type = [0x55, 0x55, 0x02, 0x0a]

        pos_list = []
        pos_err_list = []

        for i in range(len(log_data)):
            data = log_data[i:i+87]
            packet_start_flag = data.find(bytes(gnss_packet_type))
            if packet_start_flag == 0:
                parse_data = data[8:-2]
                fmt = '<HIBdddfffBBffffffff'
                parse_data_lst = struct.unpack(fmt, parse_data)
                pos_list.append(parse_data_lst[2])
                #print(f'pos = {parse_data_lst[2]}')

        for i in range(len(pos_list)):
            if pos_list[i] == 4:
                continue
            else:
                pos_err_list.append(pos_list[i])
                print(f'error: pos = {pos_list[i]}')

        if len(pos_list) == 0:
            return False, f'no GNSS packets', 'could capture GNSS packets'
        else:
            if len(pos_list) - len(pos_err_list) <= 0:
                return False, f'position type can not converges to 4, pos=4: {len(pos_list)-len(pos_err_list)}/{len(pos_list)} ', 'position type can converges to 4 '
            else:
                return True, f'position type can converges to 4, pos=4: {len(pos_list)-len(pos_err_list)}/{len(pos_list)} ', 'position type can converges to 4 '

    def GNSS_packet_reasonable_check_satellites(self):
        logf_name = f'./data/static_test_data/static_test_data_{self.test_time}.bin'

        if not os.path.exists(logf_name):
            self.static_test_setup()
            logf = open(logf_name, 'rb')
        else:
            logf = open(logf_name, 'rb')
        log_data = logf.read()
        gnss_packet_type = [0x55, 0x55, 0x02, 0x0a]
 
        sat_list = []
        sat_err_list = []
        for i in range(len(log_data)):
            data = log_data[i:i+87]
            packet_start_flag = data.find(bytes(gnss_packet_type))
            if packet_start_flag == 0:
                parse_data = data[8:-2]
                fmt = '<HIBdddfffBBffffffff'
                parse_data_lst = struct.unpack(fmt, parse_data)
                sat_list.append(parse_data_lst[9])
                #print(parse_data_lst[9], parse_data_lst[10])

        for i in range(len(sat_list)):
            if sat_list[i] >= 16:
                continue
            else:
                sat_err_list.append(sat_list[i])
                print(f'error: num of satellites={sat_list[i]}  <16')

        if len(sat_list) == 0:
            return False, f'no GNSS packets', 'could capture GNSS packets'
        else:
            if len(sat_err_list) > 0:
                return False, f'number of satellites >= 16:{len(sat_list)-len(sat_err_list)}/{len(sat_list)} ', 'number of satellites is not zero and >= 16 '
            else:
                return True, f'number of satellites >= 16:{len(sat_list)-len(sat_err_list)}/{len(sat_list)} ', 'number of satellites is not zero and >= 16 '

    def GNSS_packet_reasonable_check_latlongitude(self):
        logf_name = f'./data/static_test_data/static_test_data_{self.test_time}.bin'

        if not os.path.exists(logf_name):
            self.static_test_setup()
            logf = open(logf_name, 'rb')
        else:
            logf = open(logf_name, 'rb')
        log_data = logf.read()
        gnss_packet_type = [0x55, 0x55, 0x02, 0x0a]

        sat_list = []
        sat_err_list = []
        for i in range(len(log_data)):
            data = log_data[i:i+87]
            packet_start_flag = data.find(bytes(gnss_packet_type))
            if packet_start_flag == 0:
                parse_data = data[8:-2]
                fmt = '<HIBdddfffBBffffffff'
                parse_data_lst = struct.unpack(fmt, parse_data)
                sat_list.append([parse_data_lst[3], parse_data_lst[4]])
                #print(parse_data_lst[3], parse_data_lst[4])

        for i in range(len(sat_list)):
            if 31.116666666667<sat_list[i][0]<32.033333333333 and 119.55<sat_list[i][1]<120.63333333333:
                continue
            else:
                sat_err_list.append(sat_list[i])

        if len(sat_list) == 0:
            return False, f'no GNSS packets', 'could capture GNSS packets'
        else:
            if len(sat_err_list) > 0:
                return False, f'The location point in Wuxi:{len(sat_list)-len(sat_err_list)}/{len(sat_list)} ', 'The location point in Wuxi '
            else:
                return True, f'The location point in Wuxi:{len(sat_list)-len(sat_err_list)}/{len(sat_list)} ', 'The location point in Wuxi '

    ### section8 INS packet reasonable check (connect antenna)

    def INS_packet_reasonable_check_week(self):
        logf_name = f'./data/static_test_data/static_test_data_{self.test_time}.bin'

        if not os.path.exists(logf_name):
            self.static_test_setup()
            logf = open(logf_name, 'rb')
        else:
            logf = open(logf_name, 'rb')
        log_data = logf.read()
        ins_packet_type = [0x55, 0x55, 0x03, 0x0a]

        gps_week_list = []
        gps_ms_list = []
        gps_secs_lst = []
        unmatch_time_count = 0
        gps_signal_loss = 0
        for i in range(len(log_data)):
            data = log_data[i:i+120]
            packet_start_flag = data.find(bytes(ins_packet_type))
            if packet_start_flag == 0:
                parse_data = data[8:-2]
                fmt = '<HIBBdddfffffffffffffffffffH'
                parse_data_lst = struct.unpack(fmt, parse_data)
                gps_week_list.append(parse_data_lst[0])
                gps_ms_list.append(parse_data_lst[1])
        
        for i in range(len(gps_week_list)):
            if gps_week_list[i] < 2232:
                gps_signal_loss = gps_signal_loss +1
            else:
                gps_sec = gps_time(gps_week_list[i], gps_ms_list[i]/1000)
                gps_secs_lst.append(gps_sec)
                time_diff = cal_time_diff(gps_secs_lst[i], REAL_CAP_START_TIME)
                #print(f'real time - gps time = {time_diff}')
                if time_diff > (0-i/100) or time_diff < (-2-i/100):
                    unmatch_time_count = unmatch_time_count + 1

        if len(gps_week_list) == 0:
            return False, f'no INS packets', 'could capture INS packets'
        else:
            if unmatch_time_count == 0 and gps_signal_loss != len(gps_week_list):
                return True, f'number of unmatch real time = {unmatch_time_count}, packets have GNSS time = {len(gps_week_list)-gps_signal_loss}', 'match real time <1s'
            elif unmatch_time_count == 0 and gps_signal_loss == len(gps_week_list):
                return False, f'packets have GNSS time = {len(gps_week_list)-gps_signal_loss}, INS packets = {len(gps_week_list)} ', 'at last one INS packet has GPS time'
            else:
                return False, f'number of unmatch real time = {unmatch_time_count}, no INS singal = {gps_signal_loss}', 'match real time, <1s'

    def INS_packet_reasonable_check_time_ms(self):
        logf_name = f'./data/static_test_data/static_test_data_{self.test_time}.bin'

        if not os.path.exists(logf_name):
            self.static_test_setup()
            logf = open(logf_name, 'rb')
        else:
            logf = open(logf_name, 'rb')
        log_data = logf.read()
        ins_packet_type = [0x55, 0x55, 0x03, 0x0a]

        gps_week_list = []
        gps_ms_list = []
        gps_interval_err_lst = []
        gps_signal_loss = 0
        num_interval_err = 0
        neighbor_gps_pair = 0
        for i in range(len(log_data)):
            data = log_data[i:i+120]
            packet_start_flag = data.find(bytes(ins_packet_type))
            if packet_start_flag == 0:
                parse_data = data[8:-2]
                fmt = '<HIBBdddfffffffffffffffffffH'
                parse_data_lst = struct.unpack(fmt, parse_data)
                gps_week_list.append(parse_data_lst[0])
                gps_ms_list.append(parse_data_lst[1])

        if len(gps_week_list) >= 2:
            for i in range(len(gps_week_list)):
                if i + 1 < len(gps_week_list):
                    if gps_week_list[i] >= 2232:
                        if gps_week_list[i+1] >=2232:
                            time_interval = gps_ms_list[i+1] - gps_ms_list[i]
                            neighbor_gps_pair = neighbor_gps_pair +1
                            if time_interval == 10:
                                continue
                            else:
                                gps_interval_err_lst.append([i+2,time_interval])
                    else:
                        gps_signal_loss = gps_signal_loss + 1    
            if gps_week_list[-1] < 2232:
                gps_signal_loss = gps_signal_loss + 1

        if len(gps_week_list) == 0:
            return False, f'no INS packets', 'could capture INS packets'
        elif len(gps_week_list) < 2:
            return False, f'INS packets = {len(gps_week_list)} ', 'at last need two neighbor INS packets have GPS time'
        elif len(gps_week_list) >=2 and neighbor_gps_pair <1:
            return False, f'INS packets = {len(gps_week_list)}, packets have gps time = {len(gps_week_list)-gps_signal_loss}, neighbor INS pairs = {neighbor_gps_pair} ', 'at last one pair neighbor DM packets has gps signal'
        elif len(gps_interval_err_lst) >0:
            return False, f'INS packets={len(gps_week_list)}, packets have gps time={len(gps_week_list)-gps_signal_loss}, neighbor gps pair={neighbor_gps_pair} error interval={len(gps_interval_err_lst)} ', 'interval = 1000ms'
        else:
            return True, f'INS packets = {len(gps_week_list)}, packets have gps time = {len(gps_week_list)-gps_signal_loss}, neighbor gps pair = {neighbor_gps_pair} error interval={len(gps_interval_err_lst)}', 'interval = 1000ms'

    def INS_packet_reasonable_check_position_type(self):
        logf_name = f'./data/static_test_data/static_test_data_{self.test_time}.bin'

        if not os.path.exists(logf_name):
            self.static_test_setup()
            logf = open(logf_name, 'rb')
        else:
            logf = open(logf_name, 'rb')
        log_data = logf.read()
        ins_packet_type = [0x55, 0x55, 0x03, 0x0a]

        pos_list = []
        pos_err_list = []
        for i in range(len(log_data)):
            data = log_data[i:i+120]
            packet_start_flag = data.find(bytes(ins_packet_type))
            if packet_start_flag == 0:
                parse_data = data[8:-2]
                #parse_data = data[8:8+110]
                fmt = '<HIBBdddfffffffffffffffffffH'
                parse_data_lst = struct.unpack(fmt, parse_data)
                pos_list.append(parse_data_lst[2])
                #print(f'pos = {parse_data_lst[2]}')

        for i in range(len(pos_list)):
            if pos_list[i] == 0:
                continue
            else:
                pos_err_list.append(pos_list[i])

        if len(pos_list) == 0:
            return False, f'no INS packets', 'could capture INS packets'
        else:
            if len(pos_list) - len(pos_err_list) <= 0:
                return False, f'position type not converges to 4, pos=0: {len(pos_list)-len(pos_err_list)}/{len(pos_list)} ', 'position type not converges to 4, static test pos = 0'
            else:
                return True, f'position type not converges to 4, pos=0: {len(pos_list)-len(pos_err_list)}/{len(pos_list)} ', 'position type not converges to 4, static test pos = 0 '

    def INS_packet_reasonable_check_status(self):
        logf_name = f'./data/static_test_data/static_test_data_{self.test_time}.bin'
        #self.test_log.creat_binf_sct7(logf_name)

        if not os.path.exists(logf_name):
            self.static_test_setup()
            logf = open(logf_name, 'rb')
        else:
            logf = open(logf_name, 'rb')
        log_data = logf.read()
        ins_packet_type = [0x55, 0x55, 0x03, 0x0a]

        pos_list = []
        pos_err_list = []
        for i in range(len(log_data)):
            data = log_data[i:i+120]
            packet_start_flag = data.find(bytes(ins_packet_type))
            if packet_start_flag == 0:
                parse_data = data[8:-2]
                fmt = '<HIBBdddfffffffffffffffffffH'
                parse_data_lst = struct.unpack(fmt, parse_data)
                pos_list.append(parse_data_lst[3])

        for i in range(len(pos_list)):
            if pos_list[i] == 0:
                continue
            else:
                pos_err_list.append(pos_list[i])

        if len(pos_list) == 0:
            return False, f'no INS packets', 'could capture INS packets'
        else:
            if len(pos_err_list) > 0:
                return False, f'INS status type can not converges to 0, pos=4:{len(pos_list)-len(pos_err_list)}/{len(pos_list)} ', 'INS status type can converges to 0 '
            else:
                return True, f'INS status type can converges to 0, pos=4:{len(pos_list)-len(pos_err_list)}/{len(pos_list)} ', 'INS status type can converges to 0 '

    def INS_packet_reasonable_check_continent_ID(self):
        logf_name = f'./data/static_test_data/static_test_data_{self.test_time}.bin'
        #self.test_log.creat_binf_sct7(logf_name)

        if not os.path.exists(logf_name):
            self.static_test_setup()
            logf = open(logf_name, 'rb')
        else:
            logf = open(logf_name, 'rb')
        log_data = logf.read()
        ins_packet_type = [0x55, 0x55, 0x03, 0x0a]

        pos_list = []
        pos_err_list = []
        for i in range(len(log_data)):
            data = log_data[i:i+120]
            packet_start_flag = data.find(bytes(ins_packet_type))
            if packet_start_flag == 0:
                parse_data = data[8:-2]
                fmt = '<HIBBdddfffffffffffffffffffH'
                parse_data_lst = struct.unpack(fmt, parse_data)
                pos_list.append(parse_data_lst[26])
                #print(parse_data)
                #print(parse_data_lst)

        for i in range(len(pos_list)):
            if pos_list[i] == 1:
                continue
            else:
                #print(pos_list[i])
                pos_err_list.append(pos_list[i])

        if len(pos_list) == 0:
            return False, f'no INS packets', 'could capture INS packets'
        else:
            if len(pos_err_list) > 0:
                return False, f'Continent ID is not ID_ASIA(1), ID=1:{len(pos_list)-len(pos_err_list)}/{len(pos_list)} ', 'Continent ID is ID_ASIA'
            else:
                return True, f'Continent ID is ID_ASIA, ID=1:{len(pos_list)-len(pos_err_list)}/{len(pos_list)} ', 'Continent ID is ID_ASIA'

    ### section10 DM packet reasonable check (connect antenna)

    def DM_packet_reasonable_check_week(self):
        logf_name = f'./data/static_test_data/static_test_data_{self.test_time}.bin'
        #self.test_log.creat_binf_sct7(logf_name)

        if not os.path.exists(logf_name):
            self.static_test_setup()
            logf = open(logf_name, 'rb')
        else:
            logf = open(logf_name, 'rb')
        log_data = logf.read()
        dm_packet_type = [0x55, 0x55, 0x05, 0x0a]

        gps_week_list = []
        gps_ms_list = []
        gps_secs_lst = []
        unmatch_time_count = 0
        gps_signal_loss = 0
        for i in range(len(log_data)):
            data = log_data[i:i+32]
            packet_start_flag = data.find(bytes(dm_packet_type))
            if packet_start_flag == 0:
                parse_data = data[8:-2]
                fmt = '<HIIfff'
                parse_data_lst = struct.unpack(fmt, parse_data)
                gps_week_list.append(parse_data_lst[0])
                gps_ms_list.append(parse_data_lst[1])
        
        for i in range(len(gps_week_list)):
            if gps_week_list[i] < 2232:
                gps_signal_loss = gps_signal_loss +1
            else:
                gps_sec = gps_time(gps_week_list[i], gps_ms_list[i]/1000)
                gps_secs_lst.append(gps_sec)
                time_diff = cal_time_diff(gps_secs_lst[i], REAL_CAP_START_TIME)
                if time_diff > (0-i) or time_diff < (-2-i):
                    unmatch_time_count = unmatch_time_count + 1
                    print(f'error: real time - gps time = {time_diff+i}')

        if len(gps_week_list) == 0:
            return False, f'no DM packets', 'could capture DM packets'
        else:
            if unmatch_time_count == 0 and gps_signal_loss != len(gps_week_list):
                return True, f'number of unmatch real time = {unmatch_time_count}, packets have gps time = {len(gps_week_list)-gps_signal_loss}', 'match real time <1s'
            elif unmatch_time_count == 0 and gps_signal_loss == len(gps_week_list):
                return False, f'packets have gps time = {len(gps_week_list)-gps_signal_loss}, DM packets = {len(gps_week_list)} ', 'at last one DM packet has GPS time'
            else:
                return False, f'number of unmatch real time = {unmatch_time_count}/{len(gps_week_list)}, no gps singal = {gps_signal_loss}/{len(gps_week_list)}', 'match real time <1s'

    def DM_packet_reasonable_check_time_ms(self):
        logf_name = f'./data/static_test_data/static_test_data_{self.test_time}.bin'
        #self.test_log.creat_binf_sct7(logf_name)

        if not os.path.exists(logf_name):
            self.static_test_setup()
            logf = open(logf_name, 'rb')
        else:
            logf = open(logf_name, 'rb')
        log_data = logf.read()
        dm_packet_type = [0x55, 0x55, 0x05, 0x0a]

        gps_week_list = []
        gps_ms_list = []
        gps_interval_err_lst = []
        gps_signal_loss = 0
        num_interval_err = 0
        neighbor_gps_pair = 0
        for i in range(len(log_data)):
            data = log_data[i:i+32]
            packet_start_flag = data.find(bytes(dm_packet_type))
            if packet_start_flag == 0:
                parse_data = data[8:-2]
                fmt = '<HIIfff'
                parse_data_lst = struct.unpack(fmt, parse_data)
                gps_week_list.append(parse_data_lst[0])
                gps_ms_list.append(parse_data_lst[1])

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
                                gps_interval_err_lst.append([i+2,time_interval])
                                print(f'error: interval = {time_interval}')
                    else:
                        gps_signal_loss = gps_signal_loss + 1    
            if gps_week_list[-1] < 2232:
                gps_signal_loss = gps_signal_loss + 1

        if len(gps_week_list) == 0:
            return False, f'no DM packets', 'could capture DM packets'
        elif len(gps_week_list) < 2:
            return False, f'DM packets={len(gps_week_list)} ', 'at last need two neighbor DM packets have GPS time'
        elif len(gps_week_list) >=2 and neighbor_gps_pair <1:
            return False, f'DM packets={len(gps_week_list)}, packets have gps time={len(gps_week_list)-gps_signal_loss}\, neighbor gps pairs={neighbor_gps_pair} ', 'at last one pair neighbor DM packets has gps signal'
        elif len(gps_interval_err_lst) >0:
            return False, f'DM packets={len(gps_week_list)}, packets have gps time={len(gps_week_list)-gps_signal_loss}, neighbor gps pair={neighbor_gps_pair} error interval={len(gps_interval_err_lst)} ', 'interval = 1000ms'
        else:
            return True, f'DM packets={len(gps_week_list)}, packets have gps time={len(gps_week_list)-gps_signal_loss}, neighbor gps pair={neighbor_gps_pair} error interval={len(gps_interval_err_lst)}', 'interval = 1000ms'

    def DM_packet_reasonable_check_temp(self):
        logf_name = f'./data/static_test_data/static_test_data_{self.test_time}.bin'
        #self.test_log.creat_binf_sct7(logf_name)

        if not os.path.exists(logf_name):
            self.static_test_setup()
            logf = open(logf_name, 'rb')
        else:
            logf = open(logf_name, 'rb')
        log_data = logf.read()
        dm_packet_type = [0x55, 0x55, 0x05, 0x0a]

        temp_list = []
        for i in range(len(log_data)):
            data = log_data[i:i+32]
            packet_start_flag = data.find(bytes(dm_packet_type))
            if packet_start_flag == 0:
                parse_data = data[8:-2]
                fmt = '<HIIfff'
                parse_data_lst = struct.unpack(fmt, parse_data)
                IMU_temp = parse_data_lst[3]
                MCU_temp = parse_data_lst[4]
                GNSS_chip_temp = parse_data_lst[5]
                #print(f'IMU = {IMU_temp}, MCU = {MCU_temp}, GNSS = {GNSS_chip_temp}')
                temp_list.append([IMU_temp,MCU_temp,GNSS_chip_temp])

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
                        print(f'error: GNSS = {GNSS_chip_temp} out of 40-85')
                else:
                    mcu_out = mcu_out +1
                    print(f'error: MCU = {MCU_temp} out of 40-85')
            else:
                imu_out = imu_out +1
                print(f'error: IMU = {IMU_temp} out of 40-85')
        
        if len(temp_list) == 0:
            return False, 'no DM packets', 'could capture DM packets'
        else:
            if imu_out + mcu_out + gnss_out == 0:
                return True, 'Temperature of IMU/MCU/GNSS chip is in reasonable range', '-40 < temp <85'
            else:
                return False, f'amount out of temp range: IMU={imu_out}/{len(temp_list)},MCU={mcu_out}/{len(temp_list)},GNSS={gnss_out}/{len(temp_list)}', '-40 < temp <85'

    def DM_packet_reasonable_check_status_gnss(self):
        logf_name = f'./data/static_test_data/static_test_data_{self.test_time}.bin'
        #self.test_log.creat_binf_sct7(logf_name)

        if not os.path.exists(logf_name):
            self.static_test_setup()
            logf = open(logf_name, 'rb')
        else:
            logf = open(logf_name, 'rb')
        log_data = logf.read()
        dm_packet_type = [0x55, 0x55, 0x05, 0x0a]

        pps_list = []
        gnss_data_list = []
        gnss_signal_list = []
        for i in range(len(log_data)):
            data = log_data[i:i+32]
            packet_start_flag = data.find(bytes(dm_packet_type))
            if packet_start_flag == 0:
                parse_data = data[8:-2]
                fmt = '<HIIfff'
                parse_data_lst = struct.unpack(fmt, parse_data)
                status_bit = parse_data_lst[2]
                dev_status_bin = "{0:{fill}32b}".format(status_bit, fill='0')
                #PPS status = bit10, 31-10=21
                #GNSS data status = bit11
                #GNSS signal status = bit12
                pps_list.append(dev_status_bin[21])
                if pps_list[-1] == '1':
                    print('error: PPS=1, PPS pulse exception ', end=' || ')
                elif pps_list[-1] == '0':
                    pass
                gnss_data_list.append(dev_status_bin[20])
                if gnss_data_list[-1] == '1':
                    print('error: GNSS data status=1, GNSS chipset has NO data output', end=' || ')
                elif gnss_data_list[-1] == '0':
                    pass
                gnss_signal_list.append(dev_status_bin[19])
                if gnss_signal_list[-1] == '1':
                    print('error: GNSS signal status=1, GNSS chipset has data output, but no valid signal detected')
                elif gnss_signal_list[-1] == '0':
                    pass
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
        logf_name = f'./data/static_test_data/static_test_data_{self.test_time}.bin'
        #self.test_log.creat_binf_sct7(logf_name)

        if not os.path.exists(logf_name):
            self.static_test_setup()
            logf = open(logf_name, 'rb')
        else:
            logf = open(logf_name, 'rb')
        log_data = logf.read()
        dm_packet_type = [0x55, 0x55, 0x05, 0x0a]

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
        for i in range(len(log_data)):
            data = log_data[i:i+32]
            packet_start_flag = data.find(bytes(dm_packet_type))
            if packet_start_flag == 0:
                parse_data = data[8:-2]
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
                    print('error: Forced restart = 1')
                elif forced_restart_list[-1] == '0':
                    pass
                crc_err_list.append(dev_status_bin[23])
                tx_overflow_err_list.append(dev_status_bin[22])
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
        logf_name = f'./data/static_test_data/static_test_data_{self.test_time}.bin'
        #self.test_log.creat_binf_sct7(logf_name)

        if not os.path.exists(logf_name):
            self.static_test_setup()
            logf = open(logf_name, 'rb')
        else:
            logf = open(logf_name, 'rb')
        log_data = logf.read()
        dm_packet_type = [0x55, 0x55, 0x05, 0x0a]

        power_list = []
        mcu_list = []
        temp_u_mcu_list = []
        temp_u_sta_list = []
        temp_u_imu_list = []
        temp_o_mcu_list = []
        temp_o_sta_list = []
        temp_o_imu_list = []
        for i in range(len(log_data)):
            data = log_data[i:i+32]
            packet_start_flag = data.find(bytes(dm_packet_type))
            if packet_start_flag == 0:
                parse_data = data[8:-2]
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
                return False, f'Operation status error! Power fail={power_count}/{len(power_list)},mcu error={mcu_count}/{len(mcu_list)}\
,Temperature under MCU flag={temp_u_mcu_count}/{len(temp_u_mcu_list)},Temperature under STA flag={temp_u_sta_count}/{len(temp_u_sta_list)}\
,Temperature under IMU flag={temp_u_imu_count}/{len(temp_u_imu_list)},Temperature over MCU flag={temp_o_mcu_count}/{len(temp_o_mcu_list)}\
,Temperature over STA flag ={temp_o_sta_count}/{len(temp_o_sta_list)},Temperature over IMU flag={temp_o_imu_count}/{len(temp_o_imu_list)}'
            else:
                return True, 'IMU status is always 0', 'IMU status is always 0'

    ### section11 INS packet reasonable check (connect antenna)

    def IMU_data_packet_reasonable_check_week(self):
        logf_name = f'./data/static_test_data/static_test_data_{self.test_time}.bin'

        if not os.path.exists(logf_name):
            self.static_test_setup()
            logf = open(logf_name, 'rb')
        else:
            logf = open(logf_name, 'rb')
        log_data = logf.read()
        imu_packet_type = [0x55, 0x55, 0x01, 0x0a]

        imu_week_list = []
        imu_ms_list = []
        imu_gps_time = []
        unmatch_time_count = 0
        gps_signal_loss = 0
        for i in range(len(log_data)):
            data = log_data[i:i+40]
            packet_start_flag = data.find(bytes(imu_packet_type))
            if packet_start_flag == 0:
                parse_data = data[8:-2]
                fmt = '<HIffffff'
                parse_data_lst = struct.unpack(fmt, parse_data)
                imu_week_list.append(parse_data_lst[0])
                imu_ms_list.append(parse_data_lst[1])
        if len(imu_week_list) == 0:
            print('no Raw IMU packets!')

        for i in range(len(imu_week_list)):
            if imu_week_list[i] < 2232:
                gps_signal_loss = gps_signal_loss +1
            else:
                gps_sec = gps_time(imu_week_list[i], imu_ms_list[i]/1000)
                imu_gps_time.append(gps_sec)
                time_diff = cal_time_diff(gps_sec, REAL_CAP_START_TIME)
                #print(f'real time - gps time = {time_diff}')
                if time_diff > (0-i/100) or time_diff < (-2-i/100):
                    unmatch_time_count = unmatch_time_count + 1

        if len(imu_week_list) == 0:
            return False, f'no IMU packets', 'could capture IMU packets'
        else:
            if unmatch_time_count == 0 and gps_signal_loss != len(imu_week_list):
                return True, f'number of unmatch real time = {unmatch_time_count}/{len(imu_week_list)}, packets have gps time \
= {len(imu_week_list)-gps_signal_loss}/len(imu_week_list)', 'match real time <1s'
            elif unmatch_time_count == 0 and gps_signal_loss == len(imu_week_list):
                return False, f'packets have gps time = {len(imu_week_list)-gps_signal_loss}/{len(imu_week_list)}, DM packets \
= {len(imu_week_list)} ', 'at last one DM packet has GPS time'
            else:
                return False, f'number of unmatch real time = {unmatch_time_count}/{len(imu_week_list)}, no gps singal \
= {gps_signal_loss}/{len(imu_week_list)}', 'match real time, <1s'

    def IMU_data_packet_reasonable_check_ms(self):
        logf_name = f'./data/static_test_data/static_test_data_{self.test_time}.bin'

        if not os.path.exists(logf_name):
            self.static_test_setup()
            logf = open(logf_name, 'rb')
        else:
            logf = open(logf_name, 'rb')
        log_data = logf.read()
        imu_packet_type = [0x55, 0x55, 0x01, 0x0a]

        imu_week_list = []
        imu_ms_list = []
        neighbor_gps_pair = 0
        gps_signal_loss = 0
        num_interval_err = 0
        for i in range(len(log_data)):
            data = log_data[i:i+40]
            packet_start_flag = data.find(bytes(imu_packet_type))
            if packet_start_flag == 0:
                parse_data = data[8:-2]
                fmt = '<HIffffff'
                parse_data_lst = struct.unpack(fmt, parse_data)
                imu_week_list.append(parse_data_lst[0])
                imu_ms_list.append(parse_data_lst[1])
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
        logf_name = f'./data/static_test_data/static_test_data_{self.test_time}.bin'
        #self.test_log.creat_binf_sct7(logf_name)

        if not os.path.exists(logf_name):
            self.static_test_setup()
            logf = open(logf_name, 'rb')
        else:
            logf = open(logf_name, 'rb')
        log_data = logf.read()
        imu_packet_type = [0x55, 0x55, 0x01, 0x0a]

        imu_accel_x_list = []
        imu_accel_y_list = []
        imu_accel_z_list = []
        accel_mod_err_list = []
        for i in range(len(log_data)):
            data = log_data[i:i+40]
            packet_start_flag = data.find(bytes(imu_packet_type))
            if packet_start_flag == 0:
                parse_data = data[8:-2]
                fmt = '<HIffffff'
                parse_data_lst = struct.unpack(fmt, parse_data)
                imu_accel_x_list.append(parse_data_lst[2])
                imu_accel_y_list.append(parse_data_lst[3])
                imu_accel_z_list.append(parse_data_lst[4])
        if len(imu_accel_x_list) == 0:
            print('no Raw IMU packets!')

        for i in range(len(imu_accel_x_list)):
            s2 = math.pow(imu_accel_x_list[i],2) + math.pow(imu_accel_y_list[i],2) + math.pow(imu_accel_z_list[i],2)
            accel_mod_value = math.pow(s2, 1/2)
            #accel_mod_value = abs(imu_accel_x_list[i]) + abs(imu_accel_y_list[i]) + abs(imu_accel_z_list[i])
            if abs(accel_mod_value) < 9.7:
                print(f'error: sum<9.7 sum={accel_mod_value}={imu_accel_x_list[i]}+{imu_accel_y_list[i]}+{imu_accel_z_list[i]}')
                accel_mod_err_list.append([imu_accel_x_list[i],imu_accel_y_list[i],imu_accel_z_list[i]])
            elif abs(accel_mod_value) > 9.9:
                print(f'error: sum>9.9 sum={accel_mod_value}={imu_accel_x_list[i]}+{imu_accel_y_list[i]}+{imu_accel_z_list[i]}')
                accel_mod_err_list.append([imu_accel_x_list[i],imu_accel_y_list[i],imu_accel_z_list[i]])
            else:
                continue

        if len(imu_accel_x_list) == 0:
            return False, f'no Raw IMU packets', 'could capture Raw IMU packets'
        elif len(accel_mod_err_list) > 0:
            return False, f'accel mode is not 1g, err count={len(accel_mod_err_list)},total packets={len(imu_accel_x_list)}', 'accel of module is about 1g'
        else:
            return True, f'accel mode = 1g,total packets={len(imu_accel_x_list)}', 'accel of module is about 1g'

    def IMU_data_packet_reasonable_check_gyro(self):
        logf_name = f'./data/static_test_data/static_test_data_{self.test_time}.bin'
        #self.test_log.creat_binf_sct7(logf_name)

        if not os.path.exists(logf_name):
            self.static_test_setup()
            logf = open(logf_name, 'rb')
        else:
            logf = open(logf_name, 'rb')
        log_data = logf.read()
        imu_packet_type = [0x55, 0x55, 0x01, 0x0a]

        imu_gyro_x_list = []
        imu_gyro_y_list = []
        imu_gyro_z_list = []
        imu_gyro_err_list = []
        for i in range(len(log_data)):
            data = log_data[i:i+40]
            packet_start_flag = data.find(bytes(imu_packet_type))
            if packet_start_flag == 0:
                parse_data = data[8:-2]
                fmt = '<HIffffff'
                parse_data_lst = struct.unpack(fmt, parse_data)
                imu_gyro_x_list.append(parse_data_lst[5])
                imu_gyro_y_list.append(parse_data_lst[6])
                imu_gyro_z_list.append(parse_data_lst[7])
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

    ### section11 NMEA GNGGA

    def NMEA_GNGGA_data_packet_check_ID_GNGGA(self):
        logf_name = f'./data/static_test_data/static_test_data_{self.test_time}.bin'
        #self.test_log.creat_binf_sct7(logf_name)

        if not os.path.exists(logf_name):
            self.static_test_setup()
            logf = open(logf_name, 'rb')
        else:
            logf = open(logf_name, 'rb')
        log_data = logf.read()
        GNGGA_packet_type = [0x47, 0x4E, 0x47, 0x47, 0x41]

        gngga_list = []
        gngga_id_err_list = []
        for i in range(len(log_data)):
            data = log_data[i:i+83]
            packet_start_flag = data.find(bytes(GNGGA_packet_type))
            if packet_start_flag == 0:
                #parse_data = str(data[0:83], 'utf-8')
                parse_data = str(data[0:37], 'utf-8')
                gngga_list.append(parse_data)
                #print(parse_data)
        if len(gngga_list) == 0:
            print('no NMEA GNGGA packets!')

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
        logf_name = f'./data/static_test_data/static_test_data_{self.test_time}.bin'
        #self.test_log.creat_binf_sct7(logf_name)

        if not os.path.exists(logf_name):
            self.static_test_setup()
            logf = open(logf_name, 'rb')
        else:
            logf = open(logf_name, 'rb')
        log_data = logf.read()
        GNGGA_packet_type = [0x47, 0x4E, 0x47, 0x47, 0x41]

        gngga_utc_list = []
        gngga_utc_err_list = []
        unmatch_time_list = []
        for i in range(len(log_data)):
            data = log_data[i:i+83]
            packet_start_flag = data.find(bytes(GNGGA_packet_type))
            if packet_start_flag == 0:
                parse_data = str(data, 'utf-8')
                gngga_list = parse_data.split(",")
                gngga_utc_list.append(gngga_list[1])
        if len(gngga_utc_list) == 0:
            print('no NMEA GNGGA packets!')

        for i in range(len(gngga_utc_list)):
            hour = int(gngga_utc_list[i][0:2])
            minute = int(gngga_utc_list[i][2:4])
            second = int(gngga_utc_list[i][4:6])
            ms = int(gngga_utc_list[i][7:9])
            hour_real = REAL_CAP_START_TIME.hour
            minute_real = REAL_CAP_START_TIME.minute
            second_real = REAL_CAP_START_TIME.second
            microsec_real = REAL_CAP_START_TIME.microsecond
            time_diff = ((hour_real*3600)*1000+(minute_real*60+second_real)*1000+microsec_real/1000)-(((hour+8)*3600)*1000+(minute*60+second)*1000+ms*100)+i*1000
            #print(time_diff, '||', REAL_CAP_START_TIME, '|| ', hour, minute, second, ms)
            if abs(time_diff) < 1000:
                continue
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
        logf_name = f'./data/static_test_data/static_test_data_{self.test_time}.bin'
        #self.test_log.creat_binf_sct7(logf_name)

        if not os.path.exists(logf_name):
            self.static_test_setup()
            logf = open(logf_name, 'rb')
        else:
            logf = open(logf_name, 'rb')
        log_data = logf.read()
        GNGGA_packet_type = [0x47, 0x4E, 0x47, 0x47, 0x41]

        gngga_list = []
        unmatch_lat_list = []
        for i in range(len(log_data)):
            data = log_data[i:i+83]
            packet_start_flag = data.find(bytes(GNGGA_packet_type))
            if packet_start_flag == 0:
                packet_end_flag = data.find(bytes([0x2A]))
                if packet_end_flag > 0:
                    data_new = data[:packet_end_flag+3]
                    parse_data = str(data_new, 'utf-8')
                    gngga_list.append(parse_data)
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
        logf_name = f'./data/static_test_data/static_test_data_{self.test_time}.bin'
        #self.test_log.creat_binf_sct7(logf_name)

        if not os.path.exists(logf_name):
            self.static_test_setup()
            logf = open(logf_name, 'rb')
        else:
            logf = open(logf_name, 'rb')
        log_data = logf.read()
        GNGGA_packet_type = [0x47, 0x4E, 0x47, 0x47, 0x41]

        gngga_list = []
        unmatch_lat_list = []
        for i in range(len(log_data)):
            data = log_data[i:i+83]
            packet_start_flag = data.find(bytes(GNGGA_packet_type))
            packet_end_flag = data.find(bytes(0x2A))
            if packet_start_flag == 0:
                packet_end_flag = data.find(bytes([0x2A]))
                if packet_end_flag > 0:
                    data_new = data[:packet_end_flag+3]
                    parse_data = str(data_new, 'utf-8')
                    gngga_list.append(parse_data)
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
        logf_name = f'./data/static_test_data/static_test_data_{self.test_time}.bin'
        #self.test_log.creat_binf_sct7(logf_name)

        if not os.path.exists(logf_name):
            self.static_test_setup()
            logf = open(logf_name, 'rb')
        else:
            logf = open(logf_name, 'rb')
        log_data = logf.read()
        GNGGA_packet_type = [0x47, 0x4E, 0x47, 0x47, 0x41]

        gngga_list = []
        unmatch_pos_list = []
        for i in range(len(log_data)):
            data = log_data[i:i+83]
            packet_start_flag = data.find(bytes(GNGGA_packet_type))
            packet_end_flag = data.find(bytes(0x2A))
            if packet_start_flag == 0:
                packet_end_flag = data.find(bytes([0x2A]))
                if packet_end_flag > 0:
                    data_new = data[:packet_end_flag+3]
                    parse_data = str(data_new, 'utf-8')
                    gngga_list.append(parse_data)
        #self.uut.stop_listen_data()
        if len(gngga_list) == 0:
            print('no NMEA GNGGA packets!')

        for i in range(len(gngga_list)):
            gngga_position_type = get_position_type(gngga_list[i])
            #print(gngga_position_type)
            if gngga_position_type == position_type_p:
                continue
            else:
                unmatch_pos_list.append(gngga_position_type)
                print(f'error: pos = {gngga_position_type}')

        if len(gngga_list) == 0:
            return False, f'no NMEA GNGGA packets!', 'could capture NMEA GNGGA packets'
        elif len(unmatch_pos_list) > 0:
            return False, f'position type can not converges to 4, unmatch count={len(unmatch_pos_list)}/{len(gngga_list)}', 'position type in GNGGA can converges to 4'
        else:
            return True, f'position type in GNGGA can converges to 4', 'position type in GNGGA can converges to 4(RTK_fixed)'

    ### section12 NMEA GNZDA

    def NMEA_GNZDA_data_packet_check_ID_GNZDA(self):
        logf_name = f'./data/static_test_data/static_test_data_{self.test_time}.bin'
        #self.test_log.creat_binf_sct7(logf_name)

        if not os.path.exists(logf_name):
            self.static_test_setup()
            logf = open(logf_name, 'rb')
        else:
            logf = open(logf_name, 'rb')
        log_data = logf.read()
        GNZDA_packet_type = [0x47, 0x4E, 0x5A, 0x44, 0x41]

        gngga_list = []
        gngga_id_err_list = []
        for i in range(len(log_data)):
            data = log_data[i:i+37]
            packet_start_flag = data.find(bytes(GNZDA_packet_type))
            if packet_start_flag == 0:
                parse_data = str(data, 'utf-8')
                gngga_list.append(parse_data)
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
        logf_name = f'./data/static_test_data/static_test_data_{self.test_time}.bin'

        if not os.path.exists(logf_name):
            self.static_test_setup()
            logf = open(logf_name, 'rb')
        else:
            logf = open(logf_name, 'rb')
        log_data = logf.read()
        GNZDA_packet_type = [0x47, 0x4E, 0x5A, 0x44, 0x41]

        gngga_list = []
        unmatch_time_list = []
        for i in range(len(log_data)):
            data = log_data[i:i+37]
            packet_start_flag = data.find(bytes(GNZDA_packet_type))
            if packet_start_flag == 0:
                parse_data = str(data, 'utf-8')
                #gngga_list = parse_data.split(",")
                #gngga_utc_list.append(gngga_list[1])
                gngga_list.append(parse_data)
        if len(gngga_list) == 0:
            print('no NMEA GNZDA packets!')

        for i in range(len(gngga_list)):
            datetime_zda = get_zda_utc(gngga_list[i])
            #print(f'gnzda utc = {datetime_zda}')
            time_now = REAL_CAP_START_TIME
            #print(f'local time = {time_now}')
            time_diff = float(time_now.timestamp()) - datetime_zda.timestamp()
            #print(time_diff)
            if (-2-i) < time_diff < (0-i):
                continue
            else:
                unmatch_time_list.append(gngga_list[i])

        if len(gngga_list) == 0:
            return False, f'no NMEA GNZDA packets!', 'could capture NMEA GNZDA packets'
        elif len(unmatch_time_list) > 0:
            return False, f'UTC time do not matchs the real time, unmatch count={len(unmatch_time_list)}/{len(gngga_list)}', 'UTC time in GNZDA matchs the real time '
        else:
            return True, f'UTC time in GNZDA matchs the real time', 'UTC time in GNZDA matchs the real time'
