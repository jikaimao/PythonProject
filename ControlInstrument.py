import visa
import time
from Command import *
class Instrument(object):
    def __init__(self,instrumnetType):
        self.instrumnetType = instrumnetType
        self.visa32_dll = r"C:\Windows\System32\visa32.dll"
        self.rm = visa.ResourceManager(self.visa32_dll)
    def connect_instrument(self):
        try:
            self.instrument_list = self.rm.list_resources()
            for i in self.instrument_list:
                if i.find("TCPIP0::") != -1:
                    if i.split("::")[1].split("-")[0] == self.instrumnetType:
                        self.instrument = self.rm.open_resource(i)
                        break
            self.instrument.write("*IDN?\n")
            time.sleep(1)
            print("Connect %s Successfully!\n"%self.instrumnetType)
            return True
        except:
            print("Connect %s failed!\n"%self.instrumnetType)
            return False
    def set_instrument_freq(self,freq,unit):
        try:
            self.instrument.write("FREQ {} {}\n".format(freq,unit))
            time.sleep(1)
            return True
        except:
            print("Set frequence failed!\n")
            return False
    def set_instrument_level(self,level,unit):
        try:
            self.instrument.write("UNIT:VOLT %s\n"%(UnitDict[unit]))
            time.sleep(1)
            self.instrument.write("VOLT {}\n".format(level))
            time.sleep(1)
            return True
        except:
            print("Set power level failed!\n")
            return False
    def set_standard_to_instrument(self,standard):
        try:
            self.instrument.write("DM:TRAN %s\n"%(standard))
            time.sleep(3)
            return True
        except:
            print("Set standard failed!\n")
            return False
    def set_fader_default(self):
        try:
            self.instrument.write("FSIM:PRES\n")
            time.sleep(3)
            return True
        except:
            print("Set fader default failed!\n")
            return False
    def set_fader_profile_status(self,status,group,path,profile):#profile PDOP/SPAT/RICE/CPH
        try:
            self.status_command = "FSIM:DEL:GRO{}:PATH{}:STAT {}\n".format(group,path,status)
            self.profile_command = "FSIM:DEL:GRO{}:PATH{}:PROF {}\n".format(group,path,profile)
            self.set_other_command(self.status_command)
            self.set_other_command(self.profile_command)
            return True
        except:
            print("Set fader profile status failed!\n")
            return False
    def set_fader_pathloss(self,group,path,pathloss):
        try:
            self.instrument.write("FSIM:DEL:GRO{}:PATH{}:LOSS {}\n".format(group,path,pathloss))
            time.sleep(1)
            return True
        except:
            print("Set fader pathloss failed!\n")
            return False
    def set_fader_doppler(self,group,path,doppler):
        try:
            self.instrument.write("FSIM:DEL:GRO{}:PATH{}:FDOP {}\n".format(group,path,doppler))
            time.sleep(2)
            self.instrument.write("FSIM:DEL:GRO{}:PATH{}:FRAT 1\n".format(group,path))
            time.sleep(2)
            return True
        except:
            print("Set fader doppler failed!\n")
            return False
    def set_other_command(self,command):
        try:
            self.instrument.write(command)
            time.sleep(1)
            return True
        except:
            print("Set %s failed!\n"%command)
            return False
    def set_basic_delay(self,group,delay):
        try:
            self.instrument.write("FSIM:DEL:GRO{}:BDEL {}E-3\n".format(group,delay/1000))
            time.sleep(1)
            return True
        except:
            print("Set basic delay failed!\n")
            return False
    def set_fading_reference(self):
        if self.instrumnetType == "BTC":
            self.instrument.write("FSIM:KCON DSH\n")
            time.sleep(2)
        elif self.instrumnetType == "RSSFU":
            self.instrument.write("FSIM:REF FDOP\n")
            time.sleep(2)
    def set_const_phase(self,group,path,deg):
        try:
            self.instrument.write("FSIM:DEL:GRO{}:PATH{}:CPH {}DEG\n".format(group,path,deg))
            time.sleep(1)
        except:
            print("Set const phase failed!\n")
    def close_instrument_handle(self):
        self.instrument.close()
if __name__ == "__main__":
    BTC = Instrument("BTC")
    BTC.connect_instrument()

    
