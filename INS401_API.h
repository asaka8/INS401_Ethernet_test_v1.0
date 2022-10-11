#ifndef __INS401_API_H__

#define __INS401_API_H__


#define uint8_t unsigned char
#define int32_t int
#define uint32_t unsigned int
#define uint16_t unsigned short

/*************************************************
* @brief    初始化 需要文件权限
* @param	[in] uint8_t * file_input_addr	 输入数据的路径字符串指针
* @retval	0 初始化成功
*************************************************/
int Init_Verify(uint8_t* file_input_addr);

/*************************************************
* @brief    根据输入的CMD判断是否为已知的命令
* @param	[in] uint16_t MsgTyoe 2字节CMD Little End
* @retval	FDC_FALSE 未知命令
* @retval	FDC_TRUE 已知命令
*************************************************/
//int INS401Data_SearchCmd(uint16_t MsgType);

/*************************************************
* @brief    计算CRC16 使用查表法
* @param	[in] uint8_t *buf	输入的数据指针
* @param	[in] uint16_t length	输入的数据长度
* @return	CRC16	Big End
*************************************************/
//uint16_t CalculateCRC(uint8_t* buf, uint16_t  length);

/*************************************************
* @brief    计算各CMD包解包次数存入结构体
* @param	[in] uint16_t MsgType	输入的CMD
* @return	None
*************************************************/
//void INS401Data_PakCnt(uint16_t MsgType);

/*************************************************
* @brief    解包status_bits存入结构体
* @param	[in] uint32_t status	 status_bits
* @return	None
*************************************************/
//void int2status(uint32_t status);

/*************************************************
* @brief    解包status_bits存入CSV文件
* @param	[in] uint32_t status	 status_bits
* @return	None
*************************************************/
//void int2status_file(uint32_t status);

/*************************************************
* @brief    对包数据进行合理性校验
* @param	[in] void* Buff  包数据结构体(stRtkMsg)
* @retval	0 校验成功
* @retval	其他值 检验失败
* @note		根据data bin同级文件夹下是否有configuration.json
*			判断是否能读到测试的准确时间，有准确时间看准确时间
*			没准确时间看是否与现在的时间差超过一年
*************************************************/
//int INS401Data_Verify(void* Buff);

/*************************************************
* @brief    对数据进行解析存入包结构体
* @param	[in] uint8_t* Buff 输入数据指针
* @param	[in] uint32_t BuffLen  输入数据长度
* @retval	FDC_TRUE 解析成功
* @retval	FDC_PARM_ERROR 参数错误
*************************************************/
int INS401Data_Prase(uint8_t* Buff, uint32_t BuffLen);

/*************************************************
* @brief    输出数据校验结果
* @return	None
* @note		需要初始化完成后才能输出结果
*************************************************/
void INS401Data_result();

/*
* 实际使用中只需要使用1、初始化函数Init_Verify
*					  2、数据解析函数INS401Data_Prase
*					  3、结果输出函数INS401Data_result
strcpy(addr_input, 'file path');
Init_Verify(addr_input);

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
fread(data_buf, 1, lenth, fp);
INS401Data_Prase(data_buf, lenth);

INS401Data_result();

fclose(fp);
*/

#endif // !__INS401_API_H__


