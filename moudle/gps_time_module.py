'''
https://tool.lu/timestamp/  123
UTC is UTC0 time, 
0-时区 UTC time.localtime: '2020-08-05 10:03:03.815650'
LOCAL: datetime.datetime(2020, 8, 5, 10, 3, 3, 815650)  datetime.datetime.now()
GPS WEEK TIME OF WEEK: 2119, 214365.000  ('UTC-0: 2020-08-18 11:32:27.000000') 
(input_gpstime: [2173, 467631.002]; out_strtime UTC-0: 2021-09-03 09:53:33.002000; out_stamptime2: 1630605213.002;)
LOCAL.timestamp(): 1596592983.81565 自纪元1970以来经过的秒数,说的是UTC-0. 
GPS time: 是1980年开始的周数，秒数。
cur_stamptime UTC-0: 1657777385.4509237; cur_utc_strtime_utc8: 2022-7-14 13:43:5.0; cur_gpstime_utc0: (2218, 4, 366203, 450924);
input_strtime_utc8: 2022-7-14 13:43:5.0; gpstime_utc0: (2218, 4, 366203, 0); stamptime_utc0: 1657777385.0;
input_gpstime_utc0: [2218, 366203]; out_strtime_UTC-0: 2022-07-14 05:43:05.000000; out_stamptime2_utc0: 1657777385.0;
input_stamptime_utc0: 1657777385.4509237; out_utctime_datetime_utc8: 2022-07-14 13:43:05.450924; out_gpstime: (2218, 4, 366203, 450924);
'''


from datetime import datetime, timedelta, timezone
import time, datetime
from tzlocal import get_localzone

import pytz



# 闰秒
LEAP_SECONDS = 18
datetimeformat = "%Y-%m-%d %H:%M:%S.%f"

# UTC时间转本地时间（北京）时间
# 1. 把utc的str转为datetime（无时区信息）
# 2. 添加时区信息为utc时区
# 3. datetime转为时间戳
# 4. 从时间戳得到本地时间datetime
# 输入格式为：'2020-08-05 02:03:03.815650'
# 输出格式为：datetime.datetime.datetime(2020, 8, 5, 10, 3, 3, 815650)
def utc_to_local(utc_time):
    # 得到不包含时区的datetime
    dt_no_tz = datetime.datetime.strptime(utc_time, datetimeformat)
    # 设置时区为UTC
    # timezone.utc与timezone(timedelta(hours=0))一样
    utc_datetime = dt_no_tz.replace(tzinfo=timezone(timedelta(hours=0)))
    t = utc_datetime.timestamp()
    # 根据时间戳得到UTC时间
    # datetime.datetime.utcfromtimestamp(t)
    # 如果要将时间戳转化为东八区datetime
    # fromtimestamp(timestamp, timezone(timedelta(hours=8)))
    # 根据时间戳得到本地时间fromtimestamp(t, tz=None)
    return datetime.datetime.fromtimestamp(t)

# 本地时间转UTC0时间
# 输入格式为：'2020-08-05 10:03:03.815650'
# 输出格式为：datetime.datetime.datetime(2020, 8, 5, 2, 3, 3, 815650)
def local_to_utc(local_time):
    # 得到不包含时区的datetime
    dt_no_tz = datetime.datetime.strptime(local_time, datetimeformat)
    # 设置时区为本地时区（北京，东八区）
    # timezone.utc与timezone(timedelta(hours=0))一样
    local_datetime = dt_no_tz.replace(tzinfo=timezone(timedelta(hours=8)))
    t = local_datetime.timestamp()
    # 根据时间戳得到UTC时间
    # dt_temp = datetime.datetime.utcfromtimestamp(t)
    return local_datetime  #默认减去8小时为UTC8再计算，所以加16


# 输入：GPS周、GPS周内秒、闰秒（可选，gps时间不同，闰秒值也不同，由Leap_Second.dat文件决定）
# 输出：UTC时间（格林尼治时间）
# 输入示例： gps_week_seconds_to_utc(2119, 214365.000)
# 输出示例： '2020-08-18 11:32:27.000000'
def gps_week_seconds_to_strtime(gpsweek, gpsseconds, leapseconds=LEAP_SECONDS):
    epoch = datetime.datetime.strptime("1980-01-06 00:00:00.000", datetimeformat)
    # timedelta函数会处理seconds为负数的情况
    elapsed = timedelta(days=(gpsweek*7), seconds=(gpsseconds-leapseconds))
    # print(elapsed)
    return datetime.datetime.strftime(epoch+elapsed, datetimeformat)


# 输入：UTC时间（datetime类型）
# 输出：GPS周、周内日、周内秒、毫秒  0-Sunday 1-monday
def datetime_to_gps_week_seconds(utc, leapseconds=LEAP_SECONDS, timezone=8):
    epoch = datetime.datetime.strptime("1980-01-06 00:00:00.000", datetimeformat)
    utc_temp = utc.replace(tzinfo=None)
    tdiff = utc_temp - epoch + timedelta(seconds=leapseconds)  #timedelta 按天，秒，微秒来记录差的时间
    gpsweek = tdiff.days // 7
    gpsdays = tdiff.days - 7*gpsweek
    gpsseconds = tdiff.seconds + 86400*(tdiff.days -7*gpsweek)
    return gpsweek, gpsdays, gpsseconds, tdiff.microseconds

def gps_week_seconds(cur_stamptime):
    tz_timezone = get_localzone()
    cur_utctime_datetime = datetime.datetime.fromtimestamp(cur_stamptime) # or datetime.datetime.now()
    dt = pytz.timezone(tz_timezone.zone).localize(cur_utctime_datetime)
    cur_utctime_datetime_utc0 = pytz.utc.normalize(dt.astimezone(pytz.utc))
    cur_gpstime = datetime_to_gps_week_seconds(cur_utctime_datetime_utc0)
    return cur_gpstime

def stamptime_to_structtime(stamptime):
    return time.localtime(stamptime)

def structtime_to_stamptime(structtime):
    return time.mktime(structtime)

def stamptime_to_datetime(stamptime):
    return datetime.datetime.fromtimestamp(stamptime)

def datetime_to_stamptime(datetime2):
    return datetime2.timestamp()

def strtime_to_structtime(strtime, fmt=datetimeformat): 
    '''
    "1980-01-06 00:00:00.000"
    '''
    return time.mktime(time.strptime(strtime, fmt))

def structtime_to_strtime(structtime, fmt=datetimeformat): 
    '''
    return "1980-01-06 00:00:00.000"
    '''
    str = f'{structtime.tm_year}-{structtime.tm_mon}-{structtime.tm_mday} {structtime.tm_hour}:{structtime.tm_min}:{structtime.tm_sec}.{0}'
    return str

def datetime_to_strtime(datetime):
    return datetime.datetime.strftime(datetime, datetimeformat)

def strtime_to_datetime(strtime): 
    '''
    输入格式为：'2020-08-05 10:03:03.815650'
    '''
    return local_to_utc(strtime)


def gps_time(gps_week, gps_timeofweek):
    input_strtime = gps_week_seconds_to_strtime(gps_week, gps_timeofweek)
    out_stamptime = datetime_to_stamptime(utc_to_local(input_strtime))
    return out_stamptime

def get_curr_time():
    currenect_time = datetime.datetime.now()
    return currenect_time

def cal_time_diff(gps_time_ms, current_time):
    time_diff = float(current_time.timestamp()) - gps_time_ms
    return time_diff

if __name__ == "__main__":
    tz_timezone = get_localzone()
    cur_stamptime = time.time()
    cur_utctime_struct = time.localtime()
    cur_utctime_str = structtime_to_strtime(cur_utctime_struct)
    cur_utctime_datetime = datetime.datetime.fromtimestamp(cur_stamptime) # or datetime.datetime.now()
    dt = pytz.timezone(tz_timezone.zone).localize(cur_utctime_datetime)
    cur_utctime_datetime_utc0 = pytz.utc.normalize(dt.astimezone(pytz.utc))
    # str = datetime.datetime.strftime(cur_utctime_datetime, datetimeformat)
    # dttime = strtime_to_datetime(str)
    cur_gpstime = datetime_to_gps_week_seconds(cur_utctime_datetime_utc0)
    print(f'cur_stamptime UTC-0: {cur_stamptime}; cur_utc_strtime_utc8: {cur_utctime_str}; cur_gpstime_utc0: {cur_gpstime};')

    input_strtime = '2022-7-14 13:43:5.0'
    out_stamptime = datetime_to_stamptime(strtime_to_datetime(input_strtime))
    gpstime = datetime_to_gps_week_seconds(datetime.datetime.utcfromtimestamp(out_stamptime))
    print(f'input_strtime_utc8: {input_strtime}; gpstime_utc0: {gpstime}; stamptime_utc0: {out_stamptime};')
    
    input_gpstime = [2218, 366203]  #week number; time of week
    out_strtime = gps_week_seconds_to_strtime(input_gpstime[0],input_gpstime[1])
    out_stamptime2 = datetime_to_stamptime(utc_to_local(out_strtime))
    print(f'input_gpstime_utc0: {input_gpstime}; out_strtime_UTC-0: {out_strtime}; out_stamptime2_utc0: {out_stamptime2};')
    
    input_stamptime = 1657777385.4509237;
    out_utctime_datetime = datetime.datetime.fromtimestamp(input_stamptime) # or datetime.datetime.now()
    out_gpstime = datetime_to_gps_week_seconds(datetime.datetime.utcfromtimestamp(input_stamptime))
    print(f'input_stamptime_utc0: {input_stamptime}; out_utctime_datetime_utc8: {out_utctime_datetime}; out_gpstime: {out_gpstime};')
    pass


