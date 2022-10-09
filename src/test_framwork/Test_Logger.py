import os
import csv

class TestLogger:
    def __init__(self, file_name=None):
        self._file_name = file_name
        self.logf = None
        self._field_names = []

    def create_csv(self, field_names):
        self._field_names = field_names
        data_dir = './result'
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        with open(self._file_name, 'a+') as out_file:
            writer = csv.DictWriter(out_file, fieldnames = field_names)
            writer.writeheader()

    def write2csv(self, info_dicts):
        with open(self._file_name, 'a+') as out_file:
            writer = csv.DictWriter(out_file, fieldnames = self._field_names)
            writer.writerow(info_dicts)

    def creat_binf_sct2(self, file_name, sn_num, test_time):
        data_dir = f'./data/Packet_ODR_test_data/{sn_num}_{test_time}'
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        self.logf = open(file_name, 'wb')

    def cerat_binf_sct5(self, file_name):
        data_dir = f'./data/Packet_long_term_test_data'
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        self.logf = open(file_name, 'wb')

    def write2bin(self, data):
        if data is not None:
            self.logf.write(data)

    
