import itertools
import time
from functools import reduce

LockedDelay = 20
ReadPerTime = 5
ReadPerGuardTime = 5
GetLockStatus = ["98\r"]
GetPerValue = ["99\r"]
FPGASerialCommandDict = {
    "enterMyTool": ["./demod_tool\r"],
    "exitMyTool": ["999\r"],
    "Capture_date": ["75\r", "2\r", "10000000\r"],
    "SetFPGA_DVBT_Mode": ["2\r"],
    "SetFPGA_T1_Mode": ["14\r", "1\r", "1\r"],
    "SetFPGA_T2_Mode": ["14\r", "1\r", "2\r"],
    "GetT1_Locked_Status": ["98\r"],
    "GetT1_T2_PER_Value": ["99\r"],
    "bw_select": {"8M": ["1\r"], "7M": ["2\r"]}
}
DVBC_CHIP_Serial_commandDict = {
    "enterMyTool":["./my_tool_tl1\r","11\r"],
    "GetPer":["99\r"],
    "GetLockedStatus":["98\r"],
    "SetModulation":["11\r","1\r"],
    "16QAM":["0\r"],
    "32QAM":["1\r"],
    "64QAM":["2\r"],
    "128QAM":["3\r"],
    "256QAM":["4\r"],
    "SelectDvbc":["2\r"],
    "exitMytool":["999\r"],
    "SetFreq":["999\r","3\r","1\r"],#+"freq\r"+"11\r"
    "DvbcMode":["11\r"]
}
DTMB_CHIP_Serial_commandDict = {
    "enterMyTool":["./my_tool_tl1\r","13\r"],
    "GetPer":["99\r"],
    "GetLockedStatus":["98\r"],
    "exitMytool":["999\r"],
    "SetFreq":["999\r","3\r","1\r"]#freq\r"+"11\r"
}
Serial_command = {
    "TL1_CHIP":DVBC_CHIP_Serial_commandDict,
    "FPGA":FPGASerialCommandDict
}
UnitDict = {
    "dBm":"DBM",
    "dBuV":"DBUV",
    "dBmV":"DBMV"
}
InstrumentCommandDict = {
    "NoiseAWGN_ON": "NOIS:AWGN ON\n",
    "NoiseADD": "NOIS ADD\n",
    "NoiseONLY": "NOIS ONLY\n",
    "NoiseOFF": "NOIS OFF\n",
    "FadingON": "FSIM ON\n",
    "FadingOFF": "FSIM OFF\n",
    "InterfererON": "DM:ISRC ON\n",
    "InterfererOFF": "DM:ISRC OFF\n",
    "ModeON":"MOD ON\n",
    "ModeOFF":"MOD OFF\n",
    "SFU_DTV":"DM:SOUR DTV\n",
    "BTC_DTV":"DM:TYPE DTV\n"
}
BTC_StandardDict = {
    "DVBT": "TDMB",
    "DVBT2": "T2DV",
    "DVB-S": "DVBS",
    "DVB-S2": "DVS2",
    "DTMB":"DMB-T"
}
SFU_StandardDict = {
    
    "DVBT":"DVBT",
    "DVBT2":"T2DV",
    "DVBC":"DVBC",
    "DTMB":"DMB-T"
}
InstrumentStandardDict = {
    "RSSFU":SFU_StandardDict,
    "BTC":BTC_StandardDict
}
fft_key_list = ["1K","2K","4K","8K","16K","32K","8E","16E","32E"]
gi_key_list = ["1/4","G1_4","1/8","G1_8","1/16","G1_16","1/32","G1_32",
               "1/128","G1128","19/128","G19128","19/256","G19256"]
code_key_list = ["1/2","R1_2","2/3","R2_3","3/4","R3_4","5/6",
                 "R5_6","3/5","R3_5","4/5","R4_5","1/3","R1_3","2/5","R2_5"]
Pilot_list = ["PP%s" % i for i in range(1, 9)]
T2_Pilot_Command = ["T2DV:PIL PP%s\n" % i for i in range(1, 9)]
T2Pilot_Command = dict(zip(Pilot_list, T2_Pilot_Command))
DTMB_workMode = {"1":["DTMB:NETW MFN\n","DTMB:SING OFF\n","DTMB:FRAM OFF\n","DTMB:CONS D16\n",
                    "DTMB:RATE R04\n","DTMB:GUAR G945\n","DTMB:GIC VAR\n","DTMB:TIME I720\n",
                    "DTMB:CHAN BW_8\n","DM:POL NORM\n"],
                 "2":["DTMB:NETW MFN","DTMB:SING ON\n","DTMB:DUAL:PIL OFF\n","DTMB:FRAM OFF\n",
                      "DTMB:CONS D4\n","DTMB:RATE R08\n","DTMB:GUAR G595\n","DTMB:GIC CONS\n",
                      "DTMB:TIME I720\n","DTMB:CHAN BW_8\n","DM:POL NORM\n"],
                 "3":["DTMB:NETW MFN\n","DTMB:SING OFF\n","DTMB:FRAMes OFF\n","DTMB:CONS D16\n",
                      "DTMB:RATE R06\n","DTMB:GUAR G945\n","DTMB:GIC VAR\n","DTMB:TIME I720\n",
                      "DTMB:CHAN BW_8\n","DM:POL NORM\n"],
                 "4":["DTMB:NETW MFN","DTMB:SING ON\n","DTMB:DUAL:PIL OFF\n","DTMB:FRAMes OFF\n",
                      "DTMB:CONS D16\n","DTMB:RATE R08\n","DTMB:GUAR G595\n","DTMB:GIC CONS\n",
                      "DTMB:TIME I720\n","DTMB:CHAN BW_8\n","DM:POL NORM\n"],
                 "5":["DTMB:NETW MFN\n","DTMB:SING OFF\n","DTMB:FRAMes OFF\n","DTMB:CONS D16\n",
                      "DTMB:RATE R08\n","DTMB:GUAR G420\n","DTMB:GIC VAR\n","DTMB:TIME I720\n",
                      "DTMB:CHAN BW_8\n","DM:POL NORM\n"],
                 "6":["DTMB:NETW MFN\n","DTMB:SING OFF\n","DTMB:FRAMes OFF\n","DTMB:CONS D64\n",
                      "DTMB:RATE R06\n","DTMB:GUAR G420\n","DTMB:GIC VAR\n","DTMB:TIME I720\n",
                      "DTMB:CHAN BW_8\n","DM:POL NORM\n"],
                 "7":["DTMB:NETW MFN\n","DTMB:SING ON\n","DTMB:DUAL:PIL OFF\n","DTMB:FRAM OFF\n",
                      "DTMB:CONS D32\n","DTMB:RATE R08\n", "DTMB:GUAR G595\n", "DTMB:GIC CONS\n",
                      "DTMB:TIME I720\n","DTMB:CHAN BW_8\n","DM:POL NORM\n"],
                 "8":["DTMB:NETW MFN\n","DTMB:SING OFF\n","DTMB:FRAMes OFF\n","DTMB:CONS D16\n",
                      "DTMB:RATE R08\n","DTMB:GUAR G945\n","DTMB:GIC VAR\n", "DTMB:TIME I720\n",
                      "DTMB:CHAN BW_8\n","DM:POL NORM\n"],
                 "9":["DTMB:NETW MFN\n","DTMB:SING OFF\n","DTMB:FRAMes OFF\n","DTMB:CONS D64\n",
                      "DTMB:RATE R06\n","DTMB:GUAR G945\n","DTMB:GIC VAR\n","DTMB:TIME I720\n",
                      "DTMB:CHAN BW_8\n","DM:POL NORM\n"],
                 "10":["DTMB:NETW MFN\n","DTMB:SING OFF\n","DTMB:FRAMes OFF\n","DTMB:CONS D64\n",
                       "DTMB:RATE R08\n","DTMB:GUAR G420\n","DTMB:GIC VAR\n","DTMB:TIME I720\n",
                       "DTMB:CHAN BW_8\n","DM:POL NORM\n"]
                 }
Instrument_Setting_Command={
    "RSSFU":{"DTMB":{"Modulation":{"16QAM":"DTMB:CONS C16\n",
                                   "32QAM":"DTMB:CONS C32\n",
                                   "64QAM":"DTMB:CONS C64\n",
                                   "256QAM":"DTMB:CONS C256\n"},
                     "AwgnValue":"NOIS:CN ",
                     "BW":"DTMB:CHAN BW_",
                     "WorkMode":DTMB_workMode
                     },
             "DVBC":{"Modulation":{"16QAM":"DVBC:CONS C16\n",
                                   "32QAM":"DVBC:CONS C32\n",
                                   "64QAM":"DVBC:CONS C64\n",
                                   "256QAM":"DVBC:CONS C256\n"},
                     "AwgnValue":"NOIS:CN ",
                     "SymbolRate":"DVBC:SYMB "
                     },
             "DVBT2":{"FFT":{i:j for i,j in zip(fft_key_list,["T2DV:FFT:MODE M%s\n"%i for i in fft_key_list])},
                      "GI":{i:j for i,j in zip(gi_key_list[::2],["T2DV:GUAR:INT %s\n"%i for i in gi_key_list[1::2]])},
                      "CodeRate":{i:j for i,j in zip(code_key_list[::2],["T2DV:PLP1:RATE %s\n"%i for i in code_key_list[1::2]])},
                      "Modulation":{"QPSK":"T2DV:PLP1:CONS T4\n",
                                    "16QAM":"T2DV:PLP1:CONS T16\n",
                                    "64QAM":"T2DV:PLP1:CONS T64\n",
                                    "256QAM":"T2DV:PLP1:CONS T256\n"},
                      "AwgnValue":"NOIS:CN ",
                      "Pilot":T2Pilot_Command
                      }
             },
    "BTC":{"DTMB":{"Modulation":{"16QAM":"DTMB:CONS C16\n",
                                   "32QAM":"DTMB:CONS C32\n",
                                   "64QAM":"DTMB:CONS C64\n",
                                   "256QAM":"DTMB:CONS C256\n"},
                   "BW":"DTMB:CHAN BW_"
                     },
             "DVBC":{"Modulation":{"16QAM":"DVBC:CONS C16\n",
                                   "32QAM":"DVBC:CONS C32\n",
                                   "64QAM":"DVBC:CONS C64\n",
                                   "256QAM":"DVBC:CONS C256\n"},
                     "AwgnValue":"NOIS:CN ",
                     "SymbolRate":"DVBC:SYMB "
                     },
             "DVBT2":{"FFT":{i:j for i,j in zip(fft_key_list,["T2DV:FFT:MODE M%s\n"%i for i in fft_key_list])},
                      "GI":{i:j for i,j in zip(gi_key_list[::2],["T2DV:GUAR:INT %s\n"%i for i in gi_key_list[1::2]])},
                      "CodeRate":{i:j for i,j in zip(code_key_list[::2],["T2DV:PLP1:RATE %s\n"%i for i in code_key_list[1::2]])},
                      "Modulation":{"QPSK":"T2DV:PLP1:CONS T4\n",
                                    "16QAM":"T2DV:PLP1:CONS T16\n",
                                    "64QAM":"T2DV:PLP1:CONS T64\n",
                                    "256QAM":"T2DV:PLP1:CONS T256\n"},
                      "AwgnValue":"NOIS:CN ",
                      "BW":"",
                      "Pilot":T2Pilot_Command
                      }
             }  
 }
ProfileTypeDict = {"1":"SPAT","2":"RICE","3":"PDOP","4":"RAYL","5":"CPH"}
DVBC_Set_InstrumentDict = {
    "16QAM":"DVBC:CONS C16\n",
    "32QAM":"DVBC:CONS C32\n",
    "64QAM":"DVBC:CONS C64\n",
    "256QAM":"DVBC:CONS C256\n",
    "DVBC_SymbolRate":"DVBC:SYMB ",#example 4.711e6
    "SetAwgn":"NOIS:CN "
}
confirm_parameter_direction = {"UP":("DVBC_MINRXLEVEl_TEST", "DVBC_E/D_TEST", "DVBC_E/D_FIVE_ROAD_TEST","DVBC_AWGN_TEST"),
                               "DOWN":("DVBC_MAXRXLEVEl_TEST")}
FFT_Mode_list = ["M1K", "M2K", "M4K", "M8K", "M16K", "M32K", "M8E", "M16E", "M32E"]
Guard_Interval_list = ["G1_4", "G1_8", "G1_16", "G1_32", "G1128", "G19128", "G19256"]
Modulation_list1 = ["T4", "T16", "T64", "T256"]
Modulation_list2 = ["QPSK", "16QAM", "64QAM", "256QAM"]
CodeRate_list = ["R1_2", "R2_3", "R3_4", "R5_6", "R3_5", "R4_5", "R1_3", "R2_5"]
T2_Set_Instrument_command_list = {
    "M1K":{"G1_16":["PP4","PP5"],"G1_8":["PP2","PP3"],"G1_4":["PP1"]},
    "M2K":{"G1_32":["PP4","PP7"],"G1_16":["PP4","PP5"],"G1_8":["PP2","PP3"],"G1_4":["PP1"]},
    "M4K":{"G1_32":["PP4","PP7"],"G1_16":["PP4","PP5"],"G1_8":["PP2","PP3"],"G1_4":["PP1"]},
    "M8K":{"G1128":["PP7"],"G1_32":["PP4","P7"],"G1_16":["PP4","P5","P8"],
           "G19256":["PP4","PP5","PP8"],"G1_8":["PP2","PP3","PP8"],"G19128":["PP2","PP3","PP8"],
           "G1_4":["P1","P8"]},
    "M16K":{"G1128":["PP7"],"G1_32":["PP4","PP6","PP7"],"G1_16":["PP2","PP4","PP5","PP8"],
            "G19256": ["PP2","PP4", "PP5", "PP8"],"G1_8":["PP2","PP3","PP8"],
            "G19128":["PP2","PP3","PP8"],"G1_4":["P1","PP8"]},

    "M32K": {"G1128": ["PP7"], "G1_32": ["PP4", "PP6"], "G1_16": ["PP2", "PP4","PP8"],
             "G19256": ["PP2", "PP4","PP8"], "G1_8": ["PP2","PP8"],
             "G19128": ["P2","P8"]},
    "M8E":{"G1128":["PP7"],"G1_32":["PP4","PP7"],"G1_16":["PP4","PP5","PP8"],
           "G19256":["PP4","PP5","PP8"],"G1_8":["PP2","PP3","PP8"],"G19128":["PP2","PP3","PP8"],
           "G1_4":["P1","P8"]},
    "M16E":{"G1128":["PP7"],"G1_32":["PP4","PP6","PP7"],"G1_16":["PP2","PP4","PP5","PP8"],
            "G19256": ["PP2","PP4", "PP5", "PP8"],"G1_8":["PP2","PP3","PP8"],
            "G19128":["PP2","PP3","PP8"],"G1_4":["PP1","PP8"]},

    "M32E": {"G1128": ["PP7"], "G1_32": ["PP4", "PP6"], "G1_16": ["PP2", "PP4","PP8"],
             "G19256": ["PP2", "PP4","PP8"], "G1_8": ["PP2","PP8"],
             "G19128": ["PP2","PP8"]},
}

T1DV_Modulation_command = ["DVBT:CONS %s\n" % i for i in Modulation_list1[:3]]
T1DV_FFT_Command = ["DVBT:FFT:MODE %s\n" % i for i in FFT_Mode_list]
T1DV_CodeRate_command = ["DVBT:RATE %s\n" % i for i in CodeRate_list]
T1DV_GI_Command = ["DVBT:GUAR:INT %s\n" % i for i in Guard_Interval_list]
T1DV_Pilot_Command = ["DVBT:PIL PP%s\n" % i for i in range(1, 9)]

T1_FFT_Mode_Command = dict(zip(FFT_Mode_list, T1DV_FFT_Command))
T1Pilot_Command = dict(zip(Pilot_list, T1DV_Pilot_Command))
T1_GI_Command = dict(zip(Guard_Interval_list, T1DV_GI_Command))
T1_Modulation_command = dict(zip(Modulation_list2[:3], T1DV_Modulation_command))
T1_CodeRate_command = dict(zip(CodeRate_list, T1DV_CodeRate_command))

T1_Set_Instrument_command = {}
T1_Set_Instrument_command.update(T1_FFT_Mode_Command)
T1_Set_Instrument_command.update(T1Pilot_Command)
T1_Set_Instrument_command.update(T1_GI_Command)
T1_Set_Instrument_command.update(T1_Modulation_command)
T1_Set_Instrument_command.update(T1_CodeRate_command)

T2_Modulation_command = ["T2DV:PLP1:CONS %s\n" % i for i in Modulation_list1]
T2_FFT_Command = ["T2DV:FFT:MODE %s\n" % i for i in FFT_Mode_list]
T2_CodeRate_command = ["T2DV:PLP1:RATE %s\n" % i for i in CodeRate_list]
T2_GI_Command = ["T2DV:GUAR:INT %s\n" % i for i in Guard_Interval_list]
T2DV_FFT_Mode_Command = dict(zip(FFT_Mode_list, T2_FFT_Command))
T2DV_GI_Command = dict(zip(Guard_Interval_list, T2_GI_Command))
T2DV_Modulation_command = dict(zip(Modulation_list2, T2_Modulation_command))
T2DV_CodeRate_command = dict(zip(CodeRate_list, T2_CodeRate_command))

T2_Set_Instrument_command = {}
T2_Set_Instrument_command.update(T2DV_FFT_Mode_Command)
T2_Set_Instrument_command.update(T2Pilot_Command)
T2_Set_Instrument_command.update(T2DV_GI_Command)
T2_Set_Instrument_command.update(T2DV_Modulation_command)
T2_Set_Instrument_command.update(T2DV_CodeRate_command)
def generater_DVBC_performacne_test_case():
    pass
def generater_T1_test_case():
    print("It is generating DVBT1 test cases,wait a moment!\n")
    command_list = list(itertools.product(FFT_Mode_list,
                                          Pilot_list, Guard_Interval_list, Modulation_list2, CodeRate_list))
    it = iter(command_list)
    with open("T1_Function_test_case.txt", "w+") as f:
        for i in it:
            f.write(":".join(i))
            f.write("\n")
    print("DVBT1 test cases completed!\n")
def generater_T2_test_case():
    print("It is generating DVBT test cases,wait a moment!\n")
    with open("T2_Function_test_case.txt", "w+") as f:
        for fft in iter(FFT_Mode_list):
            gi_temp_list = list(T2_Set_Instrument_command_list[fft].keys())
            for gi in iter(gi_temp_list):
                pilotlist = T2_Set_Instrument_command_list[fft][gi]
                command_list = list(itertools.product([fft],[gi],pilotlist,Modulation_list2, CodeRate_list))
                it = iter(command_list)
                for i in it:
                    f.write(":".join(i))
                    f.write("\n")
    print("DVBT test cases completed!\n")
def generater_frequence():
    frequence_list = [i for i in range(82,859,8)]
    with open("frequence.txt","a+") as f:
        for i in frequence_list:
            command = "DVBC_MINRXLEVEl_TEST:256QAM:{}:6.875:33:1\n".format(i)
            f.write(command)
    
if __name__ == "__main__":
    #generater_T2_test_case()
    generater_frequence()


























