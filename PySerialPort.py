import serial
import time
from threading import Thread
from queue import Queue
import re
#from Command import FPGASerialCommandDict as fpga_command
from Command import *
class SerialPort(object):
    def __init__(self,com_num):
        self.open_status = False
        try:
            self.serialPort = serial.Serial(com_num,115200,timeout=1)
            self.open_status = True
        except:
            print("Open port failed!")
            self.open_status = False
            return
        self.per_list = []
        self.serial_queue_infor = Queue()
        self.start_stop_print_thread_flag = True
        #self.send_command_to_serial(fpga_command["enterMyTool"])#Once initialized, enter my tool
        self.print_thread()#Once initialized,start print thread
    def send_command_to_serial(self,args):
        for i in args:
            time.sleep(1.5)
            self.serialPort.write(i.encode())
    def print_serial_information(self):
        self.patern = r"[0-9]{4}$"
        while self.start_stop_print_thread_flag:
            self.serial_information = self.serialPort.readline().decode()
            if self.serial_information.find("75_init_ok") != -1:
                self.serial_queue_infor.put("75_init_ok")
            elif self.serial_information.find("75_init_ng") != -1:
                self.serial_queue_infor.put("75_init_ng")
            elif self.serial_information.find("isVarRequestForStopTrue") != -1:
                self.serial_queue_infor.put("Unlocked")
            elif self.serial_information.find("CPUL1POSTOK") != -1:
                self.serial_queue_infor.put("Locked")
            elif self.serial_information.find("Lock:") != -1:
                self.serial_queue_infor.put(self.serial_information)
            elif self.serial_information.find("Per:") != -1:
                self.serial_queue_infor.put(self.serial_information)
            elif re.match(self.patern,self.serial_information.strip()):
                self.serial_queue_infor.put(self.serial_information)
            elif self.serial_information == "":
                continue
            print(self.serial_information)
    def print_thread(self):
        t = Thread(target=self.print_serial_information)
        t.setDaemon(True)
        t.start()
    def close_serial_port_stop_thread(self):
        self.start_stop_print_thread_flag = False
        self.serialPort.close()
        time.sleep(3)
    def get_locked_status(self):# fpga mode include DVBT/DVBT2/J83B/DVBC
        self.temp = []
        for i in range(100):
            time.sleep(1)
            self.temp.append(self.serial_queue_infor.get())
            if len(self.temp)!= 0:
                if self.temp[0] == "Unlocked":
                    print("Unlocked")
                    return False
                elif self.temp[0] == "Locked":
                    print("Locked")
                    return True
                elif int(self.temp[0].strip().split(":")[1])== 1:
                    print("Locked")
                    return True
                elif int(self.temp[0].strip().split(":")[1])== 0:
                    print("Unlocked")
                    return False
        print("Ge locked status timeout,Get locked status failed!")
        return False
    def get_capture_date_status(self):
        self.temp = []
        for i in range(20):
            time.sleep(1)
            self.temp.append(self.serial_queue_infor.get())
            if self.temp[0] == "75_init_ok":
                print("Capture date successfully!")
                return True
            elif self.temp[0] == "75_init_ng":
                print("Capture date failed!")
                return False
    def getPerValue(self,perCommand):
        self.per_list = []
        self.send_command_to_serial(perCommand)
        time.sleep(1)
        self.per_list.append(self.serial_queue_infor.get())
        if re.match(r"[0-9]",self.per_list[0]):
            return self.per_list[0]
        else:
            return self.per_list[0].strip().split(":")[1]
        
if __name__ == "__main__":
    DVBC_CHIP_Serial = SerialPort("COM4")
    DVBC_CHIP_Serial.send_command_to_serial(DVBC_CHIP_Serial_commandDict["enterMyTool"])
    DVBC_CHIP_Serial.send_command_to_serial(DVBC_CHIP_Serial_commandDict["SetModulation"])
    DVBC_CHIP_Serial.send_command_to_serial(DVBC_CHIP_Serial_commandDict["16QAM"])
    DVBC_CHIP_Serial.send_command_to_serial(["%s\r"%(str(6875))])
    time.sleep(1)
    DVBC_CHIP_Serial.send_command_to_serial(DVBC_CHIP_Serial_commandDict["GetLockedStatus"])
    DVBC_CHIP_Serial.close_serial_port_stop_thread()
    
    
    

        
    
