import os
import time
import struct
import random

from tqdm import trange
from ..conmunicator.INS401_Ethernet import Ethernet_Dev
from moudle.gps_time_module import get_curr_time, gps_time, cal_time_diff, stamptime_to_datetime
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
        logf_name = f'./data/Packet_long_term_test_data/long_terms_data_{self.test_time}.bin' 
        # logf_name = f'./data/Packet_long_term_test_data/long_terms_data_{self.test_time}.pcap' 
        self.test_log.cerat_binf_sct5(logf_name)
        start_time = time.time()
        self.uut.start_listen_data()
        self.uut.reset_buffer()        
        while time.time() - start_time <= longterm_run_time:
            data = self.uut.read_data()
            self.test_log.write2bin(data)
            # self.test_log.write2pcap(data, logf_name)
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

    def DM_packet_reasonable_check_week(self):
        result = False
        logf_name = f'./data/Packet_ODR_test_data/{self.product_sn}_{self.test_time}/DM_packet_week.bin'
        self.test_log.creat_binf_sct2(file_name=logf_name, sn_num=self.product_sn, test_time=self.test_time)
 
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
        logf_name = f'./data/Packet_ODR_test_data/{self.product_sn}_{self.test_time}/DM_packet_time_ms.bin'
        self.test_log.creat_binf_sct2(file_name=logf_name, sn_num=self.product_sn, test_time=self.test_time)
 
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
        logf_name = f'./data/Packet_ODR_test_data/{self.product_sn}_{self.test_time}/DM_packet_check_temp.bin'
        self.test_log.creat_binf_sct2(file_name=logf_name, sn_num=self.product_sn, test_time=self.test_time)
 
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
        logf_name = f'./data/Packet_ODR_test_data/{self.product_sn}_{self.test_time}/DM_packet_check_status_gnss.bin'
        self.test_log.creat_binf_sct2(file_name=logf_name, sn_num=self.product_sn, test_time=self.test_time)
 
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
        logf_name = f'./data/Packet_ODR_test_data/{self.product_sn}_{self.test_time}/DM_packet_check_status_imu.bin'
        self.test_log.creat_binf_sct2(file_name=logf_name, sn_num=self.product_sn, test_time=self.test_time)
 
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
        logf_name = f'./data/Packet_ODR_test_data/{self.product_sn}_{self.test_time}/DM_packet_check_status_operation.bin'
        self.test_log.creat_binf_sct2(file_name=logf_name, sn_num=self.product_sn, test_time=self.test_time)
 
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

    
        