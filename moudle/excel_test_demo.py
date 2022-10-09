import time
from openpyxl import load_workbook

class xlsx_factory:
    def __init__(self) -> None:
        self.wb = load_workbook('./test.xlsx')
        self.ws = self.wb.active
        self.ts0 = self.wb.worksheets[0]
        self.ts1 = self.wb.worksheets[1]
        self.row_dict = {}

    def sheet_row_oprt(self):
        i = 0
        for row in self.ts0.rows:
            i += 1
            row_value = []
            for idx in row:
                value = idx.value
                row_value.append(value)
            self.row_dict.update({i: row_value})
        print(self.row_dict)

xf = xlsx_factory()
xf.sheet_row_oprt()