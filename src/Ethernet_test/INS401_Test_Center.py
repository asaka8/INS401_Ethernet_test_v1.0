from ..test_framwork.Test_Logger import TestLogger
from ..test_framwork.Test_Cases import Test_Section
from ..test_framwork.Test_Cases import Code
from ..test_framwork.Test_Cases import Condition_Check
from ..test_framwork.Test_Cases import Condition_Check_dlc
from ..test_framwork.Jsonf_Creater import Json_Creat
from .INS401_Test_Function import Test_Scripts

class Test_Environment:

    def __init__(self, device):
        self.scripts = Test_Scripts(device)
        self.test_sections = []
        json_f = Json_Creat()
        self.properties = json_f.creat()
        self.paramIds = []
        self.values = []
        for i in self.properties["userId"]:
            paramsId = i["ID"]
            value = i["value"]
            self.paramIds.append(paramsId)
            self.values.append(value)

    # Add test scetions & test scripts here
    def setup_tests_(self):
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
        section3.add_test_case(Condition_Check("'gnss lever arm x' setting verify",  self.scripts.set_parameters_verify, self.paramIds[0], self.values[0]))
        section3.add_test_case(Condition_Check("'gnss lever arm y' setting verify",  self.scripts.set_parameters_verify, self.paramIds[1], self.values[1]))
        section3.add_test_case(Condition_Check("'gnss lever arm z' setting verify",  self.scripts.set_parameters_verify, self.paramIds[2], self.values[2]))
        section3.add_test_case(Condition_Check("'vrp lever arm x' setting verify",  self.scripts.set_parameters_verify, self.paramIds[3], self.values[3]))
        section3.add_test_case(Condition_Check("'vrp lever arm y' setting verify",  self.scripts.set_parameters_verify, self.paramIds[4], self.values[4]))
        section3.add_test_case(Condition_Check("'vrp lever arm z' setting verify",  self.scripts.set_parameters_verify, self.paramIds[5], self.values[5]))
        section3.add_test_case(Condition_Check("'user lever arm x' setting verify",  self.scripts.set_parameters_verify, self.paramIds[6], self.values[6]))
        section3.add_test_case(Condition_Check("'user lever arm y' setting verify",  self.scripts.set_parameters_verify, self.paramIds[7], self.values[7]))
        section3.add_test_case(Condition_Check("'user lever arm z' setting verify",  self.scripts.set_parameters_verify, self.paramIds[8], self.values[8]))
        section3.add_test_case(Condition_Check("'rotation rbvx' setting verify",  self.scripts.set_parameters_verify, self.paramIds[9], self.values[9]))
        section3.add_test_case(Condition_Check("'rotation rbvy' setting verify",  self.scripts.set_parameters_verify, self.paramIds[10], self.values[10]))
        section3.add_test_case(Condition_Check("'rotation rbvz' setting verify",  self.scripts.set_parameters_verify, self.paramIds[11], self.values[11]))

        section4 = Test_Section("ID setting verification with repower")
        self.test_sections.append(section4)
        section4.add_test_case(Condition_Check_dlc("ID 1-3 setting random params test",  self.scripts.parameters_set_with_reset, self.paramIds[0]))
        section4.add_test_case(Condition_Check_dlc("ID 4-6 setting random params test",  self.scripts.parameters_set_with_reset, self.paramIds[3]))
        section4.add_test_case(Condition_Check_dlc("ID 7-9 setting random params test",  self.scripts.parameters_set_with_reset, self.paramIds[6]))
        section4.add_test_case(Condition_Check_dlc("ID 10-12 setting random params test",  self.scripts.parameters_set_with_reset, self.paramIds[9]))

        section5 = Test_Section("Longterm Test")
        self.test_sections.append(section5)
        section5.add_test_case(Code("Longterm Packet Test", self.scripts.long_term_test))
        section5.add_test_case(Code("time jump in GNSS Solution packets", self.scripts.gnss_solution_gps_time_jump_test))
        section5.add_test_case(Code("time jump in INS Solution packets", self.scripts.ins_solution_gps_time_jump_test))
        section5.add_test_case(Code("time jump in Diagnosis Message packets", self.scripts.dm_solution_gps_time_jump_test))
        section5.add_test_case(Code("time jump in raw IMU packets", self.scripts.imu_solution_gps_time_jump_test))
        section5.add_test_case(Condition_Check("ID 1-3 setting longterm test",  self.scripts.parameters_set_loop, self.paramIds[0], [0.3, 0]))
        section5.add_test_case(Condition_Check("ID 4-6 setting longterm test",  self.scripts.parameters_set_loop, self.paramIds[3], [-0.1, 0]))
        section5.add_test_case(Condition_Check("ID 7-9 setting longterm test",  self.scripts.parameters_set_loop, self.paramIds[6], [0.25, 0]))
        section5.add_test_case(Condition_Check("ID 10-12 setting longterm test",  self.scripts.parameters_set_loop, self.paramIds[9], [180, 0]))

        section6 = Test_Section("Vehicle code function test")
        self.test_sections.append(section6)
        section6.add_test_case(Condition_Check("VF33 setting test", self.scripts.vehicle_code_setting_test, self.paramIds[13], [0x56, 0x46, 0x33, 0x33]))
        section6.add_test_case(Condition_Check("VF34 setting test", self.scripts.vehicle_code_setting_test, self.paramIds[13], [0x56, 0x46, 0x33, 0x34]))
        section6.add_test_case(Condition_Check("VF35 setting test", self.scripts.vehicle_code_setting_test, self.paramIds[13], [0x56, 0x46, 0x33, 0x35]))
        section6.add_test_case(Condition_Check("VF36 setting test", self.scripts.vehicle_code_setting_test, self.paramIds[13], [0x56, 0x46, 0x33, 0x36]))
        section6.add_test_case(Condition_Check("VF33 vehicle code status test", self.scripts.vehicle_code_status_test, self.paramIds[13], [0x56 ,0x46, 0x33, 0x33]))
        section6.add_test_case(Condition_Check("VF34 vehicle code status test", self.scripts.vehicle_code_status_test, self.paramIds[13], [0x56, 0x46, 0x33, 0x34]))
        section6.add_test_case(Condition_Check("VF35 vehicle code status test", self.scripts.vehicle_code_status_test, self.paramIds[13], [0x56, 0x46, 0x33, 0x35]))
        section6.add_test_case(Condition_Check("VF36 vehicle code status test", self.scripts.vehicle_code_status_test, self.paramIds[13], [0x56, 0x46, 0x33, 0x36]))
        section6.add_test_case(Condition_Check("VF33 vehicle code setting params test", self.scripts.vehicle_code_params_test, self.paramIds[13], [0x56, 0x46, 0x33, 0x33]))
        section6.add_test_case(Condition_Check("VF34 vehicle code setting params test", self.scripts.vehicle_code_params_test, self.paramIds[13], [0x56, 0x46, 0x33, 0x34]))
        section6.add_test_case(Condition_Check("VF35 vehicle code setting params test", self.scripts.vehicle_code_params_test, self.paramIds[13], [0x56, 0x46, 0x33, 0x35]))
        section6.add_test_case(Condition_Check("VF36 vehicle code setting params test", self.scripts.vehicle_code_params_test, self.paramIds[13], [0x56, 0x46, 0x33, 0x36]))
        section6.add_test_case(Condition_Check_dlc("vehicle table version test", self.scripts.vehicle_table_version_test, self.properties["vehicle code"]["vcode version"]))

        section9 = Test_Section("DM packet reasonable check")
        self.test_sections.append(section9)
        section9.add_test_case(Code("week", self.scripts.DM_packet_reasonable_check_week))
        section9.add_test_case(Code("time ms", self.scripts.DM_packet_reasonable_check_time_ms))
        section9.add_test_case(Code("check temperature", self.scripts.DM_packet_reasonable_check_temp))
        section9.add_test_case(Code("check GNSS status", self.scripts.DM_packet_reasonable_check_status_gnss))
        section9.add_test_case(Code("check IMU status", self.scripts.DM_packet_reasonable_check_status_imu))
        section9.add_test_case(Code("check Operation status", self.scripts.DM_packet_reasonable_check_status_operation))

        section10 = Test_Section("Raw IMU packet reasonable check")
        self.test_sections.append(section10)
        section10.add_test_case(Code("check gps week", self.scripts.IMU_data_packet_reasonable_check_week))
        section10.add_test_case(Code("check gps ms", self.scripts.IMU_data_packet_reasonable_check_ms))
        section10.add_test_case(Code("check accel", self.scripts.IMU_data_packet_reasonable_check_accel))
        section10.add_test_case(Code("check accel", self.scripts.IMU_data_packet_reasonable_check_gyro))

        section11 = Test_Section("NMEA-GNGGA check")
        self.test_sections.append(section11)
        section11.add_test_case(Code("check ID GNGGA", self.scripts.NMEA_GNGGA_data_packet_check_ID_GNGGA))
        section11.add_test_case(Code("check UTC time", self.scripts.NMEA_GNGGA_data_packet_check_utc_time))
        section11.add_test_case(Code("check latitude", self.scripts.NMEA_GNGGA_data_packet_check_latitude))
        section11.add_test_case(Code("check longitude", self.scripts.NMEA_GNGGA_data_packet_check_longitude))
        section11.add_test_case(Code("check position type", self.scripts.NMEA_GNGGA_data_packet_check_position_type))

    def setup_tests(self):
        '''for update
        '''
        section5 = Test_Section("Longterm Test")
        self.test_sections.append(section5)
        section5.add_test_case(Code("Longterm setup Test", self.scripts.long_term_test_setup))

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
