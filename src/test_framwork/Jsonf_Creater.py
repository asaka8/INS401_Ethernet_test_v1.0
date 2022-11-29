import os
import json
import struct

JSON_DATA = {
    "productINFO": "INS401 5020-4007-01 2209003197 Hardware v2.0 IMU_SN 2179100249 RTK_INS App v28.04.23 Bootloader v01.02 IMU330NL FW v27.01.01 STA9100 FW v5.10.18.1",
    "userId":[
        {
            "ID": 1,
            "name": "pri lever arm x",
            "value": 0.5
        },
        {
            "ID": 2,
            "name": "pri lever arm y",
            "value": 0.5
        },
        {
            "ID": 3,
            "name": "pri lever arm z",
            "value": 0.5
        },
        {
            "ID": 4,
            "name": "vrp lever arm x",
            "value": -0.5
        },
        {
            "ID": 5,
            "name": "vrp lever arm y",
            "value": -0.5
        },
        {
            "ID": 6,
            "name": "vrp lever arm z",
            "value": -0.5
        },
        {
            "ID": 7,
            "name": "user lever arm x",
            "value": 0.5
        },
        {
            "ID": 8,
            "name": "user lever arm y",
            "value": 0.5
        },
        {
            "ID": 9,
            "name": "user lever arm z",
            "value": 0.5
        },
        {
            "ID": 10,
            "name": "rotation rbvx",
            "value": 180
        },
        {
            "ID": 11,
            "name": "rotation rbvy",
            "value": 180
        },
        {
            "ID": 12,
            "name": "rotation rbvz",
            "value": 180
        },
        {
            "ID": 13,
            "name": "odo enable",
            "value":0
        },
        {
            "ID":14,
            "name": "vehicle code",
            "value": 0
        }
    ],
    "vehicle code":{
        "vcode version": 2.0, 
        "vcode params": {
            "VF33": [-1.683913, 0.48179, -1.053507, -1.464094, 0.140739, 0.057258, -1.464094, 0.140739, 0.057258, 0.0, 0.0, -90.0],
            "VF34": [-1.995312, 0.504686, -1.044098, -1.556083, 0.140739, 0.058229, -1.556083, 0.140739, 0.058229, 0.0, 0.0, -90.0],
            "VF35": [-2.036016, -0.3862, -0.903368, -1.6835, -0.00416, 0.275406, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            "VF36": [-2.57937, -0.376738, -1.017361, -1.801946, 0.004086, 0.173387, 0.0, 0.0, 0.0, 0.0, -12.0, 180.0]
        }    
    },
    "long term test":{
        "LONGTERM_RUNNING_COUNT": 1000,
        "LONGTERM_RUNNING_TIME": 60,
        "TypeFilter": [0x010a, 0x020a, 0x030a, 0x050a]
    },
    "static test":{
        "STATIC_RUNNING_TIME": 60,
        "TypeFilter": [0x010a, 0x020a, 0x030a, 0x050a, 'GNGGA', 'GNZDA']
    },
    "NMEA":{
        "latitude": 31.494,
        "latitude_dev": 0.005,
        "latitude_dir": 'N',
        "longitude": 120.362,
        "longitude_dev": 0.005,
        "longitude_dir": 'E',
        "position type": 4
    }
    }

class Json_Creat:
    def __init__(self) -> None:
        pass

    def creat(self):
        setting_dir = './setting'
        if not os.path.exists(setting_dir):
            os.mkdir(setting_dir)
        json_dir = './setting/test_params_setting.json'
        if not os.path.exists(json_dir):
            json.dump(JSON_DATA, open(json_dir, 'w'), indent=4)
            with open(json_dir) as json_file:
                properties = json.load(json_file)
        else:
            with open(json_dir) as json_file:
                properties = json.load(json_file)
        return properties