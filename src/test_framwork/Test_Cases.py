
class Test_Section:
    _section_number = 0

    def __init__(self, section_name):
        self.section_name = section_name
        Test_Section._section_number = Test_Section._section_number + 1
        self.section_id = Test_Section._section_number
        self.test_cases = []
        self.total_test_cases = 0

    def add_test_case(self, test_case):
        self.test_cases.append(test_case)
        self.total_test_cases += 1
        test_case.test_id = self.total_test_cases

    def run_test_section(self):
        print(str(self.section_id) + ". " + self.section_name + "\r\n")
        counter = 0
        for test in self.test_cases:
            counter = counter + 1
            caseID = str(counter)
            if len(caseID) == 1:
                id = f'E{self.section_id}-00{caseID} '
            elif len(caseID) == 2:
                id = f'E{self.section_id}-0{caseID} '
            else:
                id = f'E{self.section_id}-{caseID} '

            test.run_test_case(id)

#############################################

class Test_Case:

    def __init__(self, case_name, handle = None, cmd = None, param = None):
        self.test_case_name = case_name
        self.handle = handle
        self.result = []
        self.cmd = cmd
        self.param = param
        self.test_id = 0

    def _prepare_result(self, response):
        expected_res = ''
        actual_res = ''

        if type(response[1]) is int:
            actual_res = str(response[1])
        elif type(response[1]) is list:
            for i in response[1]:
                if type(i) is int:
                    actual_res += str(i)
                else:
                    actual_res += i
        else:
            actual_res = response[1]

        if type(response[2]) is int:
            expected_res = str(response[2])
        elif type(response[2]) is list:
            for i in response[2]:
                if type(i) is int:
                    expected_res += str(i) + ", "
                else:
                    expected_res += i + ", "
        else:
            expected_res = response[2]

        self.result = { 'id': self.test_id,
                        'test_name': self.test_case_name,
                        'expected': expected_res,
                        'actual': actual_res,
                        'status': response[0]}


    def run_test_case(self, id):
        raise NotImplementedError("Subclass must implement abstract method")
        #print("\t\t" + self.test_case_name + "\r\n")
        #if(self.handle != None):
        #    self.result = self.handle(self.cmd, self.param)

#===========================================#

class Condition_Check(Test_Case):

    def run_test_case(self, id):
        self.test_id = id

        print(id + self.test_case_name + "\r\n")

        if(self.handle != None):
            response = self.handle(self.cmd, self.param)
            self._prepare_result(response)

            test_outcome = id + self.test_case_name + "Expected: "+ self.result['expected'] + " Actual: "+  self.result['actual']  + "\r\n"

            result_str = "Passed" + test_outcome if response[0] else "Failed" +  test_outcome
            #print(result_str)

#===========================================#

class Code(Test_Case):

    def run_test_case(self, id):
        self.test_id = id

        print(id + self.test_case_name + "\r\n")

        if(self.handle != None):

            response = self.handle()
            self._prepare_result(response)
            
            print(self.test_case_name, self.result['expected'], self.result['actual'])

            test_outcome = id + self.test_case_name + "Expected: "+ self.result['expected'] + " Actual: "+  self.result['actual']  + "\r\n"

            result_str = "Passed" + test_outcome if response[0] else "Failed" +  test_outcome
            #print(result_str)

#===========================================#

class Condition_Check_dlc(Test_Case):

    def run_test_case(self, id):
        self.test_id = id

        print(id + self.test_case_name + "\r\n")

        if(self.handle != None):

            response = self.handle(self.cmd)
            self._prepare_result(response)
            
            print(self.test_case_name, self.result['expected'], self.result['actual'])

            test_outcome = id + self.test_case_name + "Expected: "+ self.result['expected'] + " Actual: "+  self.result['actual']  + "\r\n"

            result_str = "Passed" + test_outcome if response[0] else "Failed" +  test_outcome
            #print(result_str)