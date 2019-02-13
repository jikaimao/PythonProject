from PySerialPort import *
from Command import *
from ControlInstrument import *
import numpy as np
import re
def TV_Performance_Test(test_board_type,instrumentType="RSSFU"):
    test_flow = r"TestFlow\TV_TEST_FLOW.txt"
    bypass_mode = False
    SerialObject = None
    InstrumentObject = Instrument(instrumentType)
    if not InstrumentObject.connect_instrument():
        return
    with open(test_flow,"r") as f:
        for i in f.readlines():
            if not string_is_valid(i):
                continue
            if i.find("bypass") != -1:
                print("Enter bypass Mode!\n")
                bypass_mode = True
    if not bypass_mode:
        SerialObject = SerialPort("COM4")
        if not SerialObject.open_status:
            print("Exit test process!\n")
            return
    test_main(instrumentType,InstrumentObject,SerialObject,test_flow,test_board_type,bypass_mode)
    if not bypass_mode:
        SerialObject.close_serial_port_stop_thread()
    InstrumentObject.close_instrument_handle()
def test_main(instrumentType,InstrumentObject,SerialObject,file_name,test_board_type,bypass_mode):
    save_pre_file_data = {}
    with open(file_name,"r") as config_file:
        parameters_list = config_file.readlines()
        for parameter in parameters_list:
            if not string_is_valid(parameter):
                continue
            elif parameter in ["\n","\r","\r\n"]:
                continue
            file_data = dict(zip(parameter.strip().split(":")[::2],
                                             parameter.strip().split(":")[1::2]))
            parmarameters_keys = list(file_data.keys())
            parse_data_set_parameters(instrumentType,test_board_type,parmarameters_keys,
                                          save_pre_file_data,file_data,InstrumentObject,SerialObject)
            if not bypass_mode:
                if "Mode" not in parmarameters_keys:
                    if save_pre_file_data["Mode"] == "DVBT2":
                        DVBT2_PerformanceTest(test_board_type,InstrumentObject,
                                              SerialObject,save_pre_file_data,file_data)
def DVBT2_PerformanceTest(test_board_type,InstrumentObject,
                          SerialObject,save_pre_file_data,file_data):
    parameter_value = 0
    ParametersType = None
    test_case = "{}_{}".format(save_pre_file_data["Mode"],save_pre_file_data["TestCase"])
    if test_board_type == "FPGA":
        cpture_enble = True
    else:
        cpture_enble = False
    if test_case == "DVBT2_FadingPathLoss":
        parameter_value = float(file_data["PathLoss"])
        ParametersType = "PathLoss"
    elif test_case == "DVBT2_AwgnTest":
        parameter_value = float(file_data["AwgnValue"])
        ParametersType = "AwgnValue"
    adjust_parameter_record_result(SerialObject, InstrumentObject,save_pre_file_data,file_data,
                               parameter_value,ParametersType,test_board_type,cpture_enble)
def get_gro_path_value(fadFineNumber):
    if int(fadFineNumber)%5 == 0:
        return (int(int(fadFineNumber)/5),5)
    else:
        return (int(int(fadFineNumber)/5)+1,int(fadFineNumber)%5)

def string_to_list(string):
    value = string.strip().split(",")
    return value
def string_is_valid(target_str):
    for i in ["#","~","$","//","@","*","-","\\"]:
        if target_str.find(i) != -1:
            return False
    return True
def adjust_parameter_record_result(SerialObject, InstrumentObject,save_pre_file_data,file_data,
                                   parameter_value,ParametersType,TestBoardType = "CHIP",cpture_enble = False):
    file_name = r"TestResult\result.log"
    temp = parameter_value
    step = float(save_pre_file_data["Step"])
    if cpture_enble:
        captuer_data(SerialObject)
        if TestBoardType == "FPGA":
            if save_pre_file_data["Mode"] == "DVBT2":
                SerialObject.send_command_to_serial(FPGASerialCommandDict["SetFPGA_T2_Mode"])
                SerialObject.send_command_to_serial(FPGASerialCommandDict["bw_select"][save_pre_file_data["BW"]])
    result = JudgePerLockedResult(SerialObject,TestBoardType,save_pre_file_data)
    direct = confirm_parameters_value_direction(result,save_pre_file_data["TestCase"],ParametersType,temp)
    if result in ("Unlocked", "lockedNotEqual"):
        while True:
            if direct == "UP":
                temp += step
            else:
                temp -= step
            select_send_para_command_type(save_pre_file_data["TestCase"],InstrumentObject,temp,file_data)
            if cpture_enble:
               if save_pre_file_data["Mode"] == "DVBT2":
                   SerialObject.send_command_to_serial(FPGASerialCommandDict["exitMyTool"])
                   captuer_data(SerialObject)
                   SerialObject.send_command_to_serial(FPGASerialCommandDict["SetFPGA_T2_Mode"])
                   SerialObject.send_command_to_serial(FPGASerialCommandDict["bw_select"][save_pre_file_data["BW"]])
            print("Current %s:%.1f\n"%(ParametersType, temp))
            result = JudgePerLockedResult(SerialObject,TestBoardType,save_pre_file_data)
            if result in ("lockedEqual"):
                result_string = "case[%s] %s:%.1f\n"%(save_pre_file_data["CaseNum"], ParametersType, temp)
                print(result_string)
                write_data_to_file(file_name,result_string)
                break
            if record_abnormal_test_result(save_pre_file_data["CaseNum"],ParametersType,temp):
                break
    elif result in ("lockedEqual"):
        while True:
            if direct == "UP":
                temp += step
            else:
                temp -= step
            select_send_para_command_type(test_case,InstrumentObject,temp,file_data)
            if cpture_enble:
                captuer_data(SerialObject)
                if save_pre_file_data["Mode"] == "DVBT2":
                    SerialObject.send_command_to_serial(FPGASerialCommandDict["exitMyTool"])
                    SerialObject.send_command_to_serial(FPGASerialCommandDict["SetFPGA_T2_Mode"])
                    SerialObject.send_command_to_serial(FPGASerialCommandDict["bw_select"][save_pre_file_data["BW"]])
            print("Current %s:%.1f\n"%(ParametersType, temp))
            result = JudgePerLockedResult(SerialObject,TestBoardType,save_pre_file_data)
            if result in ("Unlocked", "lockedNotEqual"):
                result_string = "case[%s] %s:%.1f\n"%(save_pre_file_data["CaseNum"], ParametersType, temp)
                print(result_string)
                write_data_to_file(file_name,result_string)
                break
            if record_abnormal_test_result(test_case,save_pre_file_data["CaseNum"],ParametersType,temp):
                break
def write_data_to_file(file_name,data):
    with open(file_name,"a+") as f:
        f.write(data+"\n") 
def record_abnormal_test_result(case_num,ParametersType,ParametersValue):
    file_name = "result.log"
    if ParametersType == "PowerLevel":
        if ParametersValue > 126 or ParametersValue < -13:
            result_string = "Warning:Abnormal results!case[{}] {}:{}\n".format(case_num, ParametersType, ParametersValue)
            print(result_string)
            write_data_to_file(file_name,result_string)
            return True
    elif ParametersType  == "AwgnValue":
        if ParametersValue > 60 or ParametersValue < -35:
            result_string = "Warning:Abnormal results!case[{}] {}:{}\n".format(case_num, ParametersType, ParametersValue)
            print(result_string)
            write_data_to_file(file_name,result_string)
            return True
    elif ParametersType == "PathLoss":
        if ParametersValue > 50 or ParametersValue < 0:
            result_string = "Warning:Abnormal results!case[{}] {}:{}\n".format(case_num, ParametersType, ParametersValue)
            print(result_string)
            write_data_to_file(file_name,result_string)
            return True
    return False
def confirm_parameters_value_direction(result,test_case,ParametersType,ParametersValue):
    if result in ("Unlocked", "lockedNotEqual"):
        print("Current {}:{}\n".format(ParametersType, ParametersValue))
        if test_case in ("FadingPathLoss"):
            print("Adjust parameters_direction:UP\n")
            return "UP"
        elif test_case in ("MaxLevelTest"):
            print("Adjust parameters_direction:DOWN\n")
            return "DOWN"
    elif result is "lockedEqual":
        print("Current {}:{}\n".format(ParametersType, ParametersValue))
        if test_case in ("FadingPathLoss"):
            print("Adjust parameters_direction:DOWN\n")
            return "DOWN"
        elif test_case in ("MaxLevelTest"):
            print("Adjust parameters_direction:UP\n")
            return "UP"
def select_send_para_command_type(test_case,InstrumentObject,ParametersValue,file_data):
    if test_case in ("MaxLevelTest", "MinLevelTest"):
        InstrumentObject.set_instrument_level(ParametersValue, "dBuV")
        return
    elif test_case in ("AwgnTest"):
        awgn_command = DVBC_Set_InstrumentDict["SetAwgn"] + str(ParametersValue) + "\n"
        InstrumentObject.set_other_command(awgn_command)
        return
    elif test_case in ("FadingPathLoss"):
        gro,path = get_gro_path_value(file_data["FadingFine"])
        InstrumentObject.set_fader_pathloss(gro,path,ParametersValue)
        return
def captuer_data(SerialObject):
    print("75 init......\n")
    SerialObject.send_command_to_serial(FPGASerialCommandDict["Capture_date"])
    if not SerialObject.get_capture_date_status():
        for i in range(3):
            print("Capture data again....\n")
            SerialObject.send_command_to_serial(FPGASerialCommandDict["Capture_date"])
            if SerialObject.get_capture_date_status():
                break

def JudgePerLockedResult(SerialObject,TestBoardType,save_pre_file_data):
    if TestBoardType == "CHIP":
        time.sleep(LockedDelay)
    LockStatus = SerialObject.get_locked_status()
    if TestBoardType == "FPGA":
        if save_pre_file_data["Mode"] == "DVBT2":
            if not LockStatus:
                for i in range(2):
                    SerialObject.send_command_to_serial(FPGASerialCommandDict["exitMyTool"])
                    SerialObject.send_command_to_serial(FPGASerialCommandDict["SetFPGA_T2_Mode"])
                    SerialObject.send_command_to_serial(FPGASerialCommandDict["bw_select"][save_pre_file_data["BW"]])
                    LockStatus = SerialObject.get_locked_status()
                    if LockStatus:
                        return getPerValueAndStatus(SerialObject,LockStatus)
                return getPerValueAndStatus(SerialObject,LockStatus)
    elif TestBoardType == "CHIP":
        SerialObject.send_command_to_serial(GetLockStatus)
        return getPerValueAndStatus(SerialObject,LockStatus)
        
def getPerValueAndStatus(SerialObject,lockedStatus):
    perList = []
    if lockedStatus:
        for cnt in range(5):
            time.sleep(ReadPerGuardTime)
            perList.append(SerialObject.getPerValue(GetPerValue))
            if cnt >= 1:
                if abs(int(perList[cnt]) - int(perList[cnt - 1])) > 1:
                    return "lockedNotEqual"  # locked but is not equal
        else:
            return "lockedEqual"
    else:
        return "Unlocked"
def parse_data_set_parameters(instrumentType,test_board_type,parmarameters_keys,save_pre_file_data,file_data,InstrumentObject,SerialObject):
    if "Mode" in parmarameters_keys:
        for status in ["FadingOFF","NoiseOFF"]:
            InstrumentObject.set_other_command(InstrumentCommandDict[status])
        if instrumentType == "RSSFU":
            for status in ["ModeON", "SFU_DTV"]:
                InstrumentObject.set_other_command(InstrumentCommandDict[status])
        InstrumentObject.set_standard_to_instrument(InstrumentStandardDict[instrumentType][file_data["Mode"]])
        save_pre_file_data.update(file_data)
        save_pre_file_data["FadingSetTimes"] = 0
        if file_data["Mode"] == "DVBT2" and test_board_type == "FPGA":
            SerialObject.send_command_to_serial(FPGASerialCommandDict["enterMyTool"])
            SerialObject.send_command_to_serial(FPGASerialCommandDict["SetFPGA_DVBT_Mode"])
    if "CaseNum" in parmarameters_keys:
        save_pre_file_data["CaseNum"] = file_data["CaseNum"]
    if "TestCase" in parmarameters_keys:
        save_pre_file_data["TestCase"] = file_data["TestCase"]
    if "Frequence" in parmarameters_keys:
        print(file_data["Frequence"])
        InstrumentObject.set_instrument_freq(file_data["Frequence"],"MHz")
    if "PowerLevel" in parmarameters_keys:
        print(file_data["PowerLevel"])
        InstrumentObject.set_instrument_level(file_data["PowerLevel"],"dBuV")
    if "Modulation" in parmarameters_keys:
        modulation_command = Instrument_Setting_Command[instrumentType][save_pre_file_data["Mode"]]["Modulation"][file_data["Modulation"]]
        print(modulation_command)
        InstrumentObject.set_other_command(modulation_command)
    if "FFT" in parmarameters_keys:
        fft_command = Instrument_Setting_Command[instrumentType][save_pre_file_data["Mode"]]["FFT"][file_data["FFT"]]
        print(fft_command)
        InstrumentObject.set_other_command(fft_command)
    if "GI" in parmarameters_keys:
        gi_command = Instrument_Setting_Command[instrumentType][save_pre_file_data["Mode"]]["GI"][file_data["GI"]]
        print(gi_command)
        InstrumentObject.set_other_command(gi_command)
    if "CodeRate" in parmarameters_keys:
        code_command = Instrument_Setting_Command[instrumentType][save_pre_file_data["Mode"]]["CodeRate"][file_data["CodeRate"]]
        InstrumentObject.set_other_command(code_command)
        print(code_command)
    if "Pilot" in parmarameters_keys:
        pilot_command = Instrument_Setting_Command[instrumentType][save_pre_file_data["Mode"]]["Pilot"][file_data["Pilot"]]
        print(pilot_command)
        InstrumentObject.set_other_command(pilot_command)
    if "BW" in parmarameters_keys:
        save_pre_file_data["BW"] = file_data["BW"]
        bw_command = Instrument_Setting_Command[instrumentType][save_pre_file_data["Mode"]]["BW"] + file_data["BW"] + "\n"
        print(bw_command)
        InstrumentObject.set_other_command(bw_command)
    if "WorkMode" in parmarameters_keys:
        work_mode_list = Instrument_Setting_Command[instrumentType][save_pre_file_data["Mode"]]["WorkMode"][file_data["WorkMode"]]
        for command in work_mode_list:
            InstrumentObject.set_other_command(command)
        print("WorkMode:%s\n"%file_data["WorkMode"])
    if "FadingFine" in parmarameters_keys:
        save_pre_file_data["FadingSetTimes"] += 1
        if save_pre_file_data["FadingSetTimes"] < 2:
            InstrumentObject.set_fader_default()
            InstrumentObject.set_other_command(InstrumentCommandDict["FadingON"])
            InstrumentObject.set_fading_reference()
        fadFineList = string_to_list(file_data["FadingFine"])
        for i in range(len(fadFineList)):
            gro,path = get_gro_path_value(fadFineList[i])
            if "ProfileType" in parmarameters_keys: # 1-->static 2-->Rice 3-->Doopler 4-->Raily
                profile_type = string_to_list(file_data["ProfileType"])
                InstrumentObject.set_fader_profile_status("ON",gro,path,ProfileTypeDict[profile_type[i]])
            if "Doopler" in parmarameters_keys:
                dooplerValue = string_to_list(file_data["Doopler"])
                if float(dooplerValue[i]) > 0:
                    print("Doopler Fine{} Path{} Value:{}".format(gro,path,dooplerValue[i]))
                    InstrumentObject.set_fader_doppler(gro,path,dooplerValue[i])
                else:
                    InstrumentObject.set_fader_doppler(gro,path,0)
            if "PathLoss" in parmarameters_keys:
                path_loss = string_to_list(file_data["PathLoss"])
                if float(path_loss[i]) > 0:
                    InstrumentObject.set_fader_pathloss(gro,path,path_loss[i])
                    print("PathLoss Fine{} Path{} Value:{}".format(gro,path,path_loss[i]))
                else:
                    InstrumentObject.set_fader_pathloss(gro,path,path_loss[i])
            if "BasicDelay" in parmarameters_keys:
                basic_delay = string_to_list(file_data["BasicDelay"])
                if float(basic_delay[i]) > 0:
                    InstrumentObject.set_basic_delay(gro,float(basic_delay[i]))
                    print("BasicDelay Fine{} Path{} Value:{}".format(gro,path,basic_delay[i]))
                else:
                    InstrumentObject.set_basic_delay(gro,float(basic_delay[i]))
            if "ConstPhase" in parmarameters_keys:
                deg_value = string_to_list(file_data["ConstPhase"])
                print("Const Phase Fine{} Path{} Value:{}".format(gro,path,deg_value[i]))
                InstrumentObject.set_const_phase(gro,path,deg_value[i])
    if "SymbolRate" in parmarameters_keys:
        symbol_command= Instrument_Setting_Command[instrumentType][save_pre_file_data["Mode"]]["SymbolRate"] + file_data["SymbolRate"] + "e6\n"
        InstrumentObject.set_other_command(symbol_command)
    if "AwgnValue" in parmarameters_keys:
        InstrumentObject.set_other_command(InstrumentCommandDict["NoiseADD"])
        InstrumentObject.set_other_command(InstrumentCommandDict["NoiseAWGN_ON"])
        awgn_command_string = Instrument_Setting_Command[instrumentType][save_pre_file_data["Mode"]]["AwgnValue"] + file_data["AwgnValue"] + "\n"
        InstrumentObject.set_other_command(awgn_command_string)
    if "Step" in parmarameters_keys:
        save_pre_file_data["Step"] = file_data["Step"]
def DVBT_T2_function_test(used_instype, fpga_mode):  # fpga_mode "T1":DVBT  "T2":DVBT2
    print("-*-*-*-*-*-*-*-*-*-*-*-*-DVT2 Function Test-*-*-*-*-*-*-*-*-*-*-*-*-")
    InstrumentObject = Instrument(used_instype)
    DVBT_T2_FPGA_Serial = SerialPort("COM4")
    if DVBT_T2_FPGA_Serial.open_status == False:
        print("Exit test process!\n")
        return
    if InstrumentObject.connect_instrument() == False:
        return
    if used_instype == "SFU":
        InstrumentObject.set_other_command(InstrumentCommandDict["ModeON"])
        InstrumentObject.set_other_command(InstrumentCommandDict["SFU_DTV"])
        if fpga_mode == "T1":
            InstrumentObject.set_standard_to_instrument(SFU_StandardDict["DVBT"])
        elif fpga_mode == "T2":
            InstrumentObject.set_standard_to_instrument(SFU_StandardDict["DVBT2"])
    elif used_instype == "BTC":
        InstrumentObject.set_other_command(InstrumentCommandDict["BTC_DTV"])
        if fpga_mode == "T1":
            InstrumentObject.set_standard_to_instrument(BTC_StandardDict["DVBT"])
        elif fpga_mode == "T2":
            InstrumentObject.set_standard_to_instrument(BTC_StandardDict["DVBT2"])
    if fpga_mode == "T1":
        test_case_file_name = "T1_Function_test_case.txt"
        test_report_name = "T1_Function_test_report.txt"
        DVBT_T2_FPGA_CommandList = ["Capture_date", "SetFPGA_T1_Mode", "bw_select"]
        Set_Instrument_command = T1_Set_Instrument_command
    elif fpga_mode == "T2":
        test_case_file_name = "T2_Function_test_case.txt"
        test_report_name = "T2_Function_test_report.txt"
        DVBT_T2_FPGA_CommandList = ["Capture_date", "SetFPGA_T2_Mode", "bw_select"]
        Set_Instrument_command = T2_Set_Instrument_command
    InstrumentObject.set_instrument_freq(666, "MHz")
    InstrumentObject.set_instrument_level(-28, "dbm")
    InstrumentObject.set_other_command(InstrumentCommandDict["NoiseOFF"])
    InstrumentObject.set_other_command(InstrumentCommandDict["FadingOFF"])
    DVBT_T2_FPGA_Serial.send_command_to_serial(FPGASerialCommandDict["SetFPGA_DVBT_Mode"])
    with open(test_case_file_name, "r") as testcase_file:
        case_num = 1
        for i in iter(testcase_file.readlines()):
            print("case:%d\n" % case_num)
            for parameter in iter(i.strip().split(":")):
                InstrumentObject.set_other_command(Set_Instrument_command[parameter])
            for serial_command in DVBT_T2_FPGA_CommandList:
                if serial_command == "bw_select":
                    DVBT_T2_FPGA_Serial.send_command_to_serial(FPGASerialCommandDict[serial_command]["8M"])
                    if fpga_mode == "T2":
                        with open(test_report_name, "a+") as f_report:
                            if DVBT_T2_FPGA_Serial.get_locked_status() == True:
                                print(i.strip() + "  Pass\n")
                                f_report.write(i.strip() + "  Pass\n")
                            else:
                                print(i.strip() + "  Failed\n")
                                f_report.write(i.strip() + "  Failed\n")
                else:
                    DVBT_T2_FPGA_Serial.send_command_to_serial(FPGASerialCommandDict[serial_command])
                if serial_command == "Capture_date":
                    DVBT_T2_FPGA_Serial.adjust_capture_date_status()
            DVBT_T2_FPGA_Serial.send_command_to_serial(FPGASerialCommandDict["exitMyTool"])
    DVBT_T2_FPGA_Serial.close_serial_port_stop_thread()
    InstrumentObject.close_instrument_handle()


if __name__ == "__main__":
    # DVBT_T2_function_test("BTC", "T2")
    #DVBC_FGPA_PerformanceTest()
    TV_Performance_Test("FPGA","BTC")
