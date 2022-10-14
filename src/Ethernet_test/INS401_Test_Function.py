import os
import time
import struct
import random

from tqdm import trange
from ..conmunicator.INS401_Ethernet import Ethernet_Dev
from moudle.gps_time_module import gps_time
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
        self.test_log.cerat_binf_sct5(logf_name)
        start_time = time.time()
        self.uut.start_listen_data()
        self.uut.reset_buffer()        
        while time.time() - start_time <= longterm_run_time:
            data = self.uut.read_data()
            if data is not None:
                self.test_log.write2bin(data)
        self.uut.check_len()
        self.uut.stop_listen_data()
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