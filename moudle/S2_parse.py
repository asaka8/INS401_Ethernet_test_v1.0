import struct

logf_name = input('input data path:\n')
logf = open(logf_name, 'rb')
data = logf.read()
packet_type = bytes([0x55, 0x55, 0x53, 0x32])
time_of_week_lst = []
error_num = 0
txtf = open('./s2_parse.txt', 'w+')

def parse_S2(payload):
    gps_fmt = '<HI'
    fmt = '<fffffffI'
    gps_data = struct.unpack(gps_fmt, payload[:6])
    data = struct.unpack(fmt, payload[6:])
    gps_week = gps_data[0]
    gps_time_of_week = gps_data[1]
    # gps_time_of_week = struct.unpack(gps_fmt, payload[:6])[1]
    accels = data[0:3]
    gyros = data[3:6]
    temp = data[6]
    master_bits = data[7]
    # gps_time_stamp = gps_time(gps_week, gps_time_of_week)
    
    return gps_week, gps_time_of_week, accels, gyros, temp, master_bits


for i in range(len(data)):
    header = data[i:i+4]
    if header == packet_type:
        payload = data[i+5:i+43]
        if len(payload) == 38:
            latest = parse_S2(payload)
            txtf.write(f'{latest}\n')
            time_of_week = latest[1]
            time_of_week_lst.append(time_of_week)

for i in range(len(time_of_week_lst)):
    if i + 2 <= len(time_of_week_lst):
        interval = time_of_week_lst[i+1] - time_of_week_lst[i]
    if interval != 10 and i + 2 <= len(time_of_week_lst):
        print(f'error turn: ({i}, {time_of_week_lst[i]}), ({i+1}, {time_of_week_lst[i+1]}), {interval}')
        error_num += 1

print(error_num)