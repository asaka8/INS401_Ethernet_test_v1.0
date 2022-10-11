
#include "stdio.h"
#include "stdlib.h"
#include "string.h"
#include "io.h"
#include "DateTime.h"
#include <stdint.h>
#include <time.h>
#include <windows.h>
#include "INS401.h"
#include "cJSON.h"


int main(int argc, char* argv[])
{
	char address[500];
	uint8_t* data_buf;
	int lenth;
	FILE* fp;
	char* arry[2] = { "-static","-dynamic" };

	if (argc >= 2)
	{
		strcpy(addr_input, argv[1]);
		Init_Verify(addr_input);

		/*
		* TODO:需要把静态动态分离 做成两个链接库 可在编译时
		* 加入宏定义，或整体分离
		*/

#ifdef STATIC_TEST
		if (argc >= 3)
		{
			if (!strcmp(argv[2], arry[1]))
			{
				accel_min = 9.0;
				accel_max = 11.0;
				latitude_min = 29.5;
				latitude_max = 33.5;
				longitude_min = 118.0;
				longitude_max = 122.0;
			}
#endif

#ifdef DYNAMIC_TEST
			else if (!strcmp(argv[2], arry[1]))
			{
				accel_min = -210.0;
				accel_max = 210.0;
				latitude_min = 0.0;
				latitude_max = 180.0;
				longitude_min = 0.0;
				longitude_max = 180.0;
			}
		}
#endif

		sprintf(address, addr_input);
		fp = fopen(address, "rb+");

		fseek(fp, 0, SEEK_END);

		lenth = ftell(fp);
		if (fp == NULL || lenth == 0)
		{
			printf("file error!\n");
			return 0;
		}
		data_buf = (uint8_t*)malloc(lenth);

		fseek(fp, 0, SEEK_SET);
		if(data_buf)
			fread(data_buf, 1, lenth, fp);
		INS401Data_Prase(data_buf, lenth);

		INS401Data_result();

		fclose(fp);

		//Rtk330Data_status_error_cnt();
		printf("done\nresult is print in the same folder of bin file\n");
		return 0;
	}
	else
	{
		printf("work in command line interface\nformat:\n");
		printf("programe.exe [address of user.bin] [-static or -dynamic]\n");
		lenth = getchar();
		return 0;
	}
}

/*************************************************
* @brief    初始化 需要文件权限
* @param	[in] uint8_t * file_input_addr	 输入数据的路径字符串指针
* @retval	0 初始化成功
*************************************************/
int Init_Verify(uint8_t *file_input_addr)
{
	char drive_file[_MAX_DRIVE];
	char dir_file[_MAX_DIR];
	char fname_file[_MAX_FNAME];
	char ext_file[_MAX_EXT];
	char addr_folder_input[500] = { 0 };
	char command_dir[500] = { 0 };
	char* json_buf;
	int length;

	time(&times);

	if (times > INT32_MAX)
	{
		utctime = GregorianCalendarDateAddSecond(utctime, INT32_MAX);
		utctime = GregorianCalendarDateAddSecond(utctime, (int)(times - INT32_MAX));
	}
	else
	{
		utctime = GregorianCalendarDateAddSecond(utctime, (int)times);
	}

	mjd = GregorianCalendarDateToModifiedJulianDate(utctime);
	local_time = GregorianCalendarDateAddHour(utctime, 8);
	gpstime = GregorianCalendarDateAddSecond(utctime, 18);
	gpstimews = GregorianCalendarDateToGpsWeekSecond(gpstime);


	_splitpath(file_input_addr, drive_file, dir_file, fname_file, ext_file);
	_makepath(addr_folder_input, drive_file, dir_file, "", "");
	_makepath(addr_output, drive_file, dir_file, fname_file, "");
	strcat(addr_output, "_t");
	strcat(addr_output_packet, addr_output);
	strcat(addr_output_packet, "\\packet_data");
	strcat(command_dir, "md ");
	strcat(command_dir, addr_output);
	if (_access(addr_output, 0) == -1)
		system(command_dir);
	memset(command_dir, 0, sizeof(command_dir));
	strcat(command_dir, "md ");
	strcat(command_dir, addr_output_packet);
	if (_access(addr_output_packet, 0) == -1)
		system(command_dir);

	memset(addr_output_success, 0x00, sizeof(addr_output_success));
	memset(addr_output_error, 0x00, sizeof(addr_output_error));
	memset(addr_status, 0x00, sizeof(addr_status));
	strcat(addr_output_success, addr_output_packet);
	strcat(addr_output_success, "\\success_packet.txt");
	strcat(addr_output_error, addr_output_packet);
	strcat(addr_output_error, "\\error_packet.txt");
	//strcat(addr_status, addr_output);
	//strcat(addr_status, "\\error_status.txt");
	strcat(addr_output_error_csv, addr_output);
	strcat(addr_output_error_csv, "\\error_packet.csv");
	strcat(addr_status_error_csv, addr_output);
	strcat(addr_status_error_csv, "\\error_status.csv");
	strcat(addr_status_csv, addr_output);
	strcat(addr_status_csv, "\\status_parse.csv");
	strcat(addr_configuration, addr_folder_input);
	strcat(addr_configuration, "\\configuration.json");
	strcat(addr_device_info, addr_output);
	strcat(addr_device_info, "\\device_info.txt");
	strcat(addr_decode_log, addr_output);
	strcat(addr_decode_log, "\\decode_log.txt");

	FILE* fp = fopen(addr_output_success, "w");
	FILE* fp2 = fopen(addr_output_error, "w");

	fclose(fp);
	fclose(fp2);
	fp = fopen(addr_decode_log, "w");
	fclose(fp);
	/*fp = fopen(addr_status, "w");
	fclose(fp);*/

	fp = fopen(addr_output_error_csv, "w");
	fclose(fp);
	fp = fopen(addr_status_error_csv, "w");
	fclose(fp);
	fp = fopen(addr_status_csv, "w");
	fprintf(fp, "gps_week ,gps_time ,");
	fprintf(fp, "master_fail ,hw_error ,sw_error ,config_error ,calibration_error ,accel_degradation ,");
	fprintf(fp, "gyro_degradation ,forced_restart ,CRC_error ,tx_overflow_error ,pps_status ,gnss_data_status ,");
	fprintf(fp, "gnss_signal_status ,power ,mcu_status ,temperature_under_mcu_flag ,temperature_under_sta_flag ,temperature_under_imu_flag ,");
	fprintf(fp, "temperature_over_mcu_flag ,temperature_over_sta_flag ,temperature_over_imu_flag \n");
	fclose(fp);

	fp = fopen(addr_configuration, "r");
	if (fp != NULL)
	{
		cJSON* json, * json_firmware_version, * json_name, * json_sn;
		cJSON* json2, * json3;
		cJSON* json_time,* json_parameters ,* json_rbvx, * json_rbvy, * json_rbvz;
		int ret;

		fp2 = fopen(addr_device_info, "w");

		fseek(fp, 0, SEEK_END);

		length = ftell(fp);

		json_buf = (uint8_t*)malloc(length);

		fseek(fp, 0, SEEK_SET);
		if(json_buf)
			fread(json_buf, 1, length, fp);

		fclose(fp);

		json = cJSON_Parse(json_buf);

		json2 = cJSON_GetArrayItem(json,0);

		json_time = cJSON_GetArrayItem(json2, 0);

		ret=sscanf(json_time->valuestring, "%d-%d-%d %d:%d:%d", &local_time.year, &local_time.month, &local_time.day, &local_time.hour, &local_time.minute, &local_time.second);
		utctime = GregorianCalendarDateAddHour(local_time, -8);
		gpstime = GregorianCalendarDateAddSecond(utctime, 18);
		gpstimews = GregorianCalendarDateToGpsWeekSecond(gpstime);

		config_time_flag = 1;

		json_parameters = cJSON_GetArrayItem(json2, 5);

		//if (json_parameters)
		{
			json_rbvx = cJSON_GetArrayItem(json_parameters, 13);
			json_rbvy = cJSON_GetArrayItem(json_parameters, 14);
			json_rbvz = cJSON_GetArrayItem(json_parameters, 15);
		}

		json3 = cJSON_GetArrayItem(json2, 1);

		json_name = cJSON_GetObjectItem(json3, "name");
		json_sn = cJSON_GetObjectItem(json3, "sn");

		json3 = cJSON_GetArrayItem(json2, 2);
		json_firmware_version = cJSON_GetObjectItem(json3, "firmware");

		fprintf(fp2, "time : %s\n", json_time->valuestring);
		fprintf(fp2, "device name : %s\n", json_name->valuestring);
		fprintf(fp2, "firmware version : %s\n", json_firmware_version->valuestring);
		fprintf(fp2, "sn : %s\n", json_sn->valuestring);

		if(0)// (json_parameters)
		{
			fprintf(fp2, "rotation rbvx : %f\n", json_rbvx->valuedouble);
			fprintf(fp2, "rotation rbvy : %f\n", json_rbvy->valuedouble);
			fprintf(fp2, "rotation rbvz : %f\n", json_rbvz->valuedouble);
		}
		fclose(fp2);

		if (json)
			cJSON_Delete(json);
	}

	memset(&status_error, 0, sizeof(status_error));

	accel_min = 9.0;
	accel_max = 11.0;
	latitude_min = 29.5;
	latitude_max = 33.5;
	longitude_min = 118.0;
	longitude_max = 122.0;

	return 0;
}

/*************************************************
* @brief    根据输入的CMD判断是否为已知的命令
* @param	[in] uint16_t MsgTyoe 2字节CMD Little End
* @retval	FDC_FALSE 未知命令
* @retval	FDC_TRUE 已知命令
*************************************************/
int INS401Data_SearchCmd(uint16_t MsgType)
{
	int 	 ret = FDC_FALSE;
	uint32_t i = 0;

	for (i = 0; i < ETH_TOTAL_CMD; i++)
	{
		if (EthCmd_List[i].MsgCmd == MsgType)
		{
			MsgTypeRst |= 1 << i;			/**< use to record Spi Msg type **/
			ret = FDC_TRUE;
			break;
		}
	}
	return ret;
}

/*************************************************
* @brief    计算CRC16 使用查表法
* @param	[in] uint8_t *buf	输入的数据指针
* @param	[in] uint16_t length	输入的数据长度
* @return	CRC16	Big End
*************************************************/
uint16_t CalculateCRC(uint8_t* buf, uint16_t  length)
{
	uint16_t crc = 0x1D0F;  //non-augmented inital value equivalent to the augmented initial value 0xFFFF

	for (int i = 0; i < length; i++)
	{
		crc ^= buf[i] << 8;

		for (int j = 0; j < 8; j++)
		{
			if (crc & 0x8000)
			{
				crc = (crc << 1) ^ 0x1021;
			}
			else
			{
				crc = crc << 1;
			}
		}
	}

	return ((crc << 8) & 0xFF00) | ((crc >> 8) & 0xFF);
}

/*************************************************
* @brief    计算各CMD包解包次数存入结构体
* @param	[in] uint16_t MsgType	输入的CMD        
* @return	None
*************************************************/
void INS401Data_PakCnt(uint16_t MsgType)
{
	switch (MsgType)
	{
	case MSG_TYPE_IMU:
		MsgCount.IMU_Count++;
		break;
	case MSG_TYPE_odo:
		MsgCount.odo_Count++;
		break;
	case MSG_TYPE_INS:
		MsgCount.INS_Count++;
		break;
	case MSG_TYPE_GNSS:
		MsgCount.GNSS_Count++;
		break;
	case MSG_TYPE_DM:
		MsgCount.DM_Count++;
		break;
	default:
		/** do nothing **/
		break;
	}
}

/*************************************************
* @brief    解包status_bits存入结构体
* @param	[in] uint32_t status	 status_bits
* @return	None
*************************************************/
void int2status(uint32_t status)
{

	all_status_cnt++;
	memcpy(&ins401_status, &status, sizeof(uint32_t));
	if (ins401_status.master_fail != 0)
		status_error.master_fail++;
	if (ins401_status.hw_error != 0)
		status_error.hw_error++;
	if (ins401_status.sw_error != 0)
		status_error.sw_error++;
	if (ins401_status.config_error != 0)
		status_error.config_error++;
	if (ins401_status.calibration_error != 0)
		status_error.calibration_error++;
	if (ins401_status.accel_degradation != 0)
		status_error.accel_degradation++;
	if (ins401_status.gyro_degradation != 0)
		status_error.gyro_degradation++;
	if (ins401_status.forced_restart != 0)
		status_error.forced_restart++;
	if (ins401_status.CRC_error != 0)
		status_error.CRC_error++;
	if (ins401_status.tx_overflow_error != 0)
		status_error.tx_overflow_error++;
	if (ins401_status.pps_status != 0)
		status_error.pps_status++;
	if (ins401_status.gnss_data_status != 0)
		status_error.gnss_data_status++;

	if (ins401_status.gnss_signal_status != 0)
		status_error.gnss_signal_status++;
	if (ins401_status.power != 0)
		status_error.power++;
	if (ins401_status.mcu_status != 0)
		status_error.mcu_status++;
	if (ins401_status.temperature_under_mcu_flag != 0)
		status_error.temperature_under_mcu_flag++;
	if (ins401_status.temperature_under_sta_flag != 0)
		status_error.temperature_under_sta_flag++;
	if (ins401_status.temperature_under_imu_flag != 0)
		status_error.temperature_under_imu_flag++;
	if (ins401_status.temperature_over_mcu_flag != 0)
		status_error.temperature_over_mcu_flag++;
	if (ins401_status.temperature_over_sta_flag != 0)
		status_error.temperature_over_sta_flag++;
	if (ins401_status.temperature_over_imu_flag != 0)
		status_error.temperature_over_imu_flag++;

	memset(&ins401_status, 0, sizeof(uint32_t));

}

/*************************************************
* @brief    解包status_bits存入CSV文件
* @param	[in] uint32_t status	 status_bits
* @return	None
*************************************************/
void int2status_file(uint32_t status)
{

	FILE* fp2 = fopen(addr_status_csv, "a");
	if (fp2 == NULL)
		return;

	memcpy(&ins401_status, &status, sizeof(uint32_t));

	fprintf(fp2, "%d\t,%f\t,", sT_gps_week, sT_gps_time_of_week_s);
	fprintf(fp2, "%d\t,%d\t,%d\t,%d\t,%d\t,%d\t,", ins401_status.master_fail, ins401_status.hw_error, ins401_status.sw_error,
		ins401_status.config_error, ins401_status.calibration_error, ins401_status.accel_degradation);
	fprintf(fp2, "%d\t,%d\t,%d\t,%d\t,%d\t,%d\t,", ins401_status.gyro_degradation, ins401_status.forced_restart, ins401_status.CRC_error,
		ins401_status.tx_overflow_error, ins401_status.pps_status, ins401_status.gnss_data_status);
	fprintf(fp2, "%d\t,%d\t,%d\t,%d\t,%d\t,%d\t,", ins401_status.gnss_signal_status, ins401_status.power, ins401_status.mcu_status,
		ins401_status.temperature_under_mcu_flag, ins401_status.temperature_under_sta_flag, ins401_status.temperature_under_imu_flag);
	fprintf(fp2, "%d\t,%d\t,%d\t\n", ins401_status.temperature_over_mcu_flag, ins401_status.temperature_over_sta_flag, ins401_status.temperature_over_imu_flag);

	memset(&ins401_status, 0, sizeof(uint32_t));
	fclose(fp2);

}

/*************************************************
* @brief    对包数据进行合理性校验
* @param	[in] stRtkMsg* Buff  包数据结构体
* @retval	0 校验成功
* @retval	其他值 检验失败
* @note		根据data bin同级文件夹下是否有configuration.json
*			判断是否能读到测试的准确时间，有准确时间看准确时间
*			没准确时间看是否与现在的时间差超过一年
*************************************************/
int INS401Data_Verify(void* Buff)
{
	stRtkMsg data = *(stRtkMsg *)Buff;
	int flag = 1;
	uint16_t gps_week;
	uint32_t gps_time_of_week_s;
	float x_accel;
	float y_accel;
	float z_accel;
	float x_gyro;
	float y_gyro;
	float z_gyro;
	float vehicle_speed;
	uint8_t ins_status;
	uint8_t ins_position_type;
	double latitude, longitude;
	double height;
	float north_velocity, east_velocity, up_velocity;
	float longitudinal_velocity, lateral_velocity;
	float roll, pitch, heading;
	float latitude_std, longitude_std, height_std;
	float north_velocity_std, east_velocity_std, up_velocity_std;
	float long_vel_std, lat_vel_std, roll_std, pitch_std, heading_std;
	uint16_t continent_ID;
	uint8_t position_type,numberOfSVs,numberOfSVs_in_solution;
	float hdop, diffage;
	float imu_temperature, mcu_temperature, sta_temperature;

	uint32_t status_bit;
	uint16_t msg_type;
	
	msg_type = data.code_MSB << 8 | data.code_LSB;
	INS401Data_PakCnt(msg_type);

	switch (msg_type)
	{
	case MSG_TYPE_IMU:
		if (data.payloadLength_c != 0)
		{
			memcpy(&gps_week, data.payload, 2);
			memcpy(&gps_time_of_week_s, data.payload + 2, 4);
			memcpy(&x_accel, data.payload + 6, 4);
			memcpy(&y_accel, data.payload + 10, 4);
			memcpy(&z_accel, data.payload + 14, 4);
			memcpy(&x_gyro, data.payload + 18, 4);
			memcpy(&y_gyro, data.payload + 22, 4);
			memcpy(&z_gyro, data.payload + 26, 4);

			IMU_gps_week = gps_week;
			IMU_gps_time_of_week_s = (double)gps_time_of_week_s / 1000;
			if (IMU_gps_time_of_week_s > IMU_gps_time_of_week_s_last_second)
			{
				if (IMU_gps_week_last_second != 0 && IMU_gps_time_of_week_s_last_second != 0 && (IMU_gps_time_of_week_s - IMU_gps_time_of_week_s_last_second) >= 0.02)
					flag = 6;
			}
			else
			{
				flag = 5;
			}
			IMU_gps_time_of_week_s_last_second = IMU_gps_time_of_week_s;
			IMU_gps_week_last_second = IMU_gps_week;

			if (!config_time_flag)
			{
				if (abs(gps_week) >= abs(gpstimews.week - 50))
				{
					if (((x_accel * x_accel) + (y_accel * y_accel) + (z_accel * z_accel)) >= (accel_min * accel_min)
						&& ((x_accel * x_accel) + (y_accel * y_accel) + (z_accel * z_accel)) <= (accel_max * accel_max))
					{
						if (x_gyro <= 5 && y_gyro <= 5 && z_gyro <= 5)
						{
							flag = 0;
						}
						else {
							flag = 4;
						}
					}
					else {
						flag = 3;
					}
				}
				else {
					flag = 2;
				}
			}
			else
			{
				if (gps_week == gpstimews.week)
				{
					if (((x_accel * x_accel) + (y_accel * y_accel) + (z_accel * z_accel)) >= (accel_min * accel_min)
						&& ((x_accel * x_accel) + (y_accel * y_accel) + (z_accel * z_accel)) <= (accel_max * accel_max))
					{
						if (x_gyro <= 5 && y_gyro <= 5 && z_gyro <= 5)
						{
							flag = 0;
						}
						else {
							flag = 4;
						}
					}
					else {
						flag = 3;
					}
				}
				else {
					flag = 2;
				}
			}
		}

		break;
	case MSG_TYPE_odo:
		memcpy(&vehicle_speed, data.payload, 4);
		if (vehicle_speed >= 0.0)
			flag = 0;
		else
			flag = 1;

		break;
	case MSG_TYPE_INS:
		memcpy(&gps_week, data.payload, 2);
		memcpy(&gps_time_of_week_s, data.payload + 2, 4);
		ins_status = data.payload[6];
		ins_position_type = data.payload[7];
		memcpy(&latitude, data.payload + 8, 8);
		memcpy(&longitude, data.payload + 16, 8);
		memcpy(&height, data.payload + 24, 8);
		memcpy(&north_velocity, data.payload + 32, 4);
		memcpy(&east_velocity, data.payload + 36, 4);
		memcpy(&up_velocity, data.payload + 40, 4);
		memcpy(&longitudinal_velocity, data.payload + 44, 4);
		memcpy(&lateral_velocity, data.payload + 48, 4);
		memcpy(&roll, data.payload + 52, 4);
		memcpy(&pitch, data.payload + 56, 4);
		memcpy(&heading, data.payload + 60, 4);
		memcpy(&latitude_std, data.payload + 64, 4);
		memcpy(&longitude_std, data.payload + 68, 4);
		memcpy(&height_std, data.payload + 72, 4);
		memcpy(&north_velocity_std, data.payload + 76, 4);
		memcpy(&east_velocity_std, data.payload + 80, 4);
		memcpy(&up_velocity_std, data.payload + 84, 4);
		memcpy(&long_vel_std, data.payload + 88, 4);
		memcpy(&lat_vel_std, data.payload + 92, 4);
		memcpy(&roll_std, data.payload + 96, 4);
		memcpy(&pitch_std, data.payload + 100, 4);
		memcpy(&heading_std, data.payload + 104, 4);
		memcpy(&continent_ID, data.payload + 108, 2);


		INS_gps_week = gps_week;
		INS_gps_time_of_week_s = (double)gps_time_of_week_s / 1000;
		if (INS_gps_time_of_week_s > INS_gps_time_of_week_s_last_second)
		{
			if (INS_gps_week_last_second != 0 && INS_gps_time_of_week_s_last_second != 0 && (INS_gps_time_of_week_s - INS_gps_time_of_week_s_last_second) >= 0.02)
				flag = 6;
		}
		else
		{
			flag = 5;
		}
		INS_gps_time_of_week_s_last_second = INS_gps_time_of_week_s;
		INS_gps_week_last_second = INS_gps_week;

		if (!config_time_flag)
		{
			if (abs(gps_week) >= abs(gpstimews.week - 50))
			{
				if (latitude != 0 || longitude != 0 || height != 0.0)
					flag = 0;
				if (latitude > latitude_max || latitude<latitude_min || longitude>longitude_max || longitude < longitude_min)
					flag = 1;
			}
			else {
				flag = 2;
			}
			if (continent_ID != ID_ASIA)
			{
				flag = 3;
			}
		}
		else
		{
			if (gps_week == gpstimews.week)
			{
				if (latitude != 0 || longitude != 0 || height != 0.0)
					flag = 0;
				if (latitude > latitude_max || latitude<latitude_min || longitude>longitude_max || longitude < longitude_min)
					flag = 1;
			}
			else {
				flag = 2;
			}
			if (continent_ID != ID_ASIA)
			{
				flag = 3;
			}
		}
		INS_gps_time_of_week_s_last_second = INS_gps_time_of_week_s;

		break;
	case MSG_TYPE_GNSS:
		memcpy(&gps_week, data.payload, 2);
		memcpy(&gps_time_of_week_s, data.payload + 2, 4);
		position_type = data.payload[6];
		memcpy(&latitude, data.payload + 7, 8);
		memcpy(&longitude, data.payload + 15, 8);
		memcpy(&height, data.payload + 23, 8);
		memcpy(&latitude_std, data.payload + 31, 4);
		memcpy(&longitude_std, data.payload + 35, 4);
		memcpy(&height_std, data.payload + 39, 4);
		memcpy(&numberOfSVs, data.payload + 43, 1);
		memcpy(&numberOfSVs_in_solution, data.payload + 44, 1);
		memcpy(&hdop, data.payload + 45, 4);
		memcpy(&diffage, data.payload + 49, 4);
		memcpy(&north_velocity, data.payload + 53, 4);
		memcpy(&east_velocity, data.payload + 57, 4);
		memcpy(&up_velocity, data.payload + 61, 4);
		memcpy(&north_velocity_std, data.payload + 65, 4);
		memcpy(&east_velocity_std, data.payload + 69, 4);
		memcpy(&up_velocity_std, data.payload + 73, 4);

		gN_gps_time_of_week_s = (double)gps_time_of_week_s / 1000;
		if (gN_gps_time_of_week_s > gN_gps_time_of_week_s_last_second)
		{
			if (gN_gps_time_of_week_s_last_second != 0 && (gN_gps_time_of_week_s - gN_gps_time_of_week_s_last_second) >= 2.0)
				flag = 4;
		}
		else
		{
			flag = 3;
		}
		gN_gps_time_of_week_s_last_second = gN_gps_time_of_week_s;
		if (!config_time_flag)
		{
			if (abs(gps_week) >= abs(gpstimews.week - 50))
			{
				if (latitude != 0 || longitude != 0 || height != 0.0)
					flag = 0;
				if (latitude > latitude_max || latitude<latitude_min || longitude>longitude_max || longitude < longitude_min)
					flag = 1;
			}
			else {
				flag = 2;
			}
		}
		else
		{
			if (gps_week == gpstimews.week)
			{
				if (latitude != 0 || longitude != 0 || height != 0.0)
					flag = 0;
				if (latitude > latitude_max || latitude<latitude_min || longitude>longitude_max || longitude < longitude_min)
					flag = 1;
			}
			else {
				flag = 2;
			}
		}

		break;
	case MSG_TYPE_DM:
		memcpy(&gps_week, data.payload, 2);
		memcpy(&gps_time_of_week_s, data.payload + 2, 4);
		memcpy(&status_bit, data.payload + 6, 4);
		memcpy(&imu_temperature, data.payload + 10, 4);
		memcpy(&mcu_temperature, data.payload + 14, 4);
		memcpy(&sta_temperature, data.payload + 18, 4);
		flag = 0;
		sT_gps_week = gps_week;
		sT_gps_time_of_week_s = ((double)gps_time_of_week_s / 1000);
		if (sT_gps_time_of_week_s > sT_gps_time_of_week_s_last_second)
		{
			if (sT_gps_week_last_second != 0 && sT_gps_time_of_week_s_last_second != 0 && (sT_gps_time_of_week_s - sT_gps_time_of_week_s_last_second) >= 2.0)
				flag = 2;
			else
			{
				memcpy(&RtkMsg_buf, &RtkMsg, sizeof(RtkMsg));
			}
			//if (sT_gps_time_of_week_s - 204231.0 >- 1.0&& sT_gps_time_of_week_s - 204231.0 < 1.0)
			//	flag = 2;
		}
		else
		{
			flag = 1;
		}
		sT_gps_time_of_week_s_last_second = sT_gps_time_of_week_s;
		sT_gps_week_last_second = sT_gps_week;
		int2status(status_bit);
		int2status_file(status_bit);

		break;
	default:
		break;
	}

	return flag;
}

/*************************************************
* @brief    对数据进行解析存入包结构体
* @param	[in] uint8_t* Buff 输入数据指针
* @param	[in] uint32_t BuffLen  输入数据长度
* @retval	FDC_TRUE 解析成功
* @retval	FDC_PARM_ERROR 参数错误
*************************************************/
int INS401Data_Prase(uint8_t* Buff, uint32_t BuffLen)
{
	static uint8_t SearchState = SEARCH_HEADER1;
	uint8_t* pPraseBuf = Buff;
	uint32_t BuffCnt = 0;
	uint16_t CalcCRC = 0;
	uint16_t MsgTemp = 0;
	int   ret = 0;

	if ((FDC_NULL == Buff) || (0 == BuffLen))
	{
		return FDC_PARM_ERROR;
	}

	FILE* fp = fopen(addr_output_success, "a");
	FILE* fp2 = fopen(addr_output_error, "a");


	while (BuffLen--)
	{
		switch (SearchState)
		{
		case SEARCH_HEADER1:
			if (MSG_HEADER == pPraseBuf[BuffCnt])
			{
				SearchState = SEARCH_HEADER2;
			}
			break;

		case SEARCH_HEADER2:
			if (MSG_HEADER == pPraseBuf[BuffCnt])
			{
				SearchState = SEARCH_TYPE1;
			}
			break;

		case SEARCH_TYPE1:
			MsgTemp = pPraseBuf[BuffCnt];
			RtkMsg.code_MSB = pPraseBuf[BuffCnt];
			SearchState = SEARCH_TYPE2;
			break;

		case SEARCH_TYPE2:
			MsgTemp = (MsgTemp << 8) + pPraseBuf[BuffCnt];
			RtkMsg.code_LSB = pPraseBuf[BuffCnt];

			/**< we add function to seach Msg Type
			 **  if msg is not in list, go to Header1
			 **/
			ret = INS401Data_SearchCmd(MsgTemp);
			if (FDC_TRUE == ret)
			{
				SearchState = SEARCH_LENGTH1;
			}
			else
			{
				//MsgTemp = (RtkMsg.code_MSB<< 8) + RtkMsg.code_LSB;
				//INS401Spi_FreqErrDetc(MsgTemp);
				SearchState = SEARCH_HEADER1;
				BuffCnt -= 3;
				BuffLen += 3;
			}
			break;

		case SEARCH_LENGTH1:
			/**< if Msg Len is out of range, it means transmit error**/
			if (pPraseBuf[BuffCnt] < MAX_MSG_LEN)
			{
				RtkMsg.payloadLength[0] = pPraseBuf[BuffCnt];
				SearchState = SEARCH_LENGTH2;
			}
			else
			{
				SearchState = SEARCH_HEADER1;
				BuffCnt -= 4;
				BuffLen += 4;
			}
			break;

		case SEARCH_LENGTH2:
			/**< if Msg Len is out of range, it means transmit error**/
			if (pPraseBuf[BuffCnt] < MAX_MSG_LEN)
			{
				RtkMsg.payloadLength[1] = pPraseBuf[BuffCnt];
				SearchState = SEARCH_LENGTH3;
			}
			else
			{
				SearchState = SEARCH_HEADER1;
				BuffCnt -= 5;
				BuffLen += 5;
			}
			break;

		case SEARCH_LENGTH3:
			/**< if Msg Len is out of range, it means transmit error**/
			if (pPraseBuf[BuffCnt] < MAX_MSG_LEN)
			{
				RtkMsg.payloadLength[2] = pPraseBuf[BuffCnt];
				SearchState = SEARCH_LENGTH4;
			}
			else
			{
				SearchState = SEARCH_HEADER1;
				BuffCnt -= 6;
				BuffLen += 6;
			}
			break;

		case SEARCH_LENGTH4:
			/**< if Msg Len is out of range, it means transmit error**/
			if (pPraseBuf[BuffCnt] < MAX_MSG_LEN)
			{
				RtkMsg.payloadLength[3] = pPraseBuf[BuffCnt];
				RtkMsg.payloadLength_c = RtkMsg.payloadLength[0] | RtkMsg.payloadLength[1] << 8 | RtkMsg.payloadLength[2] << 16 | RtkMsg.payloadLength[3] << 24;
				MsgTemp = 0;
				SearchState = SEARCH_DATA;
			}
			else
			{
				SearchState = SEARCH_HEADER1;
				BuffCnt -= 7;
				BuffLen += 7;
			}
			break;

		case SEARCH_DATA:
			if (MsgTemp < RtkMsg.payloadLength_c)
			{
				RtkMsg.payload[MsgTemp] = pPraseBuf[BuffCnt];
				MsgTemp++;
			}
			else
			{
				SearchState = SEARCH_CRC;
				continue;
			}
			break;

		case SEARCH_CRC:
			if (MsgTemp < (RtkMsg.payloadLength_c + 3))
			{
				RtkMsg.payload[MsgTemp] = pPraseBuf[BuffCnt];
				MsgTemp++;
			}

			if (MsgTemp == (RtkMsg.payloadLength_c + 2))
			{
				CalcCRC = CalculateCRC(&RtkMsg.code_MSB, RtkMsg.payloadLength_c + 6);
				MsgTemp = (RtkMsg.payload[RtkMsg.payloadLength_c + 1] << 8)
					+ RtkMsg.payload[RtkMsg.payloadLength_c];

				if (MsgTemp == CalcCRC)
				{
					MsgPtclRst = MsgTypeRst;
					MsgTemp = (RtkMsg.code_MSB << 8) + RtkMsg.code_LSB;
					ret = INS401Data_Verify(&RtkMsg);

					if (ret != 0)
					{
						if (RtkMsg.code_MSB == 0x01 && RtkMsg.code_LSB == 0x0a)
						{
							switch (ret)
							{
							case 2:IMU_gpsweek_error++;
								break;
							case 3:IMU_acce_error++;
								break;
							case 4:IMU_gyro_error++;
								break;
							case 5:IMU_time_return_error++;
								break;
							case 6:IMU_time_jump_error++;
								break;
							default:IMU_error++;
							}
						}
						if (RtkMsg.code_MSB == 0x01 && RtkMsg.code_LSB == 0x0b)
						{
							switch (ret)
							{
							case 2:odo_gpsweek_error++;
								break;
							case 3:odo_acce_error++;
								break;
							case 4:odo_gyro_error++;
								break;
							default:odo_error++;
							}
						}
						if (RtkMsg.code_MSB == 0x03 && RtkMsg.code_LSB == 0x0a)
						{
							switch (ret)
							{
							case 1:INS_rationality_error++;
								break;
							case 2:INS_gpsweek_error++;
								break;
							case 3:INS_continent_error++;
								break;
							case 5:INS_time_return_error++;
								break;
							case 6:INS_time_jump_error++;
								break;
							default:INS_error++;
							}
						}
						if (RtkMsg.code_MSB == 0x02 && RtkMsg.code_LSB == 0x0a)
						{
							switch (ret)
							{
							case 1:GNSS_rationality_error++;
								break;
							case 2:GNSS_gpsweek_error++;
								break;
							case 3:GNSS_time_return_error++;
								break;
							case 4:GNSS_time_jump_error++;
								break;
							default:GNSS_error++;
							}
						}
						if (RtkMsg.code_MSB == 0x05 && RtkMsg.code_LSB == 0x0a)
						{
							switch (ret)
							{
							case 1:DM_time_return_error++;
								break;
							case 2:DM_time_jump_error++;
								fprintf(fp2, "sT_time_jump_error_last %0.0f %02x %02x %02x %02x ", sT_gps_time_of_week_s_last_second, RtkMsg_buf.sync_MSB, RtkMsg_buf.sync_LSB, RtkMsg_buf.code_MSB, RtkMsg_buf.code_LSB);
								fprintf(fp2, "%02x %02x %02x %02x ", RtkMsg_buf.payloadLength_c, RtkMsg_buf.payloadLength[1], RtkMsg_buf.payloadLength[2], RtkMsg_buf.payloadLength[3]);
								for (int i = 0; i < RtkMsg_buf.payloadLength_c + 2; i++)
									fprintf(fp2, "%02x ", RtkMsg_buf.payload[i]);
								fprintf(fp2, "\n");
								fprintf(fp2, "sT_time_jump_error_next %0.0f %02x %02x %02x %02x ", sT_gps_time_of_week_s,RtkMsg.sync_MSB, RtkMsg.sync_LSB, RtkMsg.code_MSB, RtkMsg.code_LSB);
								fprintf(fp2, "%02x %02x %02x %02x ", RtkMsg.payloadLength_c, RtkMsg.payloadLength[1], RtkMsg.payloadLength[2], RtkMsg.payloadLength[3]);
								for (int i = 0; i < RtkMsg.payloadLength_c + 2; i++)
									fprintf(fp2, "%02x ", RtkMsg.payload[i]);
								fprintf(fp2, "\n");
								break;
							default:DM_error++;
							}
						}
						/*if (RtkMsg.code_MSB == 0x01|| RtkMsg.code_MSB == 0x02|| RtkMsg.code_MSB == 0x03)
						{
							fprintf(fp2, "%c%c 0x%02x%02x ", RtkMsg.sync_MSB, RtkMsg.sync_LSB, RtkMsg.code_LSB, RtkMsg.code_MSB);
							fprintf(fp2, "%d ", RtkMsg.payloadLength_c);
							for (int i = 0; i < RtkMsg.payloadLength_c + 2; i++)
								fprintf(fp2, "%d ", RtkMsg.payload[i]);
							fprintf(fp2, "\n");
						}*/
					}

					fprintf(fp, "%c%c 0x%02x%02x ", RtkMsg.sync_MSB, RtkMsg.sync_LSB, RtkMsg.code_LSB, RtkMsg.code_MSB);
					fprintf(fp, "%d %d %d %d ", RtkMsg.payloadLength_c, RtkMsg.payloadLength[1], RtkMsg.payloadLength[2], RtkMsg.payloadLength[3]);
					for (int i = 0; i < RtkMsg.payloadLength_c + 2; i++)
						fprintf(fp, "%d ", RtkMsg.payload[i]);
					fprintf(fp, "\n");
					s_cnt++;
				}
#if 1		//INS401考虑crc校验错误
				else
				{

					MsgTemp = (RtkMsg.code_MSB << 8) + RtkMsg.code_LSB;
					//INS401Data_FreqErrDetc(MsgTemp);

					fprintf(fp2, "%c%c 0x%02x%02x ", RtkMsg.sync_MSB, RtkMsg.sync_LSB, RtkMsg.code_MSB, RtkMsg.code_LSB);
					fprintf(fp2, "%d %d %d %d ", RtkMsg.payloadLength_c, RtkMsg.payloadLength[1], RtkMsg.payloadLength[2], RtkMsg.payloadLength[3]);
					for (int i = 0; i < RtkMsg.payloadLength_c + 2; i++)
						fprintf(fp2, "%d ", RtkMsg.payload[i]);
					fprintf(fp2, "\n");
					error_cnt++;
					
				}
#endif
				MsgTemp = 0;
				SearchState = SEARCH_HEADER1;
			}
			break;

		default:
			SearchState = SEARCH_HEADER1;
			break;
		}
		BuffCnt++;
	}

	fclose(fp);
	fclose(fp2);
	return FDC_TRUE;
}

/*************************************************
* @brief    输出数据校验结果
* @return	None
* @note		需要初始化完成后才能输出结果
*************************************************/
void INS401Data_result()
{
	char command_dir[500] = { 0 };
	FILE* fp = fopen(addr_output_success, "a");
	FILE* fp2;
	//FILE* fp2 = fopen(addr_output_error, "a");

	fprintf(fp, "all : %d\tsuccess : %d\n", s_cnt + error_cnt, s_cnt);
	//fprintf(fp2, "all : %d\terror : %d\n", s_cnt + error_cnt, error_cnt);

	printf("Raw IMU gps week error:%d\n", IMU_gpsweek_error);
	printf("Raw IMU acce error:%d\n", IMU_acce_error);
	printf("Raw IMU gyro error:%d\n", IMU_gyro_error);
	printf("Raw IMU time return error:%d\n", IMU_time_return_error);
	printf("Raw IMU time jumped error:%d\n", IMU_time_jump_error);
	printf("INS solution packet gps week error:%d\n", INS_gpsweek_error);
	printf("INS solution packet rationality error : % d\n", INS_rationality_error);
	printf("INS solution packet continent ID error:%d\n", INS_continent_error);
	printf("INS time return error:%d\n", INS_time_return_error);
	printf("INS time jumped error:%d\n", INS_time_jump_error);
	printf("GNSS solution packet gps week error:%d\n", GNSS_gpsweek_error);
	printf("GNSS solution packet rationality error:%d\n", GNSS_rationality_error);
	printf("GNSS time return error:%d\n", GNSS_time_return_error);
	printf("GNSS time jumped error:%d\n", GNSS_time_jump_error);
	printf("Status time return error:%d\n", DM_time_return_error);
	printf("Status time jumped error:%d\n", DM_time_jump_error);

	printf("other packet error:\ns1:%d\ns2:%d\niN:%d\ngN:%d\n", IMU_error, odo_error, INS_error, GNSS_error);

	fclose(fp);

	printf("\nstatus error cnt\n");

	printf("master_fail\t%d\n", status_error.master_fail);
	printf("hw_error\t%d\n", status_error.hw_error);
	printf("sw_error\t%d\n", status_error.sw_error);
	printf("config_error\t%d\n", status_error.config_error);
	printf("calibration_error\t%d\n", status_error.calibration_error);
	printf("accel_degradation\t%d\n", status_error.accel_degradation);
	printf("gyro_degradation\t%d\n", status_error.gyro_degradation);
	printf("forced_restart\t%d\n", status_error.forced_restart);
	printf("CRC_error\t%d\n", status_error.CRC_error);
	printf("tx_overflow_error\t%d\n", status_error.tx_overflow_error);
	printf("pps_status\t%d\n", status_error.pps_status);
	printf("gnss_data_status\t%d\n", status_error.gnss_data_status);
	printf("gnss_signal_status\t%d\n", status_error.gnss_signal_status);
	printf("power\t%d\n", status_error.power);
	printf("mcu_status\t%d\n", status_error.mcu_status);
	printf("temperature_under_mcu_flag\t%d\n", status_error.temperature_under_mcu_flag);
	printf("temperature_under_sta_flag\t%d\n", status_error.temperature_under_sta_flag);
	printf("temperature_under_imu_flag\t%d\n", status_error.temperature_under_imu_flag);
	printf("temperature_over_mcu_flag\t%d\n", status_error.temperature_over_mcu_flag);
	printf("temperature_over_sta_flag\t%d\n", status_error.temperature_over_sta_flag);
	printf("temperature_over_imu_flag\t%d\n", status_error.temperature_over_imu_flag);

	fp = fopen(addr_output_error_csv, "a");
	fp2 = fopen(addr_status_error_csv, "a");

	fprintf(fp, "error_name,error_cnt\n");
	fprintf(fp, "Raw IMU gps week error\t,%d\n", IMU_gpsweek_error);
	fprintf(fp, "Raw IMU acce error\t,%d\n", IMU_acce_error);
	fprintf(fp, "Raw IMU gyro error\t,%d\n", IMU_gyro_error);
	fprintf(fp, "Raw IMU time return error\t,%d\n", IMU_time_return_error);
	fprintf(fp, "Raw IMU time jumped error\t,%d\n", IMU_time_jump_error);
	fprintf(fp, "INS solution packet gps week error\t,%d\n", INS_gpsweek_error);
	fprintf(fp, "INS solution packet rationality error\t,%d\n", INS_rationality_error);
	fprintf(fp, "INS solution packet continent ID error\t,%d\n", INS_continent_error);
	fprintf(fp, "INS time return error\t,%d\n", INS_time_return_error);
	fprintf(fp, "INS time jumped error\t,%d\n", INS_time_jump_error);
	fprintf(fp, "GNSS solution packet gps week error\t,%d\n", GNSS_gpsweek_error);
	fprintf(fp, "GNSS solution packet rationality error\t,%d\n", GNSS_rationality_error);
	fprintf(fp, "GNSS time return error\t,%d\n", GNSS_time_return_error);
	fprintf(fp, "GNSS time jumped error\t,%d\n", GNSS_time_jump_error);
	fprintf(fp, "Status time return error\t,%d\n", DM_time_return_error);
	fprintf(fp, "Status time jumped error\t,%d\n", DM_time_jump_error);
	fprintf(fp, "other_packet_error,error_cnt\n");
	fprintf(fp, "Raw IMU\t,%d\nINS solution packet\t,%d\nGNSS solution packet\t,%d\n", IMU_error, INS_error, GNSS_error);
	fprintf(fp, "all_cnt,all_error_cnt\n");
	fprintf(fp, "%d\t,%d\n", s_cnt + error_cnt, error_cnt);

	fprintf(fp2, "all status count,%d\n", all_status_cnt);
	fprintf(fp2, "status_name,status_error_cnt\n");

	fprintf(fp2, "master_fail\t,%d\n", status_error.master_fail);
	fprintf(fp2, "hw_error\t,%d\n", status_error.hw_error);
	fprintf(fp2, "sw_error\t,%d\n", status_error.sw_error);
	fprintf(fp2, "config_error\t,%d\n", status_error.config_error);
	fprintf(fp2, "calibration_error\t,%d\n", status_error.calibration_error);
	fprintf(fp2, "accel_degradation\t,%d\n", status_error.accel_degradation);
	fprintf(fp2, "gyro_degradation\t,%d\n", status_error.gyro_degradation);
	fprintf(fp2, "forced_restart\t,%d\n", status_error.forced_restart);
	fprintf(fp2, "CRC_error\t,%d\n", status_error.CRC_error);
	fprintf(fp2, "tx_overflow_error\t,%d\n", status_error.tx_overflow_error);
	fprintf(fp2, "pps_status\t,%d\n", status_error.pps_status);
	fprintf(fp2, "gnss_data_status\t,%d\n", status_error.gnss_data_status);
	fprintf(fp2, "gnss_signal_status\t,%d\n", status_error.gnss_signal_status);
	fprintf(fp2, "power\t,%d\n", status_error.power);
	fprintf(fp2, "mcu_status\t,%d\n", status_error.mcu_status);
	fprintf(fp2, "temperature_under_mcu_flag\t,%d\n", status_error.temperature_under_mcu_flag);
	fprintf(fp2, "temperature_under_sta_flag\t,%d\n", status_error.temperature_under_sta_flag);
	fprintf(fp2, "temperature_under_imu_flag\t,%d\n", status_error.temperature_under_imu_flag);
	fprintf(fp2, "temperature_over_mcu_flag\t,%d\n", status_error.temperature_over_mcu_flag);
	fprintf(fp2, "temperature_over_sta_flag\t,%d\n", status_error.temperature_over_sta_flag); 
	fprintf(fp2, "temperature_over_imu_flag\t,%d\n", status_error.temperature_over_imu_flag);

	fclose(fp);
	fclose(fp2);

	fp = fopen(addr_decode_log, "a");
	fprintf(fp, "type IMU : \t%d\n", MsgCount.IMU_Count);
	fprintf(fp, "type odo : \t%d\n", MsgCount.odo_Count);
	fprintf(fp, "type INS : \t%d\n", MsgCount.INS_Count);
	fprintf(fp, "type GNSS : \t%d\n", MsgCount.GNSS_Count);
	fprintf(fp, "type DM : \t%d\n", MsgCount.DM_Count);
	fclose(fp);

	strcat(command_dir, "explorer.exe ");
	strcat(command_dir, addr_output);
	if (_access(addr_output, 0) == 0)
		system(command_dir);

}


/**
  * @brief  Move the cursor to the specified position on the text screen.
  * @param  [in] x: X axis coordinates.
  * @param  [in] y: Y axis coordinates.
  * @return None.
  */
static void gotoxy(int x, int y)
{
	COORD  pos = { x, y };
	HANDLE hOut = GetStdHandle(STD_OUTPUT_HANDLE);
	SetConsoleCursorPosition(hOut, pos);
}
