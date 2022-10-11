#ifndef __INS401_H__

#define __INS401_H__

#include "INS401_API.h"

#define uint8_t unsigned char
#define int32_t int
#define uint32_t unsigned int
#define uint16_t unsigned short

#define   		MSG_HEADER		0x55
#define			ETH_MSG_HEADER	0x5555


/***************ERROR CODE DEFINITION BEGIN************/
#define     FDC_FALSE                   (-1)
#define     FDC_TRUE                    (1)
#define     FDC_OK                      (1)
#define     FDC_PARM_ERROR              (-2)
#define     FDC_BUFF_ERROR              (-3)
#define		FDC_NULL					(0)
#define		FDC_IDLE					(0)
/***************ERROR CODE DEFINITION END**************/

#define	   MAX_PAYLOAD_LENGTH					255

/*******************************************************/
#define 		MSG_TYPE_IMU		0x010a
#define 		MSG_TYPE_odo		0x010b
#define 		MSG_TYPE_INS		0x030a
#define 		MSG_TYPE_GNSS		0x020a
#define 		MSG_TYPE_DM		0x050a
/*******************************************************/

#define	   MAX_MSG_LEN							111//90

#define uint32_t unsigned int

typedef struct {
	/*IMU*/
	uint32_t master_fail : 1; // 0:normal 1:fatal error occured
	uint32_t hw_error : 1;  // 0:normal 1:hardware exception detected
	uint32_t sw_error : 1; // 0:normal 1:software exception detected
	uint32_t config_error : 1; // 0:normal 1:config error detected by periodic selftest
	uint32_t calibration_error : 1; // 0:normal 1:calobration data corrupted
	uint32_t accel_degradation : 1; // 0:normal 1:accel data degradation due to sensor exception
	uint32_t gyro_degradation : 1; //0:normal 1:gyro data degradation due to sensor exception
	uint32_t forced_restart : 1; //0:normal 1:forced restart
	uint32_t CRC_error : 1; //0:normal 1:CRC error detected
	uint32_t tx_overflow_error : 1; // 0:normal 1:tx overflow occurred 10 consecutive cycles

	/*GNSS*/
	uint32_t pps_status : 1; //0:normal 1:1PPS pulse exception
	uint32_t gnss_data_status : 1; //0:normal 1:GNSS chipset has NO data output
	uint32_t gnss_signal_status : 1; // 0:normal 1:GNSS chipset has data output but no valid signal detected

	/*operation*/
	uint32_t power : 1; // 0:normal 1:any component has no power
	uint32_t mcu_status : 1; // 0:normal 1:MCU failure
	uint32_t temperature_under_mcu_flag : 1; // 0:normal 1:under temperature
	uint32_t temperature_under_sta_flag : 1; // 0:normal 1:under temperature
	uint32_t temperature_under_imu_flag : 1; // 0:normal 1:under temperature
	uint32_t temperature_over_mcu_flag : 1; // 0:normal 1:over temperature
	uint32_t temperature_over_sta_flag : 1; // 0:normal 1:over temperature
	uint32_t temperature_over_imu_flag : 1; // 0:normal 1:over temperature

	uint32_t rexerved : 11;
} status_bit_t;

typedef struct {
	uint16_t gps_week : 16;
	uint32_t gps_millisecs : 32;
	uint8_t position_type : 8;	//0:invalid 1:single-point positioning(SPP) 
								//2:Real time differential Gnss(RTD) 
								//4:Real time kinematic(RTK) ambiguity fixed(RTK_FIXED) 
								//5:RTK with ambiguity float(RTK_FLOAT)
	double latitude;	//geodetic latitude
	double longitude;	//geodetic longitude
	double height;		//height above ellipsoid
	float latitude_std;	//latitudinal position accuracy
	float longitude_std;//longitudinal position accuracy
	float height_std;	//vertical position accuracy
	uint8_t numberOfSVs : 8;	//number of satellites
	uint8_t numberOfSVs_in_solution : 8;	//number of satellites in solution
	float hdop;		//horizontal dilution of precision
	float diffage;	//age of differential GNSS correction
	float north_vel;	//north velocity
	float east_vel;		//east velocity
	float up_vel;		//up velocity
	float north_vel_std;	//north velocity accuracy
	float east_vel_std;		//east velocity accuracy
	float up_vel_std;		//up velocity accuracy

}gnss_sloution_packet;

typedef struct {
	uint16_t gps_week : 16;
	uint32_t gps_millisecs : 32;
	uint8_t ins_status : 8;
	uint8_t ins_position_type : 8;
	double latitude;
	double longitude;
	double height;
	float north_velocity;
	float east_velocity;
	float up_velocity;
	float longitudinal_velocity;
	float lateral_velocity;
	float roll;
	float pitch;
	float heading;
	float latitude_std;
	float longitude_std;
	float height_std;
	float north_velocity_std;
	float east_velocity_std;
	float up_velocity_std;
	float long_vel_std;
	float lat_vel_std;
	float roll_std;
	float picth_std;
	float heading_std;
}ins_solution_packet;

typedef struct {
	uint16_t gps_week : 16;
	uint32_t gps_millisecs : 32;
	uint32_t device_status_bit_field : 32;
	float imu_temperature;
	float mcu_temperature;
	float sta_temperature;
}diagnostic_message;

typedef struct {
	uint16_t gps_week;
	uint32_t gps_millisecs;
	float accel_x;
	float accel_y;
	float accel_z;
	float gyro_x;
	float gyro_y;
	float gyro_z;
}raw_imu_data ;


enum {
	SEARCH_HEADER1 = 0,
	SEARCH_HEADER2 = 1,
	SEARCH_TYPE1 = 2,
	SEARCH_TYPE2 = 3,
	SEARCH_LENGTH1 = 4,
	SEARCH_LENGTH2 = 5,
	SEARCH_LENGTH3 = 6,
	SEARCH_LENGTH4 = 7,
	SEARCH_DATA = 8,
	SEARCH_CRC = 9,
};

enum {
	ETH_CMD_S1 = 0,
	ETH_CMD_O1 = 1,
	ETH_CMD_IN = 2,
	ETH_CMD_GN = 3,
	ETH_CMD_ST = 4,

	ETH_TOTAL_CMD,
};

/** All Msg Freq define **/
enum {
	ETH_IMU_FREQ = 100,
	ETH_ODO_FREQ = 100,
	ETH_INS_FREQ = 100,
	ETH_GNSS_FREQ = 1,
	ETH_DM_FREQ = 1,
};

enum IDCONTINENT
{
	ID_NONE = -2,
	ID_ERROR = -1,
	ID_UNKNOWN = 0,
	ID_ASIA = 1,
	ID_EUROPE = 2,
	ID_OCEANIA = 3,
	ID_AFRICA = 4,
	ID_NORTHAMERICA = 5,
	ID_SOUTHAMERICA = 6,
	ID_ANTARCTICA = 7,
};

typedef struct {
	uint8_t       sync_MSB;        // 1
	uint8_t       sync_LSB;        // 2
	uint8_t       code_MSB;        // 3
	uint8_t       code_LSB;        // 4
	uint8_t	      payloadLength[4];   // 5
	uint8_t       payload[MAX_PAYLOAD_LENGTH + 3];
	uint8_t		  payloadLength_c;
}stRtkMsg;

/** ETH Cmd List **/
typedef struct {
	uint16_t	MsgCmd;
	uint8_t		MsgFreq;
}stEthCmdList;


static stEthCmdList EthCmd_List[ETH_TOTAL_CMD] = {
	{MSG_TYPE_IMU, ETH_IMU_FREQ},
	{MSG_TYPE_odo, ETH_ODO_FREQ},
	{MSG_TYPE_INS, ETH_INS_FREQ},
	{MSG_TYPE_GNSS, ETH_GNSS_FREQ},
	{MSG_TYPE_DM, ETH_DM_FREQ}
};

typedef struct {
	uint32_t		IMU_Count;
	uint32_t		odo_Count;
	uint32_t		INS_Count;
	uint32_t		GNSS_Count;
	uint32_t		DM_Count;
}stMsgCount;

///** Frequency error flag **/
//typedef struct {
//	uint8_t		s1_Err : 1;
//	uint8_t		s2_Err : 1;
//	uint8_t		iN_Err : 1;
//	uint8_t		d1_Err : 1;
//	uint8_t		gN_Err : 1;
//	uint8_t		d2_Err : 1;
//	uint8_t		sT_Err : 1;
//	uint8_t		Flag_1s : 1;
//}stSpiMsgFreqErr;

//typedef union {
//	uint8_t MsgFreqErr;
//	stSpiMsgFreqErr MsgFreqErrBit;
//}unSpiMsgFreqErr;

typedef struct {
	/*IMU*/
	uint32_t master_fail; // 0:normal 1:fatal error occured
	uint32_t hw_error;  // 0:normal 1:hardware exception detected
	uint32_t sw_error; // 0:normal 1:software exception detected
	uint32_t config_error; // 0:normal 1:config error detected by periodic selftest
	uint32_t calibration_error; // 0:normal 1:calobration data corrupted
	uint32_t accel_degradation; // 0:normal 1:accel data degradation due to sensor exception
	uint32_t gyro_degradation; //0:normal 1:gyro data degradation due to sensor exception
	uint32_t forced_restart; //0:normal 1:forced restart
	uint32_t CRC_error; //0:normal 1:CRC error detected
	uint32_t tx_overflow_error; // 0:normal 1:tx overflow occurred 10 consecutive cycles

	/*GNSS*/
	uint32_t pps_status; //0:normal 1:1PPS pulse exception
	uint32_t gnss_data_status; //0:normal 1:GNSS chipset has NO data output
	uint32_t gnss_signal_status; // 0:normal 1:GNSS chipset has data output but no valid signal detected

	/*operation*/
	uint32_t power; // 0:normal 1:any component has no power
	uint32_t mcu_status; // 0:normal 1:MCU failure
	uint32_t temperature_under_mcu_flag; // 0:normal 1:under temperature
	uint32_t temperature_under_sta_flag; // 0:normal 1:under temperature
	uint32_t temperature_under_imu_flag; // 0:normal 1:under temperature
	uint32_t temperature_over_mcu_flag; // 0:normal 1:over temperature
	uint32_t temperature_over_sta_flag; // 0:normal 1:over temperature
	uint32_t temperature_over_imu_flag; // 0:normal 1:over temperature

	uint32_t rexerved : 11;

}status_error_cnt;


status_bit_t ins401_status = { 0 };
gnss_sloution_packet ins401_gnss = { 0 };
ins_solution_packet ins401_ins = { 0 };
diagnostic_message ins401_st = { 0 };
raw_imu_data ins401_s1 = { 0 };

uint32_t sT_gps_week;
uint32_t sT_gps_week_last_second;
uint32_t IMU_gps_week;
uint32_t IMU_gps_week_last_second;
uint32_t INS_gps_week;
uint32_t INS_gps_week_last_second;
double sT_gps_time_of_week_s;
double sT_gps_time_of_week_s_last_second=0.0;
double gN_gps_time_of_week_s;
double gN_gps_time_of_week_s_last_second = 0.0;
double IMU_gps_time_of_week_s;
double IMU_gps_time_of_week_s_last_second = 0.0;
double INS_gps_time_of_week_s;
double INS_gps_time_of_week_s_last_second = 0.0;

stRtkMsg        RtkMsg = { 0x55, 0x55 };
stRtkMsg        RtkMsg_buf = { 0x55, 0x55 };
stRtkMsg	iN_RtkMsg_buf[10];
stRtkMsg	gN_RtkMsg_buf;

uint8_t			MsgTypeRst = 0;
uint8_t			MsgPtclRst = 0;

stMsgCount    MsgCount = { 0 };
//unSpiMsgFreqErr SpiMsgFreqErr = { 0 };

//int error_cnt = 0;

status_error_cnt status_error = { 0 };


float accel_min = 9.5;
float accel_max = 11.5;
float latitude_min = 29.5;
float latitude_max = 33.5;
float longitude_min = 118.0;
float longitude_max = 122.0;


int INS401Data_Prase(uint8_t* Buff, uint32_t BuffLen);
int Init_Verify(uint8_t* file_input_addr);
//void Rtk330Data_status_error_cnt();
static void gotoxy(int x, int y);
void INS401Data_result();

uint8_t addr_input[500] = "";
char addr_output[500] = { 0 };
char addr_output_packet[500] = { 0 };
uint8_t addr_output_success[500] = "";
uint8_t addr_output_error[500] = "";
uint8_t addr_status[500] = "";
uint8_t addr_output_error_csv[500] = "";
uint8_t addr_status_error_csv[500] = "";
uint8_t addr_status_csv[500] = "";
uint8_t addr_configuration[500] = "";
uint8_t addr_device_info[500] = "";
uint8_t addr_decode_log[500] = "";



time_t        times = 0;
double        mjd = 0.0;
DateTime      utctime = { .year = 1970, .month = 1, .day = 1, .hour = 0, .minute = 0, .second = 0 };
DateTime      local_time = { .year = 1970, .month = 1, .day = 1, .hour = 8, .minute = 0, .second = 0 };
DateTime      gpstime = { .year = 1970, .month = 1, .day = 1, .hour = 0, .minute = 0, .second = 0 };
GpsWeekSecond gpstimews = { 0 };

int		IMU_error = 0, odo_error = 0, INS_error = 0, GNSS_error = 0, DM_error = 0;
int IMU_gpsweek_error = 0, IMU_acce_error = 0, IMU_gyro_error = 0;
int odo_gpsweek_error = 0, odo_acce_error = 0, odo_gyro_error = 0;
int INS_gpsweek_error = 0, INS_rationality_error = 0, INS_continent_error = 0;
int GNSS_gpsweek_error = 0, GNSS_rationality_error = 0;
int DM_time_return_error = 0, DM_time_jump_error = 0;
int GNSS_time_return_error = 0, GNSS_time_jump_error = 0;
int INS_time_return_error = 0, INS_time_jump_error = 0;
int IMU_time_return_error = 0, IMU_time_jump_error = 0;
int all_status_cnt = 0;
int   s_cnt = 0;
int   error_cnt = 0;

int config_time_flag = 0;


#endif // !__INS401_H__


