import os
import json
import struct

JSON_DATA = {
    "productINFO": "INS401 5020-4007-01 2209003197 Hardware v2.0 IMU_SN 2179100249 RTK_INS App v28.04.23 Bootloader v01.02 IMU330NL FW v27.01.01 STA9100 FW v5.10.18.1"

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