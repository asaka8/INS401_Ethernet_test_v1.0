import time
import struct
import io
import random
from tqdm import trange
from INS401_Ethernet import Ethernet_Dev
from Test_Logger import TestLogger
from Test_Cases import Test_Section
from Test_Cases import Test_Case
from Test_Cases import Code
from Test_Cases import Condition_Check
from Test_Cases import Condition_Check_dlc


INPUT_PACKETS = [b'\x01\xcc', b'\x02\xcc', b'\x03\xcc', b'\x04\xcc', b'\x05\xcc', b'\x06\xcc', b'\x01\x0b', b'\x02\x0b']
OTHER_OUTPUT_PACKETS = [b'\x01\n', b'\x02\n', b'\x03\n', b'\x04\n', b'\x05\n', b'\x06\n']

user_parameters = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
paramsId = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
random_parameters = [0.5, 1, 10, 10.5, 90, 180, -0.5, -1, -10, -10.5, -90, -180]
rtcm_data = [1, 2, 3, 4, 5, 6, 7, 8]
vehicle_speed_value = 80
LONGTERM_RUNNING_COUNT = 10000

output_time = []


# Add test scripts here
class Test_Scripts:
    uut = None

    def __init__(self, device):
        Test_Scripts.uut = device
    
    def hex_string(self, number_bytes = []):
        if number_bytes is None:
            return None
        return hex(int(struct.unpack('<H', number_bytes)[0]))
  
    def get_production_info(self):
        message_bytes = []
        command = INPUT_PACKETS[0]
        response = self.uut.write_read_response(command, message_bytes, 0.1)
        if(response[0] == command):
            return True, self.hex_string(response[0]), self.hex_string(command)
        else:
            return False, self.hex_string(response[0]), self.hex_string(command)
            
    def get_user_configuration_parameters(self):
        command = INPUT_PACKETS[1]
        result = False
        
        for field_id in range(12):
            message_bytes = []
            field_id_bytes = struct.pack('<I', field_id)
            message_bytes.extend(field_id_bytes)

            response = self.uut.write_read_response(command, message_bytes, 0.1)
            if(response[0] == command):
                reulst = True
            else:
                reulst = False
                break
 
        if(reulst):
            return True, self.hex_string(response[0]), self.hex_string(command)
        else:
            return False, self.hex_string(response[0]), self.hex_string(command)
                
    def set_user_configuration(self):
        command = INPUT_PACKETS[2]
        result = False
        
        for field_id in range(12):
            message_bytes = []
            field_id_bytes = struct.pack('<I', field_id)
            message_bytes.extend(field_id_bytes)

            if (field_id >= 0) and (field_id < 12):
                field_value_bytes = struct.pack('<f', user_parameters[field_id])
                message_bytes.extend(field_value_bytes)
                
            response = self.uut.write_read_response(command, message_bytes, 0.1)
            if(response[0] == command):
                reulst = True
            else:
                reulst = False
                break
                
        if(reulst):
            return True, self.hex_string(response[0]), self.hex_string(command)
        else:
            return False, self.hex_string(response[0]), self.hex_string(command)     
 
    def save_user_configuration(self):
        command = INPUT_PACKETS[3]
        message_bytes = []

        response = self.uut.write_read_response(command, message_bytes, 0.1)
        if(response[0] == command):
            return True, self.hex_string(response[0]), self.hex_string(command)
        else:
            return False, self.hex_string(response[0]), self.hex_string(command)

    def set_mount_angle_command(self):
        command = INPUT_PACKETS[4]
        message_bytes = []

        response = self.uut.write_read_response(command, message_bytes, 0.1)
        if(response[0] == command):
            return True, self.hex_string(response[0]), self.hex_string(command)
        else:
            return False, self.hex_string(response[0]), self.hex_string(command)
            
    def send_system_reset_command(self):
        command = INPUT_PACKETS[5]
        message_bytes = []

        response = self.uut.write_read_response(command, message_bytes, 0.1)
        if(response[0] == command):
            return True, self.hex_string(response[0]), self.hex_string(command)
        else:
            return False, self.hex_string(response[0]), self.hex_string(command)

    def set_base_rtcm_data(self):
        command = INPUT_PACKETS[6]
        message_bytes = []
        
        message_bytes.extend(rtcm_data)
        
        for i in range(10):
            self.uut.send_message(command, message_bytes)
            time.sleep(1)
        
        return True, self.hex_string(command), self.hex_string(command)
        
    def set_vehicle_speed_data(self):
        command = INPUT_PACKETS[7]
        message_bytes = []        

        field_value_bytes = struct.pack('<f', vehicle_speed_value)
        message_bytes.extend(field_value_bytes)
        
        self.uut.send_message(command, message_bytes)
        
        return True, self.hex_string(command), self.hex_string(command)
        
    def long_term_test(self):
        result = True
        command = INPUT_PACKETS[0]
        message_bytes = []
        
        # long term count manual setting
        result = self.uut.async_write_read(command, message_bytes, LONGTERM_RUNNING_COUNT)       
        if(result):
            return True, 'Non zero packets', 'Non zero packets'
        else:
            return False, 'Non zero packets', 'Non zero packets'
    
    def output_packet_callback(self, packet):
        output_time.append(time.time())
        pass
        
    def output_packet_raw_imu_data_test(self):
        global output_time     
        result = True
        command = OTHER_OUTPUT_PACKETS[0]
        
        cmd_type = struct.unpack('>H', command)[0]
        for i in range(10):
            output_time = []
            self.uut.read(2, cmd_type, self.output_packet_callback, 2)
            if(len(output_time) == 2):
                output_time_internal = output_time[1] - output_time[0]
                if(output_time_internal > 0.015):  #100Hz
                    print(output_time_internal)
                    result = False
                    break
            else:
                result = False
                break         
        
        if(result):
            return True, self.hex_string(command), self.hex_string(command)
        else:
            return False, self.hex_string(command), self.hex_string(command)


    def output_packet_gnss_solution_test(self):
        global output_time 
        
        result = True
        command = OTHER_OUTPUT_PACKETS[1]
        
        cmd_type = struct.unpack('>H', command)[0]
        for i in range(10):
            output_time = []
            self.uut.read(2, cmd_type, self.output_packet_callback, 2)
            if(len(output_time) == 2):
                output_time_internal = output_time[1] - output_time[0]
                if(output_time_internal > 1.2):
                    result = False
                    break
            else:
                result = False
                break      
        
        if(result):
            return True, self.hex_string(command), self.hex_string(command)
        else:
            return False, self.hex_string(command), self.hex_string(command)
            
    def output_packet_ins_solution_test(self):
        global output_time 
        
        result = True
        command = OTHER_OUTPUT_PACKETS[2]
        
        cmd_type = struct.unpack('>H', command)[0]
        for i in range(10):
            output_time = []
            self.uut.read(2, cmd_type, self.output_packet_callback, 2)
            if(len(output_time) == 2):
                output_time_internal = output_time[1] - output_time[0]
                if(output_time_internal > 0.015):   # 100HZ
                    print(output_time_internal)
                    result = False
                    break
            else:
                result = False
                break             
        
        if(result):
            return True, self.hex_string(command), self.hex_string(command)
        else:
            return False, self.hex_string(command), self.hex_string(command)  

    def output_packet_diagnostic_message_test(self):
        global output_time 
        
        result = True
        command = OTHER_OUTPUT_PACKETS[4]
        
        cmd_type = struct.unpack('>H', command)[0]
        for i in range(10):
            output_time = []
            self.uut.read(2, cmd_type, self.output_packet_callback, 3)
            if(len(output_time) == 2):
                output_time_internal = output_time[1] - output_time[0]
                if(output_time_internal > 1.2):
                    result = False
                    break
            else:
                result = False
                break      
        
        if(result):
            return True, self.hex_string(command), self.hex_string(command)
        else:
            return False, self.hex_string(command), self.hex_string(command)  

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

        if(result):
            return True, f'{val}', f'{get_params}'
        else:
            return False, f'{val}', f'{get_params}'

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
                params = random.choice(random_parameters)
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
            time.sleep(20)
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
    
#################################################

class Test_Environment:

    def __init__(self, device):
        self.scripts = Test_Scripts(device)
        self.test_sections = []

    # Add test scetions & test scripts here
    def setup_tests(self):

        section1 = Test_Section("ETHERNET Transaction Verification")
        self.test_sections.append(section1)
        section1.add_test_case(Code("get production test",  self.scripts.get_production_info))
        section1.add_test_case(Code("set user configuration test",self.scripts.set_user_configuration))
        section1.add_test_case(Code("get user configuration parameters test", self.scripts.get_user_configuration_parameters))
        section1.add_test_case(Code("save user configuration test",self.scripts.save_user_configuration))
        section1.add_test_case(Code("set mount angle test",self.scripts.set_mount_angle_command))
        section1.add_test_case(Code("set base rtcm data test", self.scripts.set_base_rtcm_data))
        section1.add_test_case(Code("set vehicle speed test", self.scripts.set_vehicle_speed_data))

        section2 = Test_Section("Output Packet Test")
        self.test_sections.append(section2)
        section2.add_test_case(Code("raw imu data test", self.scripts.output_packet_raw_imu_data_test))
        section2.add_test_case(Code("gnss solution test", self.scripts.output_packet_gnss_solution_test))
        section2.add_test_case(Code("ins solution test", self.scripts.output_packet_ins_solution_test))
        section2.add_test_case(Code("diagnostic message test", self.scripts.output_packet_diagnostic_message_test))

        section3 = Test_Section("ID setting valid or not without reset power")
        self.test_sections.append(section3)
        section3.add_test_case(Condition_Check("'gnss lever arm x' setting verify",  self.scripts.set_parameters_verify, paramsId[0], 0.5))
        section3.add_test_case(Condition_Check("'gnss lever arm y' setting verify",  self.scripts.set_parameters_verify, paramsId[1], 0.5))
        section3.add_test_case(Condition_Check("'gnss lever arm z' setting verify",  self.scripts.set_parameters_verify, paramsId[2], 0.5))
        section3.add_test_case(Condition_Check("'vrp lever arm x' setting verify",  self.scripts.set_parameters_verify, paramsId[3], -0.5))
        section3.add_test_case(Condition_Check("'vrp lever arm y' setting verify",  self.scripts.set_parameters_verify, paramsId[4], -0.5))
        section3.add_test_case(Condition_Check("'vrp lever arm z' setting verify",  self.scripts.set_parameters_verify, paramsId[5], -0.5))
        section3.add_test_case(Condition_Check("'user lever arm x' setting verify",  self.scripts.set_parameters_verify, paramsId[6], 0.5))
        section3.add_test_case(Condition_Check("'user lever arm y' setting verify",  self.scripts.set_parameters_verify, paramsId[7], 0.5))
        section3.add_test_case(Condition_Check("'user lever arm z' setting verify",  self.scripts.set_parameters_verify, paramsId[8], 0.5))
        section3.add_test_case(Condition_Check("'rotation rbvx' setting verify",  self.scripts.set_parameters_verify, paramsId[9], 180))
        section3.add_test_case(Condition_Check("'rotation rbvy' setting verify",  self.scripts.set_parameters_verify, paramsId[10], 180))
        section3.add_test_case(Condition_Check("'rotation rbvz' setting verify",  self.scripts.set_parameters_verify, paramsId[11], 180))
        
        section4 = Test_Section("ID setting valid or not with reset power")
        self.test_sections.append(section4)
        section4.add_test_case(Condition_Check_dlc("ID 1-3 setting random params test",  self.scripts.parameters_set_with_reset, paramsId[0]))
        section4.add_test_case(Condition_Check_dlc("ID 4-6 setting random params test",  self.scripts.parameters_set_with_reset, paramsId[3]))
        section4.add_test_case(Condition_Check_dlc("ID 7-9 setting random params test",  self.scripts.parameters_set_with_reset, paramsId[6]))
        section4.add_test_case(Condition_Check_dlc("ID 10-12 setting random params test",  self.scripts.parameters_set_with_reset, paramsId[9]))
        
        section5 = Test_Section("Longterm Test")
        self.test_sections.append(section5)
        section5.add_test_case(Code("Longterm Packet Test", self.scripts.long_term_test))
        section5.add_test_case(Condition_Check("ID 1-3 setting longterm test",  self.scripts.parameters_set_loop, paramsId[0], [0.3, 0]))
        section5.add_test_case(Condition_Check("ID 4-6 setting longterm test",  self.scripts.parameters_set_loop, paramsId[3], [-0.1, 0]))
        section5.add_test_case(Condition_Check("ID 7-9 setting longterm test",  self.scripts.parameters_set_loop, paramsId[6], [0.25, 0]))
        section5.add_test_case(Condition_Check("ID 10-12 setting longterm test",  self.scripts.parameters_set_loop, paramsId[9], [180, 0]))
        
        section6 = Test_Section("System Reset Test")
        self.test_sections.append(section6)
        section6.add_test_case(Code("System Reset Test", self.scripts.send_system_reset_command))

    def setup_tests_(self):
        '''for update
        '''
        section5 = Test_Section("Longterm Test")
        self.test_sections.append(section5)
        # section5.add_test_case(Code("Longterm Packet Test", self.scripts.long_term_test))
        section5.add_test_case(Condition_Check("ID 1-3 setting longterm test",  self.scripts.parameters_set_loop, paramsId[0], [0.3, 0]))
        section5.add_test_case(Condition_Check("ID 4-6 setting longterm test",  self.scripts.parameters_set_loop, paramsId[3], [-0.1, 0]))
        section5.add_test_case(Condition_Check("ID 7-9 setting longterm test",  self.scripts.parameters_set_loop, paramsId[6], [0.25, 0]))
        section5.add_test_case(Condition_Check("ID 10-12 setting longterm test",  self.scripts.parameters_set_loop, paramsId[9], [180, 0]))
        

    def run_tests(self):
        for section in self.test_sections:
            section.run_test_section()

    def print_results(self):
        print("Test Results:")
        for section in self.test_sections:
            print("Section " + str(section.section_id) + ": " + section.section_name + "\r\n")
            for test in section.test_cases:
                id = str(section.section_id) + "." + str(test.test_id)
                result_str = "Passed --> " if test.result['status'] else "Failed --x "
                print(result_str + id + " " + test.test_case_name + " Expected: "+ test.result['expected'] + " Actual: "+  test.result['actual'] + "\r\n")

    def _create_csv(self, file_name, fieldnames):
        with open(file_name, 'w+') as out_file:
            writer = csv.DictWriter(out_file, fieldnames = fieldnames)
            writer.writeheader()

    def log_results(self, file_name):
        logger = TestLogger(file_name)
        field_names = ['id', 'test_name', 'expected', 'actual', 'status']
        logger.create(field_names)
        for section in self.test_sections:
            for test in section.test_cases:
                logger.write_log(test.result)
