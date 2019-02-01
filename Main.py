from PySerialPort import *
from Command import *
from ControlInstrument import *
import numpy as np
import re
case_num = 1
test_case_list = []
def TV_Performance_Test(test_board_type,instrumentType="RSSFU"):
    test_flow = "DVBC_TEST_FLOW.txt"
    bypass_mode = False
    InstrumentObject = Instrument(instrumentType)
    if not InstrumentObject.connect_instrument():
        return
    SerialObject = SerialPort("COM4")
    if not SerialObject.open_status:
        print("Exit test process!\n")
        return
    with open(test_flow,"r") as f:
        for i in f.readlines():
            if i.find("bypass") != -1:
                print("Enter bypass Mode!\n")
                bypass_mode = True
    if not bypass_mode:
        if test_board_type == "FPGA":
            SerialObject.send_command_to_serial(FPGASerialCommandDict["enterMyTool"])
            SerialObject.send_command_to_serial(FPGASerialCommandDict["SetFPGA_DVBT_Mode"])
        elif test_board_type == "CHIP":
            SerialObject.send_command_to_serial(DTMB_CHIP_Serial_commandDict["enterMyTool"])
    test_main(instrumentType,InstrumentObject,SerialObject,test_flow,test_board_type,bypass_mode)
    InstrumentObject.close_instrument_handle()
    SerialObject.close_serial_port_stop_thread()
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
            if "Mode" in parmarameters_keys:
                for status in ["FadingOFF","NoiseOFF"]:
                    InstrumentObject.set_other_command(InstrumentCommandDict[status])
                if instrumentType == "RSSFU":
                    for status in ["ModeON", "SFU_DTV"]:
                        InstrumentObject.set_other_command(InstrumentCommandDict[status])
                InstrumentObject.set_standard_to_instrument(InstrumentStandardDict[instrumentType][file_data["Mode"]])
                save_pre_file_data = file_data
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
                bw_command = Instrument_Setting_Command[instrumentType][save_pre_file_data["Mode"]]["BW"]
                print(bw_command)
                #InstrumentObject.set_other_command(bw_command)
            if "WorkMode" in parmarameters_keys:
                work_mode_list = Instrument_Setting_Command[instrumentType][save_pre_file_data["Mode"]]["WorkMode"][file_data["WorkMode"]]
                for command in work_mode_list:
                    InstrumentObject.set_other_command(command)
                print("WorkMode:%s\n"%file_data["WorkMode"])
            if "FadingFine" in parmarameters_keys:
                InstrumentObject.set_fader_default()
                InstrumentObject.set_other_command(InstrumentCommandDict["FadingON"])
                InstrumentObject.set_fading_reference()
                fadFineList = string_to_list(file_data["FadingFine"])
                for i in range(len(fadFineList)):
                    gro,path = get_gro_path_value(fadFineList[i])
                    if "Static" in parmarameters_keys:
                        static_value = string_to_list(file_data["Static"])
                        if int(static_value[i]) > 0:
                            InstrumentObject.set_fader_profile_status("ON",gro,path,"SPAT")
                            print("Static Fine{} Path{}".format(gro,path))
                    if "Rice" in parmarameters_keys:
                        rice_value = string_to_list(file_data["Rice"])
                        if int(rice_value[i]) > 0:
                            InstrumentObject.set_fader_profile_status("ON",gro,path,"RICE")
                            print("Rice Fine{} Path{}".format(gro,path))
                    if "Doopler" in parmarameters_keys:
                        dooplerFine = string_to_list(file_data["Doopler"])
                        if float(dooplerFine[i]) > 0:
                            InstrumentObject.set_fader_profile_status("ON",gro,path,"PDOP")
                            print("Doopler Fine{} Path{}".format(gro,path))
                    if "DooplerValue" in parmarameters_keys:
                        dooplerValue = string_to_list(file_data["DooplerValue"])
                        if float(dooplerValue[i]) > 0:
                            print("Doopler Fine{} Path{} Value:{}".format(gro,path,dooplerValue[i]))
                            InstrumentObject.set_fader_doppler(gro,path,dooplerValue[i])
                    if "PathLoss" in parmarameters_keys:
                        path_loss = string_to_list(file_data["PathLoss"])
                        if float(path_loss[i]) > 0:
                            InstrumentObject.set_fader_pathloss(gro,path,path_loss[i])
                            print("PathLoss Fine{} Path{} Value:{}".format(gro,path,path_loss[i]))
                    if "BasicDelay" in parmarameters_keys:
                        basic_delay = string_to_list(file_data["BasicDelay"])
                        if float(basic_delay[i]) > 0:
                            InstrumentObject.set_basic_delay(gro,float(basic_delay[i]))
                            print("BasicDelay Fine{} Path{} Value:{}".format(gro,path,basic_delay[i]))
            if "SymbolRate" in parmarameters_keys:
                symbol_command= Instrument_Setting_Command[instrumentType][save_pre_file_data["Mode"]]["SymbolRate"] + file_data["SymbolRate"] + "e6\n"
                InstrumentObject.set_other_command(symbol_command)
            if "AwgnValue" in parmarameters_keys:
                InstrumentObject.set_other_command(InstrumentCommandDict["NoiseADD"])
                InstrumentObject.set_other_command(InstrumentCommandDict["NoiseAWGN_ON"])
                awgn_value = string_to_list(file_data["AwgnValue"])
                parameter_type = "AWGN"
                awgn_command_string = Instrument_Setting_Command[instrumentType][save_pre_file_data["Mode"]]["AwgnValue"] + file_data["AwgnValue"] + "\n"
                InstrumentObject.set_other_command(awgn_command_string)
            if not bypass_mode:
                if save_pre_file_data["Mode"] == "DVBC":
                    DVBC_PerformanceTest(test_board_type,InstrumentObject,SerialObject)
                elif save_pre_file_data["Mode"] == "DVBT2":
                    DVBT2_PerformanceTest(test_board_type,parameter_type,InstrumentObject,SerialObject,file_data)
                elif save_pre_file_data["Mode"] == "DVBT":
                    pass
                elif save_pre_file_data["Mode"] == "J83B":
                    pass
                elif save_pre_file_data["Mode"] == "DTMB":
                    DTMB_PerformanceTest(test_board_type,parameter_type,InstrumentObject,SerialObject,save_pre_file_data,file_data)
def get_gro_path_value(fadFineNumber):
    if int(fadFineNumber)%5 == 0:
        return (int(int(fadFineNumber)/5),5)
    else:
        return (int(int(fadFineNumber)/5)+1,int(fadFineNumber)%5)
def DVBC_PerformanceTest(test_board_type,InstrumentObject,SerialObject):
    pass
def DVBT2_PerformanceTest(test_board_type,parameter_type,InstrumentObject,SerialObject,file_data):
        test_case = "{}_{}".format(file_data["Mode"],file_data["TestCase"])
        
        adjust_parameter_record_result(SerialObject, InstrumentObject, test_case,
                                       float(file_data["AwgnValue"]), parameter_type,
                                       float(file_data["Step"]),file_data["BW"],TestBoardType = "FPGA",cpture_enble = True)
def DTMB_PerformanceTest(test_board_type,parameter_type,InstrumentObject,SerialObject,save_pre_file_data,file_data):
    test_case = "{}_{}".format(save_pre_file_data["Mode"],save_pre_file_data["TestCase"])
    step = float(save_pre_file_data["Step"])
    if test_case == "DTMB_AWGN_TEST":
        parameter_value = float(file_data["AwgnValue"])
        ParametersType = "AWGN"
    adjust_parameter_record_result(SerialObject, InstrumentObject, test_case,parameter_value,ParametersType,step)

def string_to_list(string):
    value = string.strip().split(",")
    if len(value) == 1:
        return value[0]
    return value
def string_is_valid(target_str):
    for i in ["#","~","$","//","@","*","-","\\"]:
        if target_str.find(i) != -1:
            print("String in the file contains illegal characters (%s)!\n"%i)
            return False
    return True
def set_instrument_command_times(case_list):
    length = len(case_list)
    if length > 1:
        if case_list[length-1]  != case_list[length-1]:
            return True
    return False
def count_case_appears_times(case_name, target_case):
    test_case_list.append(case_name)
    return test_case_list.count(target_case)
def DVBC_FGPA_PerformanceTest(instrumentType="RSSFU"):  # parameter "BTC" "RSSFU"
    file_name = "result.log"
    SFU = Instrument(instrumentType)
    if not SFU.connect_instrument():
        return
    for status in ["ModeON", "SFU_DTV"]:
        SFU.set_other_command(InstrumentCommandDict[status])
    SFU.set_standard_to_instrument(SFU_StandardDict["DVBC"])
    CHIP_Serial = SerialPort("COM4")
    if not CHIP_Serial.open_status:
        print("Exit test process!\n")
        return
    CHIP_Serial.send_command_to_serial(DVBC_CHIP_Serial_commandDict["enterMyTool"])
    CHIP_Serial.send_command_to_serial(DVBC_CHIP_Serial_commandDict["DvbcMode"])
    # DVBC_Modulation_test(SFU,CHIP_Serial)
    with open("DVBC_TEST_FLOW.txt", "r") as test_case:
        for i in test_case.readlines():
            case_name = i.strip().split(":")[0]
            if case_name in ["DVBC_AWGN_TEST"]:
                if count_case_appears_times(case_name, case_name) < 2:
                    print("Current Test case[{}]\n".format(case_name))
                    for status in ["FadingOFF","NoiseADD","NoiseAWGN_ON"]:
                        SFU.set_other_command(InstrumentCommandDict[status])
                write_data_to_file(file_name,i.strip())
                DvbcAwgnTest(SFU, CHIP_Serial, i.strip().split(":"))
            elif case_name in ["DVBC_MINRXLEVEl_TEST", "DVBC_MAXRXLEVEl_TEST"]:
                if count_case_appears_times(case_name, case_name) < 2:
                    print("Current Test case[{}]\n".format(case_name))
                    for status in ["NoiseOFF", "FadingOFF"]:
                        SFU.set_other_command(InstrumentCommandDict[status])
                write_data_to_file(file_name,i.strip())
                DVBC_RecvPowLevelRange(SFU, CHIP_Serial, i.strip().split(":"))
            elif case_name in ["DVBC_E/D_TEST","DVBC_E/D_FIVE_ROAD_TEST"]:
                if count_case_appears_times(case_name, case_name) < 2:
                    print("Current Test case[{}]\n".format(case_name))
                    SFU.set_fader_default()
                    for status in ["NoiseOFF", "FadingON"]:
                        SFU.set_other_command(InstrumentCommandDict[status])
                    SFU.set_fader_profile_status("ON", 1, 1, "SPAT")
                    SFU.set_fader_profile_status("ON", 2, 1, "SPAT")
                write_data_to_file(file_name,i.strip())
                DVBC_E_D_Test(SFU, CHIP_Serial,i.strip().split(":"))
            elif case_name in ["DVBC_SYMBOLRATE_TEST","DVBC_SYMBOLRATECAP_TEST"]:
                if count_case_appears_times(case_name, case_name) < 2:
                    print("Current Test case[{}]\n".format(case_name))
                    for status in ["NoiseOFF","FadingOFF"]:
                        SFU.set_other_command(InstrumentCommandDict[status])
                DVBC_SymbolRate_test(SFU, CHIP_Serial,i.strip().split(":"))
            elif case_name in ["DVBC_FREQUENCE_TEST","DVBC_FREQUENCECAP_TEST"]:
                if count_case_appears_times(case_name, case_name) < 2:
                    print("Current Test case[{}]\n".format(case_name))
                    for status in ["NoiseOFF","FadingOFF"]:
                        SFU.set_other_command(InstrumentCommandDict[status])
                DVBC_Freq_test(SFU, CHIP_Serial,i.strip().split(":"))   
    CHIP_Serial.close_serial_port_stop_thread()
    SFU.close_instrument_handle()

def DVBC_Set_Instrument_Serial_func(InstrumentObject, SerialObject,parametes_value_index):
    #set instrument freq/power level/symbolrate/modulation serial freq/modulation/symbolrate
    set_symbol_str = DVBC_Set_InstrumentDict["DVBC_SymbolRate"] + parametes_value_index["symbol_rate"] + "e6\n"
    InstrumentObject.set_instrument_level(parametes_value_index["power_level"], "dBuV")
    InstrumentObject.set_instrument_freq(parametes_value_index["freq"], "MHz")
    InstrumentObject.set_other_command(DVBC_Set_InstrumentDict[parametes_value_index["modulation"]])
    InstrumentObject.set_other_command(set_symbol_str)
    SerialObject.send_command_to_serial(DVBC_CHIP_Serial_commandDict["SetFreq"])
    if parametes_value_index["test_case"] in ["DVBC_FREQUENCECAP_TEST"]:
        frq_command = "474000\r"
    else:
        frq_command = "{}\r".format(int(float(parametes_value_index["freq"]) * 1000))
    SerialObject.send_command_to_serial([frq_command])
    time.sleep(1)
    SerialObject.send_command_to_serial(DVBC_CHIP_Serial_commandDict["SetModulation"])
    SerialObject.send_command_to_serial(DVBC_CHIP_Serial_commandDict[parametes_value_index["modulation"]])
    if parametes_value_index["test_case"] in ["DVBC_SYMBOLRATECAP_TEST"]:
        SerialObject.send_command_to_serial(["6875\r"])
    else:
        SerialObject.send_command_to_serial([str(int(float(parametes_value_index["symbol_rate"]) * 1000)) + "\r"]) 
    SerialObject.send_command_to_serial(DVBC_CHIP_Serial_commandDict["SelectDvbc"])
    
def DVBC_E_D_Test(InstrumentObject, SerialObject, parametes_list):  # include five road test
    parameters_name = ["test_case", "modulation", "power_level", "freq", "symbol_rate",
                       "pathloss1", "basic_delay","step"]
    parametes_value_index = dict(zip(parameters_name, parametes_list))
    InstrumentObject.set_fader_pathloss(2,1,parametes_value_index["pathloss1"])
    InstrumentObject.set_basic_delay(2,float(parametes_value_index["basic_delay"]))
    DVBC_Set_Instrument_Serial_func(InstrumentObject, SerialObject,parametes_value_index)
    adjust_parameter_record_result(SerialObject, InstrumentObject, parametes_value_index["test_case"],
                                   float(parametes_value_index["pathloss1"]),
                                   "PATHLOSS", float(parametes_value_index["step"]))
def DvbcAwgnTest(InstrumentObject, SerialObject, parametes_list):
    parameters_name = ["test_case", "modulation",
                       "power_level", "freq", "symbol_rate", "awgn", "step"]
    parametes_value_index = dict(zip(parameters_name, parametes_list))
    awgn_command = DVBC_Set_InstrumentDict["SetAwgn"] + parametes_value_index["awgn"] + "\n"
    InstrumentObject.set_other_command(awgn_command)
    DVBC_Set_Instrument_Serial_func(InstrumentObject, SerialObject,parametes_value_index)
    adjust_parameter_record_result(SerialObject, InstrumentObject, parametes_value_index["test_case"],
                                   float(parametes_value_index["awgn"]),
                                   "AWGN", float(parametes_value_index["step"]))
def DVBC_Modulation_test(InstrumentObject, SerialObject):
    global case_num
    test_report = open("result.log", "a+")
    for i in iter(["ModeON", "SFU_DTV", "NoiseOFF", "FadingOFF"]):
        InstrumentObject.set_other_command(InstrumentCommandDict[i])
    InstrumentObject.set_instrument_freq(474, "MHz")
    InstrumentObject.set_instrument_level(60, "dBuV")
    for modu in ["16QAM", "32QAM", "64QAM", "256QAM"]:
        for symbol in [6875, 5057]:
            InstrumentObject.set_other_command(DVBC_Set_InstrumentDict[modu])
            set_symbol_str = DVBC_Set_InstrumentDict["DVBC_SymbolRate"] + str(symbol) + "e6\n"
            InstrumentObject.set_other_command(set_symbol_str)
            SerialObject.send_command_to_serial(DVBC_CHIP_Serial_commandDict["SetModulation"])
            SerialObject.send_command_to_serial(DVBC_CHIP_Serial_commandDict[modu])
            SerialObject.send_command_to_serial([str(symbol) + "\r"])
            result = JudgePerLockedResult(SerialObject)
            if result in ["lockedNotEqual", "Unlocked"]:
                print("case[{}] Modulation:{},SymbolRate:{},result:Fail\n".format(case_num,modu, symbol))
                test_report.write("case[{}] Modulation:{},SymbolRate:{},result:Fail\n".format(case_num,modu,symbol))
                break
            else:
                continue
            print("case[{}] Modulation:{},SymbolRate:{},result:Pass\n".format(case_num,modu, symbol))
            test_report.write("case[{}] Modulation:{},SymbolRate:{},result:Pass\n".format(case_num,modu,symbol))
    case_num += 1
    test_report.close()
def DVBC_RecvPowLevelRange(InstrumentObject, SerialObject, parametes_list):
    parameters_name = ["test_case", "modulation",
                       "freq", "symbol_rate", "power_level", "step"]
    parametes_value_index = dict(zip(parameters_name, parametes_list))
    DVBC_Set_Instrument_Serial_func(InstrumentObject, SerialObject,parametes_value_index)
    adjust_parameter_record_result(SerialObject, InstrumentObject, parametes_value_index["test_case"],
                                   float(parametes_value_index["power_level"]),
                                   "PowerLevel", float(parametes_value_index["step"]))
def DVBC_SymbolRate_test(InstrumentObject, SerialObject, parametes_list):
    global case_num
    file_name = "result.log"
    parameters_name = ["test_case", "modulation","power_level","freq","symbol_rate"]
    parametes_value_index = dict(zip(parameters_name, parametes_list))
    DVBC_Set_Instrument_Serial_func(InstrumentObject, SerialObject,parametes_value_index)
    result = JudgePerLockedResult(SerialObject)
    if result in ["lockedNotEqual", "Unlocked"]:
        result_string = "case[{}] Modulation:{},SymbolRate:{},result:Fail\n".format(case_num,
                                                                                    parametes_value_index["modulation"],
                                                                                    parametes_value_index["symbol_rate"])
    else:
        result_string = "case[{}] Modulation:{},SymbolRate:{},result:Pass\n".format(case_num,
                                                                                    parametes_value_index["modulation"],
                                                                                    parametes_value_index["symbol_rate"])
    print(result_string)
    write_data_to_file(file_name,result_string)
    case_num += 1    
def DVBC_Freq_test(InstrumentObject, SerialObject, parametes_list):#include frequence capture range test
    global case_num
    file_name = "result.log"
    parameters_name = ["test_case", "modulation","power_level","freq","symbol_rate"]
    parametes_value_index = dict(zip(parameters_name, parametes_list))
    DVBC_Set_Instrument_Serial_func(InstrumentObject, SerialObject,parametes_value_index)
    result = JudgePerLockedResult(SerialObject)
    if result in ["lockedNotEqual", "Unlocked"]:
        result_string = "case[{}]Modulation:{},Frequence:{},result:Fail\n".format(case_num,
                                                                           parametes_value_index["modulation"],
                                                                           parametes_value_index["freq"])
    else:
        result_string = "case[{}]Modulation:{},Frequence:{},result:Pass\n".format(case_num,
                                                                           parametes_value_index["modulation"],
                                                                           parametes_value_index["freq"])
    print(result_string)
    write_data_to_file(file_name,result_string)
    case_num += 1    
def write_data_to_file(file_name,data):
    with open(file_name,"a+") as f:
        f.write(data+"\n") 
def record_abnormal_test_result(test_case,case_num,ParametersType,ParametersValue):
    file_name = "result.log"
    if test_case in ("DVBC_MINRXLEVEl_TEST", "DVBC_MAXRXLEVEl_TEST"):
        if ParametersValue > 126 or ParametersValue < -13:
            result_string = "Warning:Abnormal results!case[{}] {}:{}\n".format(case_num, ParametersType, ParametersValue)
            print(result_string)
            write_data_to_file(file_name,result_string)
            return True
    elif test_case in ("DVBC_AWGN_TEST"):
        if ParametersValue > 60 or ParametersValue < -35:
            result_string = "Warning:Abnormal results!case[{}] {}:{}\n".format(case_num, ParametersType, ParametersValue)
            print(result_string)
            write_data_to_file(file_name,result_string)
            return True
    elif test_case in ("DVBC_E/D_TEST", "DVBC_E/D_FIVE_ROAD_TEST"):
        if ParametersValue > 50 or ParametersValue < 1:
            result_string = "Warning:Abnormal results!case[{}] {}:{}\n".format(case_num, ParametersType, ParametersValue)
            print(result_string)
            write_data_to_file(file_name,result_string)
            return True
    return False
def confirm_parameters_value_direction(result,test_case,ParametersType,ParametersValue):
    if result in ("Unlocked", "lockedNotEqual"):
        print("Current {}:{}\n".format(ParametersType, ParametersValue))
        if test_case in ("DVBC_MINRXLEVEl_TEST", "DVBC_E/D_TEST",
                         "DVBC_E/D_FIVE_ROAD_TEST",
                         "DVBC_AWGN_TEST",
                         "DVBT2_AWGN_TEST",
                         "DTMB_AWGN_TEST"):
            print("Adjust parameters_direction:UP\n")
            return "UP"
        elif test_case in ("DVBC_MAXRXLEVEl_TEST"):
            print("Adjust parameters_direction:DOWN\n")
            return "DOWN"
    elif result is "lockedEqual":
        print("Current {}:{}\n".format(ParametersType, ParametersValue))
        if test_case in ("DVBC_MINRXLEVEl_TEST", "DVBC_E/D_TEST", "DVBC_E/D_FIVE_ROAD_TEST",
                         "DVBC_AWGN_TEST","DVBT2_AWGN_TEST",
                         "DTMB_AWGN_TEST"):
            print("Adjust parameters_direction:DOWN\n")
            return "DOWN"
        elif test_case in ("DVBC_MAXRXLEVEl_TEST"):
            print("Adjust parameters_direction:UP\n")
            return "UP"
def select_send_para_command_type(test_case,InstrumentObject,ParametersValue):
    if test_case in ("DVBC_MINRXLEVEl_TEST", "DVBC_MAXRXLEVEl_TEST"):
        InstrumentObject.set_instrument_level(ParametersValue, "dBuV")
        return
    elif test_case in ("DVBC_AWGN_TEST","DVBT2_AWGN_TEST","DTMB_AWGN_TEST"):
        awgn_command = DVBC_Set_InstrumentDict["SetAwgn"] + str(ParametersValue) + "\n"
        InstrumentObject.set_other_command(awgn_command)
        return
    elif test_case in ("DVBC_E/D_TEST", "DVBC_E/D_FIVE_ROAD_TEST"):
        InstrumentObject.set_fader_pathloss(2,1,ParametersValue)
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
def adjust_parameter_record_result(SerialObject, InstrumentObject, test_case,
                                   parameter_value, ParametersType, step,BW = "8M",TestBoardType = "CHIP",cpture_enble = False):
#***********************************************************************
#*parameter description:                                               *
#*1.SerialObject need serial object example "COM4"                     *
#*2.InstrumentObject need instrument object,example SFU,BTC and so on  *
#*3.test_case "MaxRecvLevel","MinRecvLevel"...                         *
#*4.parameter_value  30,50,115                                         *
#*5.ParametersType   "Level","Awgn","PathLoss","Doople"                *
#***********************************************************************
    global case_num
    file_name = "result.log"
    temp = parameter_value
    if cpture_enble:
        captuer_data(SerialObject)
        if TestBoardType == "FPGA":
            if test_case == "DVBT2_AWGN_TEST":
                SerialObject.send_command_to_serial(FPGASerialCommandDict["SetFPGA_T2_Mode"])
                SerialObject.send_command_to_serial(FPGASerialCommandDict["bw_select"][BW])
    result = JudgePerLockedResult(SerialObject,test_case)
    direct = confirm_parameters_value_direction(result,test_case,ParametersType,temp)
    if result in ("Unlocked", "lockedNotEqual"):
        while True:
            if direct == "UP":
                temp += step
            else:
                temp -= step
            select_send_para_command_type(test_case,InstrumentObject,temp)
            if cpture_enble:
               if test_case == "DVBT2_AWGN_TEST":
                   SerialObject.send_command_to_serial(FPGASerialCommandDict["exitMyTool"])
                   captuer_data(SerialObject)
                   SerialObject.send_command_to_serial(FPGASerialCommandDict["SetFPGA_T2_Mode"])
                   SerialObject.send_command_to_serial(FPGASerialCommandDict["bw_select"][BW])
            print("Current %s:%.1f\n"%(ParametersType, temp))
            result = JudgePerLockedResult(SerialObject,test_case)
            if result in ("lockedEqual"):
                result_string = "case[%s] %s:%.1f\n"%(case_num, ParametersType, temp)
                print(result_string)
                write_data_to_file(file_name,result_string)
                break
            if record_abnormal_test_result(test_case,case_num,ParametersType,temp):
                break
    elif result in ("lockedEqual"):
        while True:
            if direct == "UP":
                temp += step
            else:
                temp -= step
            select_send_para_command_type(test_case,InstrumentObject,temp)
            if cpture_enble:
                captuer_data(SerialObject)
                if test_case == "DVBT2_AWGN_TEST":
                    SerialObject.send_command_to_serial(FPGASerialCommandDict["exitMyTool"])
                    SerialObject.send_command_to_serial(FPGASerialCommandDict["SetFPGA_T2_Mode"])
                    SerialObject.send_command_to_serial(FPGASerialCommandDict["bw_select"][BW])
            print("Current %s:%.1f\n"%(ParametersType, temp))
            result = JudgePerLockedResult(SerialObject,test_case)
            if result in ("Unlocked", "lockedNotEqual"):
                result_string = "case[%s] %s:%.1f\n"%(case_num, ParametersType, temp)
                print(result_string)
                write_data_to_file(file_name,result_string)
                break
            if record_abnormal_test_result(test_case,case_num,ParametersType,temp):
                break
    case_num += 1
def JudgePerLockedResult(SerialObject,test_case):
    time.sleep(LockedDelay)
    SerialObject.send_command_to_serial(GetLockStatus)
    perList = []
    if SerialObject.get_locked_status():
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
    TV_Performance_Test("CHIP","BTC")
