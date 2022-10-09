import os

from tqdm import trange
from ..test_framwork.Test_Logger import TestLogger
from ..test_framwork.Test_Cases import Test_Section
from ..test_framwork.Test_Cases import Test_Case
from ..test_framwork.Test_Cases import Code
from ..test_framwork.Test_Cases import Condition_Check
from ..test_framwork.Test_Cases import Condition_Check_dlc
from .INS401_Test_Function import Test_Scripts

paramsId = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]


class Test_Environment:

    def __init__(self, device):
        self.scripts = Test_Scripts(device)
        self.test_sections = []

    # Add test scetions & test scripts here
    def setup_tests(self):
        section1 = Test_Section("User command test")
        self.test_sections.append(section1)
        section1.add_test_case(Code("Get production test",  self.scripts.get_production_info))
        section1.add_test_case(Code("Check the separator in response of Ping message", self.scripts.info_separator_check))
        section1.add_test_case(Code("Get user configuration parameters test", self.scripts.get_user_configuration_parameters))
        section1.add_test_case(Code("Set user configuration parameters test", self.scripts.set_user_configuration))
        section1.add_test_case(Code("Save user configuration test", self.scripts.save_user_configuration))
        section1.add_test_case(Code("System reset test", self.scripts.send_system_reset_command))
        section1.add_test_case(Code("set base rtcm data test", self.scripts.set_base_rtcm_data)) # TODO: update
        section1.add_test_case(Code("set vehicle speed test", self.scripts.set_vehicle_speed_data)) # TODO: update

        section2 = Test_Section("Output packet test")
        self.test_sections.append(section2)
        section2.add_test_case(Code("Output rate of packet-GNSS solution binary packet", self.scripts.output_packet_gnss_solution_test))
        section2.add_test_case(Code("Output rate of packet-INS solution binary packet", self.scripts.output_packet_ins_solution_test))
        section2.add_test_case(Code("Output rate of packet-Diagnostic message binary packet", self.scripts.output_packet_diagnostic_message_test))
        section2.add_test_case(Code("Output rate of packet-IMU solution binary packet", self.scripts.output_packet_raw_imu_data_test))

        section3 = Test_Section("ID setting verification without restart")
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

        section4 = Test_Section("ID setting verification with repower")
        self.test_sections.append(section4)
        section4.add_test_case(Condition_Check_dlc("ID 1-3 setting random params test",  self.scripts.parameters_set_with_reset, paramsId[0]))
        section4.add_test_case(Condition_Check_dlc("ID 4-6 setting random params test",  self.scripts.parameters_set_with_reset, paramsId[3]))
        section4.add_test_case(Condition_Check_dlc("ID 7-9 setting random params test",  self.scripts.parameters_set_with_reset, paramsId[6]))
        section4.add_test_case(Condition_Check_dlc("ID 10-12 setting random params test",  self.scripts.parameters_set_with_reset, paramsId[9]))

        section5 = Test_Section("Longterm Test")
        self.test_sections.append(section5)
        section5.add_test_case(Code("Longterm Packet Test", self.scripts.long_term_test))
        section5.add_test_case(Code("time jump in GNSS Solution packets", self.scripts.gnss_solution_gps_time_jump_test))
        section5.add_test_case(Code("time jump in INS Solution packets", self.scripts.ins_solution_gps_time_jump_test))
        section5.add_test_case(Code("time jump in Diagnosis Message packets", self.scripts.dm_solution_gps_time_jump_test))
        section5.add_test_case(Code("time jump in raw IMU packets", self.scripts.imu_solution_gps_time_jump_test))
        section5.add_test_case(Condition_Check("ID 1-3 setting longterm test",  self.scripts.parameters_set_loop, paramsId[0], [0.3, 0]))
        section5.add_test_case(Condition_Check("ID 4-6 setting longterm test",  self.scripts.parameters_set_loop, paramsId[3], [-0.1, 0]))
        section5.add_test_case(Condition_Check("ID 7-9 setting longterm test",  self.scripts.parameters_set_loop, paramsId[6], [0.25, 0]))
        section5.add_test_case(Condition_Check("ID 10-12 setting longterm test",  self.scripts.parameters_set_loop, paramsId[9], [180, 0]))

        section6 = Test_Section("Vehicle code function test")
        self.test_sections.append(section6)
        section6.add_test_case(Condition_Check("VF33 setting test", self.scripts.vehicle_code_setting_test, paramsId[13], [0x56, 0x46, 0x33, 0x33]))
        section6.add_test_case(Condition_Check("VF34 setting test", self.scripts.vehicle_code_setting_test, paramsId[13], [0x56, 0x46, 0x33, 0x34]))
        section6.add_test_case(Condition_Check("VF35 setting test", self.scripts.vehicle_code_setting_test, paramsId[13], [0x56, 0x46, 0x33, 0x35]))
        section6.add_test_case(Condition_Check("VF36 setting test", self.scripts.vehicle_code_setting_test, paramsId[13], [0x56, 0x46, 0x33, 0x36]))
        section6.add_test_case(Condition_Check("VF33 vehicle code status test", self.scripts.vehicle_code_status_test, paramsId[13], [0x56 ,0x46, 0x33, 0x33]))
        section6.add_test_case(Condition_Check("VF34 vehicle code status test", self.scripts.vehicle_code_status_test, paramsId[13], [0x56, 0x46, 0x33, 0x34]))
        section6.add_test_case(Condition_Check("VF35 vehicle code status test", self.scripts.vehicle_code_status_test, paramsId[13], [0x56, 0x46, 0x33, 0x35]))
        section6.add_test_case(Condition_Check("VF36 vehicle code status test", self.scripts.vehicle_code_status_test, paramsId[13], [0x56, 0x46, 0x33, 0x36]))
        section6.add_test_case(Condition_Check("VF33 vehicle code setting params test", self.scripts.vehicle_code_params_test, paramsId[13], [0x56, 0x46, 0x33, 0x33]))
        section6.add_test_case(Condition_Check("VF34 vehicle code setting params test", self.scripts.vehicle_code_params_test, paramsId[13], [0x56, 0x46, 0x33, 0x34]))
        section6.add_test_case(Condition_Check("VF35 vehicle code setting params test", self.scripts.vehicle_code_params_test, paramsId[13], [0x56, 0x46, 0x33, 0x35]))
        section6.add_test_case(Condition_Check("VF36 vehicle code setting params test", self.scripts.vehicle_code_params_test, paramsId[13], [0x56, 0x46, 0x33, 0x36]))
        section6.add_test_case(Condition_Check_dlc("vehicle table version test", self.scripts.vehicle_table_version_test, 2))

    def setup_tests_(self):
        '''for update
        '''

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

    def log_results(self, file_name):
        logger = TestLogger(file_name)
        field_names = ['id', 'test_name', 'expected', 'actual', 'status']
        logger.create_csv(field_names)
        for section in self.test_sections:
            for test in section.test_cases:
                logger.write2csv(test.result)
