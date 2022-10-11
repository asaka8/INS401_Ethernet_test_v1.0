#ifndef __INS401_API_H__

#define __INS401_API_H__


#define uint8_t unsigned char
#define int32_t int
#define uint32_t unsigned int
#define uint16_t unsigned short

/*************************************************
* @brief    ��ʼ�� ��Ҫ�ļ�Ȩ��
* @param	[in] uint8_t * file_input_addr	 �������ݵ�·���ַ���ָ��
* @retval	0 ��ʼ���ɹ�
*************************************************/
int Init_Verify(uint8_t* file_input_addr);

/*************************************************
* @brief    ���������CMD�ж��Ƿ�Ϊ��֪������
* @param	[in] uint16_t MsgTyoe 2�ֽ�CMD Little End
* @retval	FDC_FALSE δ֪����
* @retval	FDC_TRUE ��֪����
*************************************************/
//int INS401Data_SearchCmd(uint16_t MsgType);

/*************************************************
* @brief    ����CRC16 ʹ�ò��
* @param	[in] uint8_t *buf	���������ָ��
* @param	[in] uint16_t length	��������ݳ���
* @return	CRC16	Big End
*************************************************/
//uint16_t CalculateCRC(uint8_t* buf, uint16_t  length);

/*************************************************
* @brief    �����CMD�������������ṹ��
* @param	[in] uint16_t MsgType	�����CMD
* @return	None
*************************************************/
//void INS401Data_PakCnt(uint16_t MsgType);

/*************************************************
* @brief    ���status_bits����ṹ��
* @param	[in] uint32_t status	 status_bits
* @return	None
*************************************************/
//void int2status(uint32_t status);

/*************************************************
* @brief    ���status_bits����CSV�ļ�
* @param	[in] uint32_t status	 status_bits
* @return	None
*************************************************/
//void int2status_file(uint32_t status);

/*************************************************
* @brief    �԰����ݽ��к�����У��
* @param	[in] void* Buff  �����ݽṹ��(stRtkMsg)
* @retval	0 У��ɹ�
* @retval	����ֵ ����ʧ��
* @note		����data binͬ���ļ������Ƿ���configuration.json
*			�ж��Ƿ��ܶ������Ե�׼ȷʱ�䣬��׼ȷʱ�俴׼ȷʱ��
*			û׼ȷʱ�俴�Ƿ������ڵ�ʱ����һ��
*************************************************/
//int INS401Data_Verify(void* Buff);

/*************************************************
* @brief    �����ݽ��н���������ṹ��
* @param	[in] uint8_t* Buff ��������ָ��
* @param	[in] uint32_t BuffLen  �������ݳ���
* @retval	FDC_TRUE �����ɹ�
* @retval	FDC_PARM_ERROR ��������
*************************************************/
int INS401Data_Prase(uint8_t* Buff, uint32_t BuffLen);

/*************************************************
* @brief    �������У����
* @return	None
* @note		��Ҫ��ʼ����ɺ����������
*************************************************/
void INS401Data_result();

/*
* ʵ��ʹ����ֻ��Ҫʹ��1����ʼ������Init_Verify
*					  2�����ݽ�������INS401Data_Prase
*					  3������������INS401Data_result
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


