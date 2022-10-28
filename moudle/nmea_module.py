import pynmea2

def get_latitude(gngga_str):
    gngga = pynmea2.parse(gngga_str)
    return gngga.latitude, gngga.lat_dir

def get_longitude(gngga_str):
    gngga = pynmea2.parse(gngga_str)
    return gngga.longitude, gngga.lon_dir

def get_position_type(gngga_str):
    gngga = pynmea2.parse(gngga_str)
    return gngga.gps_qual

def get_talker(gngga_str):
    gngga = pynmea2.parse(gngga_str)
    return gngga.talker

def get_sentence_type(gngga_str):
    gngga = pynmea2.parse(gngga_str)
    return gngga.sentence_type

if __name__ == "__main__":
    nmea_gngga_str = "$GNGGA,055308.00,3129.6553688,N,12021.7767500,E,1,17,1.0,113.200,M,6.809,M,0.0,*68"
    gngga = pynmea2.parse(nmea_gngga_str)
    print(gngga)
    print(f"utc={gngga.timestamp}")
    print(f'latitude={gngga.lat}')
    print(f'latitude float={gngga.latitude}')
    print(f'Latitude Direction={gngga.lat_dir}')
    print(f'longiture={gngga.lon}')
    print(f'longiture float={gngga.longitude}')
    print(f'Longiture Direction={gngga.lon_dir}')

