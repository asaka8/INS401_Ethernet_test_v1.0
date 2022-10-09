import time
import struct
from gps_time_module import gps_week_seconds

start_time = time.time()

def build_gt_packet(payload):
    header = [0x55, 0x55]
    packet_type = [0x47, 0x54]
    length = [0x06]

    gt_msg = bytes(packet_type + length) + payload
    crc = bytes(calc_crc(gt_msg))
    print(crc)

    gt_packet = bytes(header) + gt_msg + crc

    return gt_packet

def calc_crc(payload):
        crc = 0x1D0F
        for bytedata in payload:
            crc = crc ^ (bytedata << 8)
            i = 0
            while i < 8:
                if crc & 0x8000:
                    crc = (crc << 1) ^ 0x1021
                else:
                    crc = crc << 1
                i += 1

        crc = crc & 0xffff
        crc_msb = (crc & 0xFF00) >> 8
        crc_lsb = (crc & 0x00FF)
        return [crc_msb, crc_lsb]

def gt_sender():
    start_time = time.time()
    while True:    
        if time.time() - start_time >= 1:
            cur_time = time.time()
            gps_week_num = gps_week_seconds(cur_time)[0]
            gps_time_of_week = gps_week_seconds(cur_time)[2]
            payload = struct.pack('<I', gps_time_of_week) + struct.pack('<H', gps_week_num)
            gt_packet = build_gt_packet(payload)
            print(gt_packet.hex())
            start_time = time.time()

gt_sender()