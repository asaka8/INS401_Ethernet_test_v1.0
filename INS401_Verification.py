from src.conmunicator.INS401_Ethernet import Ethernet_Dev
from src.Ethernet_test.INS401_Test_Center import Test_Environment

def main():
    uut = Ethernet_Dev()
    print("\n#######   INS401 ETHERNET Interface Verification V1.0   #######\n")
    
    result = uut.find_device(times=1)
    if result != True:
        return
    
    result = uut.ping_device()
    if result != True:
        print('Ethernet ping error.')
        return
    
    model = uut.model_string 
    serial_number = uut.serial_number
    version = uut.app_version
    
    print("\n# UUT Model: ", model)
    print("\n# UUT Serial Number: ", serial_number)
    print("\n# UUT Version: ", version)
    print("")

    env = Test_Environment(uut)
    env.setup_tests()
    print("###########  Executing tests...   ##########################\n")
    env.run_tests()
    print("##########  Results   #####################################\n")
    env.print_results()

    file_name = f'./result/test_results_{str(serial_number)}_{str(version)}.csv'
    env.log_results(file_name)


if __name__ == "__main__":

    main()